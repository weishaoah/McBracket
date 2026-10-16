# workbuddy.md · McBracket 开发过程记录

本项目（McBracket · 麦门最强餐品争霸赛）全程在 WorkBuddy 中开发，
本文按活动要求记录真实的使用过程，供 WorkBuddy 专项奖励核验。

## 开发环境

- WorkBuddy 桌面版（Windows），工作区 `G:/WorkBuddy`
- 项目目录：`G:/WorkBuddy/McBracket`
- 时间：2026-10-14 深夜 至 2026-10-15 凌晨（北京时间）

## WorkBuddy 在本项目中的实际使用

1. **规则与竞品研究**：读取官方挑战赛仓库 README（报名条件、必交文件、
   Star 排名规则），检索官方 Issues 与已有参赛作品，确认「餐品淘汰赛」方向
   无同质成熟项目。
2. **真实数据采集**：通过 WorkBuddy 连接的麦当劳官方 MCP（`mcd-mcp` 自定义
   连接器，Token 存于 WorkBuddy 的 MCP 配置中）执行只读调用：
   `now-time-info`、`query-nearby-stores`、`query-meals`、`list-nutrition-foods`、
   `calculate-price`。Demo 快照 `src/data/snapshot.json` 即来自这些真实调用
   （2026-10-14 11:26:56，官方时间基准）。
3. **代码编写**：全部源码（React + TypeScript + Vite）由 WorkBuddy 编写，
   包括淘汰赛引擎、数据揭晓、对阵图、冠军卡与 PNG 导出。
4. **质量验证**：WorkBuddy 运行 Vitest 测试（11 条）、TypeScript 构建检查，
   并驱动自动化浏览器（agent-browser）真实点击完成多轮完整 7 场对局、
   验证重新挑战与冠军卡 PNG 下载。
5. **数据陷阱的发现与修复**：开发中实测发现 `query-meals`（元·字符串）与
   `calculate-price`（分·整数）单位不一致、`query-meal-detail` 参数名为
   `code`、营业时间外菜单缩水等问题，均记录于 `MCP_INTEGRATION.md`。

## 诚实边界

- 页面展示的所有价格与营养数据均来自上述真实 MCP 调用或其快照；
  匹配不上的数据一律显示「暂无可靠数据」，未由模型生成或推测。
- 餐品插画为原创 SVG，非官方素材；冠军称号文案仅由真实数据与赛果推导。
- 冠军完全由用户的点击决定，WorkBuddy / AI 不参与比赛结果的任何判定。

---

## 2026-10-15 发布前审计会话（同一项目，续记）

**触发**：作者决定在截止前交付一个「符合规则、可公开试玩」的版本，
要求先做正式发布前审计再谈推送/部署/报名。

**WorkBuddy 在本轮实际做的事**：

1. **数据核查（直连官方 MCP 只读调用）**：拉取 `list-nutrition-foods`
   全表 160 行，逐值核对 8 强营养数据；查询当前时段菜单，确认
   培根安格斯厚牛堡不在售（与快照的「菜单参考价」口径互相印证）；
   确认苹果片 sodium=0 是官方表真实值而非缺失。
2. **修复采集管线三处缺陷**（`scripts/fetch_snapshot.py`）：
   - 营养缺失字段被 `or 0` 填成 0 → 改为 `null`，页面显示「—」；
   - 合并逻辑无门店/渠道门禁 → 增加 `channel` 字段与双门禁，
     不一致整体拒绝合并；种子集合外的历史行不合并；超 7 天旧行丢弃；
   - 「证据评分」式合并会让旧价静默覆盖新观测 → 改为字段级合并：
     新核价优先，旧核价仅在本次失败时补位并记录 `quoteCollectedAt`。
3. **补测试**：新增 `tests/test_data_pipeline.py`（21 条，Python 标准库
   unittest）与 `src/data/snapshot.test.ts`（15 条），后者把官方营养表
   实测值钉死为回归基线——未来任何人改数据都必须显式更新测试。
4. **前端口径修复**：每款餐品标注「官方核价 / 菜单参考价」；
   数据揭晓显示两侧采集时间与「沿用」说明；快照去重 + 场次安全索引，
   防止重复商品与错误晋级；快照不完整时显示数据错误面板而非白屏。
