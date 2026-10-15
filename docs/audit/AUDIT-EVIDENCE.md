# 发布前审计证据 · 2026-10-15

本目录保存 McBracket 提交比赛前的**真实运行证据**：全部由当次实际执行产生，
无编造、无修饰。复现方式见各脚本头部注释。

## 运行环境

- 开发服务器：`npm run dev`（Vite，http://127.0.0.1:5173/）
- 生产构建：`npm run build` + `python -m http.server 5174`（模拟无 Token 公开 Demo）
- 浏览器：agent-browser 0.17.0（Chromium 无头），手机视口 390×844 + 桌面 1280×800
- 官方时钟基准：`now-time-info`（2026-10-15 22:00:51 GMT+08:00）

## 1. 单元测试

```
$ npm test
 ✓ src/engine/tournament.test.ts (11 tests)
 ✓ src/data/snapshot.test.ts (15 tests)
 Test Files  2 passed (2)
      Tests  26 passed (26)

$ python -m unittest discover -s tests
Ran 21 tests in 0.022s
OK
```

覆盖：淘汰赛规则（含 200 次随机对局）、金额格式化、快照完整性
（8 个唯一 code、插画全覆盖、核价与菜单价一致、营养值钉死官方表现值）、
价格口径标签、营养缺失字段不变成 0、跨门店/渠道拒绝合并、旧价不覆盖新价、
超期旧行丢弃、非种子行不合并。

## 2. 类型检查与构建

```
$ npx tsc --noEmit        # 零错误
$ npm run build
dist/index.html                   0.62 kB │ gzip:  0.51 kB
dist/assets/index-DDT165HD.css    9.65 kB │ gzip:  2.72 kB
dist/assets/index-6sdqbm2o.js    13.75 kB │ gzip:  5.42 kB
dist/assets/index-B0t0tM3l.js   165.19 kB │ gzip: 55.42 kB
✓ built in 12.75s
```

## 3. 手机视口完整流程（scripts/audit-browser.sh）

```
== home (390x844) ==
roster items: 8
menu-reference label: "yes"        ← 培根安格斯显示「菜单参考价」
carried capture date: "yes"        ← 首页可见 10-14 的采集时间
non-live notice: "yes"             ← 「官方数据快照，非实时」

== match 1 + data reveal ==
reveal provenance: "yes"           ← 数据揭晓注明官方核价口径

== champion page facts ==
champion: "【美汁源】“黄金橙橙”"
bracket matches: 7
bracket winners: 7
route steps: 3
snapshot notice: "yes"

== restart ==
progress after restart: "第 1 场 / 共 7 场"

== replay + PNG export ==（另见 scripts/audit-export-evidence.sh）
png data url length: 711938        ← 冠军卡栅格化为 ~712KB data URL
✓ Downloaded to shots/audit-champion-card.png (mcbracket-card-*.png)
```

控制台：**零错误、零警告**（`agent-browser console` 无输出）。

## 4. 生产构建无 Token Demo（scripts/audit-demo-dist.sh）

```
roster items: 8
snapshot badge: "yes"
menu-reference label: "yes"
non-live notice: "yes"
no token anywhere: "clean"
champion: "【美汁源】“黄金橙橙”"
✓ Downloaded to shots/audit-demo-card.png (mcbracket-card-*.png)   ← 526KB
```

## 5. 数据核对（2026-10-15 21:44，直连官方 MCP 只读调用）

- `list-nutrition-foods` 返回的 8 行营养值与 `src/data/snapshot.json`
  逐值一致（巨无霸 513kcal/961mg 钠、培根安格斯 707kcal/1037mg 钠、
  不素之霸 493/1012、麦香鱼 325/556、麦香鸡 369/731、V翅 192/594、
  美汁源 165/53、苹果片 32/0——苹果片的 0 是官方表真实值，非缺失）。
- `query-meals`（门店 1450713，21:44）在售 7 款，菜单价与快照一致
  （25.5 / 26.5 / 22.5 / 17 / 16 / 13 / 7）；培根安格斯厚牛堡不在售，
  与快照「菜单参考价 + 10-14 采集」的口径处理互相印证。
- 22:00:51 重新采集：6/8 在售且全部拿到官方核价（与菜单价一致）；
  不素之霸、培根安格斯缺席，按合并规则沿用各自时间戳的旧数据。

## 6. 合规扫描

- 全仓（不含 node_modules/dist）扫描 Token/密钥/手机号/邮箱模式：**无匹配**。
- 无官方图片外链（`menu-img.mcd.cn` 等）：**无匹配**；餐品视觉全部为
  `src/data/art.ts` + `FoodArt.tsx` 的原创 SVG。
- 「官方」字样仅出现在数据来源语境（官方 MCP / 官方核价 / 官方营养表 /
  官方数据快照）；「独立开发、非官方产品」声明出现在首页、冠军页、
  冠军卡 PNG、README 与 CONTEST_DECLARATION.md。
- `CONTEST_DECLARATION.md` 与官方仓库模板
  （M-China/mcd-developer-innovation-challenge）逐字比对一致
  （1522 字节，仅换行符差异，git 推送时归一化为 LF）。

## 7. 已知残留风险（如实列出）

1. **培根安格斯厚牛堡无核价**：只有 10-14 的菜单参考价。若评委核价，
   会看到它标着「菜单参考价」——这是设计行为，但确实少一份验证。
2. **单门店单渠道**：全部数据来自上海黄浦华旭国际大厦餐厅（1450713）、
   orderType=1/beType=1，未覆盖其他城市/门店/外送渠道。
3. **8 强有选择性偏差**：特意挑了能精确匹配官方营养表的 8 款，
   不是随机抽样。
4. **无真人试玩**：验收全部为自动化浏览器，未邀请真实用户；
   「10 秒理解」未经外部验证。
5. **agent-browser daemon 不稳定**：验收过程中 daemon 数次崩溃，
   靠短链重试完成；复现审计时需预留重试空间（不影响结论，
   所有通过项都有完整日志）。

## 文件清单

| 文件 | 内容 |
|---|---|
| `audit-01-home.png` | 手机视口首页（8 强名单 + 价格口径 + 分批采集时间） |
| `audit-02-match1.png` | 第 1 场对决 |
| `audit-03-reveal.png` | 数据揭晓（价格/热量/蛋白质/钠对比） |
| `audit-04-match7.png` | 第 7 场（总决赛） |
| `audit-05-champion.png` | 冠军页（晋级路线 + 淘汰者 + 完整对阵图） |
| `audit-06-restart.png` | 重新挑战后回到第 1 场 |
| `audit-07-card-render.png` | 冠军卡在页面中的渲染（750px 固定布局） |
| `audit-08-desktop.png` | 桌面视口（1280×800）冠军页 |
| `audit-09-demo-home.png` | 生产构建首页（无 Token Demo） |
| `audit-10-demo-champion.png` | 生产构建冠军页 |
| `../shots/audit-champion-card.png` | 真实导出的冠军卡 PNG（开发服） |
| `../shots/audit-demo-card.png` | 真实导出的冠军卡 PNG（生产构建） |
