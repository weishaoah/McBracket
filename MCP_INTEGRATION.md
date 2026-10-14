# MCP Integration · McBracket

本文记录 McBracket 对麦当劳官方 MCP Server（`https://mcp.mcd.cn`，仓库
[M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server)）的**实际**集成：
调用了哪些 Tool、以什么参数、返回格式实测长什么样、以及我们如何避免把数据用错。

## 1. 接入方式

- 协议：MCP over Streamable HTTP，`POST https://mcp.mcd.cn`，
  Header `Authorization: Bearer <token>`，JSON-RPC `tools/call`。
- 客户端：`scripts/fetch_snapshot.py`，仅用 Python 标准库 `urllib` 实现，零第三方依赖。
  实测无需维持 session，单次 `tools/call` 即可。
- 只读约束：脚本内置白名单（仅下列 6 个 Tool）与写入类工具黑名单
  （`create-order`、`cancel-order`、`mall-create-order`、`party-order-create`、
  `draw-lottery`、`auto-bind-coupons`、`delivery-create-address`），
  后者一旦出现在调用列表立即抛错，**结构性阻止**而非口头承诺。

## 2. 实际调用的 Tool

| Tool | 参数（实测有效） | 用途 |
|---|---|---|
| `now-time-info` | `{}` | 官方时间基准；快照的「采集时间」取自这里，不信本机时钟 |
| `query-nearby-stores` | `{"beType":1,"searchType":2,"city":"上海","keyword":"人民广场"}` | 选定采集门店 |
| `query-meals` | `{"storeCode":"1450713","orderType":1,"beType":1}` | 获取在售餐品与菜单价 |
| `list-nutrition-foods` | `{}` | 官方营养表（CSV 内嵌于 JSON 字符串，160 条） |
| `calculate-price` | `{"storeCode":"...","orderType":1,"beType":1,"items":[{"productCode":"1100","quantity":1}]}` | 官方核价 |
| `query-meal-detail` | `{"storeCode":"...","orderType":1,"beType":1,"code":"1100"}` | 餐品详情（采集脚本支持；当前页面未使用） |

注意：`query-meal-detail` 的参数名是 **`code`**，不是 `productCode`；缺少
`beType` 时接口直接返回 400。这两个坑都已写进脚本注释。

## 3. 响应格式实测（不要只信文档）

### 3.1 「输出格式要求 + Original Response」混合文本

每个 Tool 返回的文本不是纯 JSON，而是先有一段给 LLM 看的输出格式说明，
其中含有形如 `data.meals.{code}` 的**花括号占位符**，随后才是真正的 JSON：

````
## 输出格式要求
… data.meals.{code} …
## Original Response
{"success":true,"code":200,"message":"请求成功",...,"data":{...}}
````

直接对整段文本做 `JSON.parse` 会失败。`scripts/fetch_snapshot.py` 的
`scan_balanced_json()` 用字符串状态机 + 逐个 `{` 起点配平来定位真正的响应体。

### 3.2 金额单位不一致（本项目最重要的实测发现）

同一笔钱，两个接口两种单位：

| 接口 | 字段 | 实测值 | 单位 |
|---|---|---|---|
| `query-meals` | `data.meals["1100"].currentPrice` | `"25.5"` | **字符串·元** |
| `calculate-price` | `data.price` | `2550` | **整数·分** |

McBracket 统一换算成「分」后再展示（`src/types.ts` 的 `effectivePriceCents`），
展示层再格式化为元（`25.50 → ¥25.5`）。数据揭晓里的价格对比因此只在同一单位
基准上成立。

### 3.3 营养表

`list-nutrition-foods` 的 `data` 是一个 **CSV 字符串**（首行为列声明
`[160]{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:`），
不是 JSON 数组、也不是 Markdown 表格。解析按逗号切分并按列名取值。

只取 `productName` 与菜单名**完全一致**的行作为「精确匹配」；套餐、限定品、
周边匹配不上时，页面显示「暂无可靠数据」。8 强中 8/8 精确匹配
（这也是选择这 8 款的原因之一）。

### 3.4 业务成功 ≠ 传输成功

`calculate-price` 在商品不可售（实测：23:59 后对仍挂在菜单里的巨无霸核价）
时返回业务失败或 0。脚本以 `success===true` 且价格 > 0 才认可核价结果，
否则降级使用 `query-meals` 菜单价并在快照中标注 `priceSource`。

## 4. 采集记录（真实运行日志摘要）

| 时间（官方 now-time-info） | 结果 |
|---|---|
| 2026-10-14 11:26:56 | 营业时段采集：3 店 × 全菜单；8 强候选在 1450713 全部在售、营养全部精确匹配。Demo 快照 `src/data/snapshot.json` 的数据来源 |
| 2026-10-14 23:59:25 | 夜间复测：8 强仅 5 款在售（1406/1440/515837 已下架），核价正常；证明菜单随供应时段变化，快照必须标注时间 |
| 2026-10-15 00:00:33 | 跨日复测：巨无霸仍在菜单但核价不可用（价格来源降级为菜单价）；8 强仅 5 款在售 |

夜间复测还验证了：`query-meals` 菜单价与 `calculate-price` 核价在可比商品上
完全一致（¥16/¥17/¥13/¥7 四款，元↔分换算无误差）。

## 5. 页面如何消费这些数据

- **模式 A（公开 Demo）**：读取 `src/data/snapshot.json`，页头显示
  「官方数据快照」徽标，页脚展示门店、采集时间、工具清单。
- **模式 B（真实 MCP）**：开发者本地用 `scripts/fetch_snapshot.py` 刷新快照
  （Token 走环境变量 `MCD_MCP_TOKEN` 或 `~/.workbuddy/mcp.json`），产物同为
  snapshot.json。**Token 永远不进浏览器前端、不进仓库**；页面本身不直接持有
  Token，因此公开部署不需要后端。
- 写入类工具全程未接入；本项目不会代替用户执行任何下单、领券、抽奖操作。

## 6. 已知限制

1. Demo 快照是单门店单渠道的时点数据，不同城市/门店/时段会有差异。
2. `8 强`由采集脚本中的 `SEED_CODES` 决定，换城市重采时若某款不在售会自动剔除
   （脚本会报告 `items: n/8`），不会编造补位。
3. 官方营养表覆盖常驻单品；限定品与套餐大概率「暂无可靠数据」，这是数据源口径
   而非程序缺陷。