5. **重新采集**：22:00:51 用修复后的脚本实跑，6/8 在售全部拿到核价，
   不素之霸沿用 15:47 核价（时间戳保留），培根安格斯沿用 10-14 菜单参考价。
6. **浏览器验收**：agent-browser 手机视口完整 7 场 + 重开 + PNG 导出 +
   控制台零错误；对生产构建（dist）复跑无 Token Demo 全程，导出成功。
7. **合规扫描**：全仓无 Token/密钥/个人信息；插画均为原创 SVG；
   `CONTEST_DECLARATION.md` 与官方大赛仓库模板逐字比对一致
   （curl 官方原始字节后 diff，仅换行符差异）。
8. **材料更新**：README（真实核价覆盖 7/8、测试数、审计结论）、
   MCP_INTEGRATION（合并四规则、审计表）、REVIEW_PACKET（重新生成）、
   `docs/audit/`（截图 + AUDIT-EVIDENCE.md）。

**本轮踩到的环境坑**（已绕开，记录备查）：

- agent-browser CLI 版本升级后 `viewport` 命令改名为 `set viewport`，
  旧脚本全部失效——用 `--help` 核对后修正三个脚本。
- `agent-browser <cmd> | head/tail` 会因管道提前关闭收到 SIGTERM，
  必须重定向到文件再读（老问题，本轮又踩一次）。
- 审计 session 的 daemon 数次崩溃（`Daemon failed to start`），
  靠「单命令唤醒 + 短链重跑」完成；长链（75+ 命令）中途死亡两次，
  因此把导出证据拆成独立短链。
- 本机沙箱会拦截 `rm`（直接 SIGTERM），文件清理靠重跑覆盖实现。

**诚实边界（续）**：

- 本轮所有测试数字、截图、导出文件均为真实运行产物；
  唯一未覆盖的是真人试玩（作者明确记录为残留风险，未虚构用户反馈）。
- 培根安格斯厚牛堡截至审计时仍无核价，页面按「菜单参考价」展示，
  未用任何估算值补齐。

---

## 2026-10-16 Release Candidate 冻结会话（同一项目，续记）

**触发**：审计结果确认后，作者决定冻结候选版本，进入 RC 阶段：
先固化证据与材料，对外操作（建仓/推送/部署/报名）等确认后再执行。

**WorkBuddy 在本轮实际做的事**：

1. **冻结候选版本**：以 `22d3852` 为基线重跑全量验证（tsc PASS /
   Vitest 26/26 / Python 21/21 / build 2.65s），记录快照 git blob
   `62716180` 与 md5 `117dd0b7`，产出 `docs/RELEASE-RC1.md`；
   RC 冻结提交于 2026-10-16 10:22（8 个文件：RC 报告、部署工作流、
   试玩指南与模板、子路径实测截图、README/package.json/workbuddy.md
   更新）。提交哈希不写入文件——自引用哈希会随提交本身失效，
   以 `git log` 顶部记录为准。
2. **必交文件核对**：README / CONTEST_DECLARATION / MCP_INTEGRATION /
   mcp-config.example.json / workbuddy.md / LICENSE / 源代码齐全；
   参赛声明与官方模板逐字一致（md5 双方 `91a7b32e`）。
3. **措辞核查**：全仓检索「在售/实时」30 处逐一核对，确认页面从未声称
   8 款当前全部在售，该词只出现在带时间戳的采集记录中；结论是无误，
   未做改动（核查过程写入 RC 报告 §4）。
4. **部署就绪**：新增 `.github/workflows/deploy.yml`（push → tsc + Vitest
   → build → Pages）；发现 Vite 不复制 public 点文件，改在 build 脚本
   尾部用 node 写 `dist/.nojekyll`；本地以 `/McBracket/` 子路径
   HTTP + 浏览器双重实测通过。
5. **用户材料**：新增 `docs/PLAY_GUIDE.md`（只讲怎么玩，不宣传）与
   `docs/PLAYTEST_TEMPLATE.md`（试玩记录模板，含「不足 5 人如实写不足」
   的诚实约束）。

**诚实边界（再续）**：

- RC 报告中「未验证」一栏如实列出：0 人试玩、Pages 线上未访问、
  官方 Issue 未提交、培根安格斯核价未补齐——发布前不会把这些写成已完成。
- 试玩指南与模板只提供方法和格式，不含任何玩家反馈（尚未发生）。
