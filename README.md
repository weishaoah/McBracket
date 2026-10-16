# McBracket · 麦门最强餐品争霸赛

**8 款真实麦当劳餐品，7 场一对一对决，只有一个冠军。**

选出你心中的麦门最强，生成可分享的冠军卡——菜单价格与营养数据全部来自
[麦当劳官方 MCP](https://github.com/M-China/mcd-mcp-server)，不是静态换皮游戏。

这是「麦当劳程序员创意开发大赛」的参赛作品，由个人独立开发，**非麦当劳官方产品**。

## 试玩

| 方式 | 说明 |
|---|---|
| 在线 Demo | **https://weishaoah.github.io/McBracket/**（GitHub Pages，已上线；无需 Token、无需注册） |
| 本地运行 | `npm install && npm run dev`，打开 http://127.0.0.1:5173/ |

## 三步玩法

1. **开始争霸赛** —— 8 款餐品自动随机抽签进入淘汰赛对阵。
2. **7 场对决** —— 每场点选你更喜欢的一款：四分之一决赛 4 场 → 半决赛 2 场 → 总决赛 1 场。每场选择后揭晓两款的价格、热量、蛋白质、钠对比。
3. **加冕冠军** —— 查看晋级路线、完整对阵图，一键导出竖版冠军卡 PNG 发朋友圈。

## 截图

| 首页（含数据口径） | 对决与数据揭晓 |
|---|---|
| ![首页](docs/screenshots/01-home.png) | ![对决](docs/screenshots/11-picked.png) |

| 冠军页与对阵图 | 导出的冠军卡 PNG |
|---|---|
| ![冠军](docs/screenshots/20-champion.png) | ![冠军卡](docs/screenshots/champion-card.png) |

发布前审计截图（手机视口完整流程 + 生产构建 Demo）在 [`docs/audit/`](docs/audit/)。

## 数据从哪里来（重要）

页面展示的每一项数据都有明确来源，且**三种状态严格区分**：

- **官方核价**：价格优先采用 `calculate-price` 的官方核价结果（单位：分），
  与菜单价一致时才同时展示两者；每款餐品旁边都标注了价格口径。
- **菜单参考价**：拿不到核价时，只展示 `query-meals` 的菜单价（单位：元），
  并明确标注「菜单参考价」与采集日期——绝不把菜单价包装成核价。
- **暂无可靠数据**：营养数据只采用官方营养表与菜单名的**精确匹配**结果；
  官方表里缺失的字段显示「—」，匹配不上就显示「暂无可靠数据」，绝不编造或估算。

当前快照（2026-10-15 22:00 官方时钟）的 8 强数据口径：

| 餐品 | 价格口径 | 采集时间 |
|---|---|---|
| 巨无霸 / 麦香鱼 / 麦香鸡 / 薄皮焦香V翅 / 美汁源 / 苹果片 | 官方核价（与菜单价一致） | 2026-10-15 22:00 |
| 不素之霸双层牛堡 | 官方核价（与菜单价一致） | 2026-10-15 15:47 |
| 培根安格斯厚牛堡 | **菜单参考价**（未核价） | 2026-10-14 11:26 |

> 培根安格斯厚牛堡在最近两次采集时段都不在门店菜单上（深夜菜单切换），
> 快照按规则沿用 10-14 的菜单参考价并如实标注日期，不用猜测价格补齐。

已知的数据陷阱及处理方式（实测踩坑）：

- `query-meals` 的价格单位是**元**（字符串 `"25.5"`），`calculate-price` 的单位是**分**（整数 `2550`）。两者已统一换算为分后比较。
- **菜单按营业时段切换**：`query-meals` 返回的是当前时段菜单。实测早餐时段（09:28）门店 95 个在售商品中，8 强只有饮料 1 款在售——汉堡和小食不是下架，而是这个时段本就不供应；22:00 的深夜菜单中不素之霸与培根安格斯也缺席。因此快照支持**分批采集合并**，每条数据保留各自的采集时间，页面显示时间区间而非单一时刻。
- 营业时间外门店菜单会缩水（实测 23:59 后 8 强中 3 款下架、核价接口不可用），此时快照缺项而不是猜测。
- 快照中的价格对比仅在同一门店、同一订餐渠道（orderType=1, beType=1）下成立；合并历史快照时会**结构性校验**门店与渠道，不一致就整体拒绝合并。
- 超过 7 天的旧数据行会被丢弃而不是继续展示——旧价格不覆盖新观测。

详见 [MCP_INTEGRATION.md](MCP_INTEGRATION.md)。

## 安装与本地运行

```bash
npm install
npm run dev        # http://127.0.0.1:5173/
npm run test       # Vitest 26 条：淘汰赛规则 + 快照完整性与展示口径
npm run test:data  # Python 21 条：数据管线回归（营养缺失/合并门禁/旧价覆盖）
npm run build      # 类型检查 + 产物构建（GitHub Pages 可直接部署 dist/）
```

可选：用你自己的 Token 刷新数据快照（Token 只走环境变量，绝不入库）：

```bash
export MCD_MCP_TOKEN=你的Token
python scripts/fetch_snapshot.py --city 上海 --keyword 人民广场 --out src/data/snapshot.json
```

## 真实接入的证据

- `scripts/fetch_snapshot.py` 是自包含的 MCP 客户端（标准库 urllib，零第三方依赖），实际调用了 5 个只读 Tool，并在写入类工具上设置了硬性拒绝（`create-order` 等一旦出现在调用列表即抛错）。
- 2026-10-15 22:00:51 的实跑记录：门店 1450713 当前时段 6/8 款在售，全部拿到官方核价且与菜单价一致；营养表 8 行与官方 `list-nutrition-foods` 实时返回值逐值一致。
- 冠军卡由 html-to-image 在浏览器内真实栅格化生成；发布前审计用自动化浏览器对**开发服与生产构建**各跑完整 7 场对局 + PNG 导出，控制台零错误（证据见 [`docs/audit/AUDIT-EVIDENCE.md`](docs/audit/AUDIT-EVIDENCE.md)）。

## 工程结构

```
src/engine/tournament.ts    淘汰赛核心逻辑（纯函数，测试覆盖含 200 次随机对局）
src/engine/championTitle.ts 冠军称号（仅依据真实数据与赛果生成）
src/components/             HomeView / MatchView / DataReveal / BracketView / ChampionCard / FoodArt
src/data/snapshot.json      官方 MCP 数据快照（含门店、渠道、采集时间、工具清单）
src/data/snapshot.test.ts   快照完整性与价格口径测试（15 条）
tests/test_data_pipeline.py 采集管线回归测试（21 条）
scripts/fetch_snapshot.py   只读 MCP 采集脚本（Demo 快照的可复现来源）
scripts/audit-browser.sh        发布前浏览器审计（手机视口完整流程）
scripts/audit-export-evidence.sh 冠军卡导出与控制台证据
scripts/audit-demo-dist.sh      生产构建无 Token Demo 冒烟测试
scripts/make_review_packet.py   外部审查包生成器
```

## 安全与免责

- Token 不进入前端代码、不进入仓库；`mcp-config.example.json` 仅含 `${MCD_MCP_TOKEN}` 占位符。
- 全程只读：不接入 `create-order`、`cancel-order`、`auto-bind-coupons`、`draw-lottery` 等任何写入类工具，不代用户下单。
- 餐品视觉为原创 SVG 插画，不复制官方图片素材；本项目与麦当劳官方无关。
- 价格与营养数据仅供参考，请以麦当劳官方渠道实时结果为准。

## 参赛材料

按大赛要求提供：`README.md`、`CONTEST_DECLARATION.md`（与官方模板逐字一致）、
`MCP_INTEGRATION.md`、源代码、`workbuddy.md`（WorkBuddy 开发记录）、
`mcp-config.example.json`（脱敏配置示例）。

## 部署（GitHub Pages）

Demo 是纯静态站点：无后端、无数据库、无 Token。两种方式任选：

**方式一：GitHub Actions（推荐，仓库公开后）**

1. 仓库 Settings → Pages → Build and deployment → Source 选 **GitHub Actions**。
2. 推送即自动部署：`.github/workflows/deploy.yml` 会先跑 `tsc --noEmit` 与
   Vitest，通过后才 `npm run build` 并发布 `dist/`。
3. 几分钟后访问 `https://<user>.github.io/McBracket/`。

**方式二：手动**

```bash
npm run build          # 产物在 dist/
# 把 dist/ 推到 gh-pages 分支，或用任何静态托管
```

子路径兼容：`vite.config.ts` 设置 `base: './'`，HTML 里的资源引用全部是相对路径，
部署到项目子路径（`/McBracket/`）不需要改任何配置——发布前已在本地以
`/McBracket/` 子路径实测通过，上线后又对线上地址
（https://weishaoah.github.io/McBracket/）用真实浏览器复验：
8 强名单、「官方数据快照」徽标、非官方声明、完整对局与数据揭晓均正常
（截图 `docs/audit/audit-13-live-site.png`）。

## License

MIT，见 [LICENSE](LICENSE)。参赛声明见 [CONTEST_DECLARATION.md](CONTEST_DECLARATION.md)。
