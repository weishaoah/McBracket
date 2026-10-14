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
