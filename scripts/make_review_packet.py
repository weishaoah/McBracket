#!/usr/bin/env python3
"""Assemble a self-contained review packet for an outside reviewer.

The point is to hand a second opinion everything it needs in one paste: what
the project claims, the evidence behind those claims, the code that makes the
claims true or false, and the questions we cannot answer ourselves.

Regenerate after any change:
    python scripts/make_review_packet.py                 # -> REVIEW_PACKET.md
    python scripts/make_review_packet.py --no-tests      # slimmer

Usage:
    python scripts/make_review_packet.py [--out REVIEW_PACKET.md] [--no-tests]
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files the reviewer needs, in reading order.
SOURCES = [
    'src/types.ts',
    'src/engine/tournament.ts',
    'src/engine/championTitle.ts',
    'src/App.tsx',
    'src/components/MatchView.tsx',
    'src/components/DataReveal.tsx',
    'src/components/ChampionCard.tsx',
    'src/components/HomeView.tsx',
    'src/components/BracketView.tsx',
    'src/components/FoodArt.tsx',
    'scripts/fetch_snapshot.py',
]
TEST_FILE = 'src/engine/tournament.test.ts'

# Questions we genuinely cannot settle from inside the project. A good review
# answers these instead of restating what the README already says.
QUESTIONS = """\
请按下列顺序审，并**明确指出我说错或夸大的地方**（这是我找外部审查的唯一目的，
不需要为了照顾我而保留情面）：

### A. 数据真实性（最高优先级 —— 比赛会查）
1. `fetch_snapshot.py` 与 `snapshot.json` 里，有没有任何一处会让读者误以为
   当前页面数据是**实时**的？我已经修过 `mode` 字段（改成 `demo-snapshot`，
   页面显示「非实时」）和分批采集的时间区间，但可能还有漏网的措辞。
2. 「菜单价（元·字符串）vs 核价（分·整数）」的换算是否真的正确？
   请独立核一遍 `yuan_to_cents()` 和 `effectivePriceCents()`，
   这是本项目最容易出错、也最容易被评委一眼看穿的地方。
3. 营养数据只取「商品名精确匹配」，其余显示「暂无可靠数据」。
   这个降级策略有没有在某处被绕过（比如悄悄填了 0 或估算值）？

### B. 合规风险（会不会被取消资格或收到律师函）
4. 项目名含 "Mc"，README 与冠军卡上出现麦当劳商品名。
   以你的判断，这构成商标风险吗？声明「独立作品、非官方出品」的位置
   是否足够显眼？
5. `CONTEST_DECLARATION.md` 要求与官方模板逐字节一致，我已核对
   （md5 `91a7b32e`）。还有哪些参赛材料是容易被漏掉的形式要求？

### C. 代码正确性
6. `tournament.ts` 的晋级逻辑：有没有可能出现同一商品重复晋级、
   某场比赛被跳过、或 7 场没跑完就出冠军？（我有 11 条测试含 200 次随机对局，
   但测试可能有盲区 —— 请特别看测试**没有覆盖**的分支。）
7. `merge_items()` 的合并逻辑：分批采集时会不会错误地用旧数据覆盖新数据？
   `_score()` 的排序是否存在某种情况下会退化？
8. 有没有任何路径会执行写入类 Tool（下单/领券/抽奖）？

### D. 竞争力（这是比赛，排名只看 GitHub Star）
9. 以评审者/路人的视角：**这个 README 前三屏**能不能让人想点 Star？
   最劝退的地方在哪？
10. 项目最大的卖点应该是什么？我现在的说法
    （「真实 MCP 数据 + 8 强淘汰赛 + 可分享冠军卡」）是不是太平淡？
11. 有没有明显的「自嗨」痕迹 —— 即我觉得有价值、但外人根本不关心的部分？

### E. 诚实性审查（最重要）
12. 通读 `MCP_INTEGRATION.md` 与 `README.md`，
    找出所有**证据不足以支撑**的断言。我已经知道的一个自我质疑是：
    「8 强选择理由是价格带宽 + 品类分散」，但实际上有 6/8 没有官方核价验证。
    请把这类「说了但其实没做到」的地方都挑出来。
"""

KNOWN_ISSUES = """\
### 我自己已经知道的问题（不用重复指出，但欢迎说它比我想的更严重）

1. **核价只验证 2/8**：只有巨无霸（¥25.5）和美汁源（¥13.0）拿到了
   `calculate-price` 官方核价，其余 6 款降级为 `query-meals` 菜单价。
   原因是麦当劳菜单按营业时段切换，早餐时段汉堡不在菜单里。
   计划午间正餐时段重采补齐。
2. **Demo 模式就是唯一模式**：页面始终读静态快照，没有真正的实时路径。
   「模式 B（真实 MCP）」目前只是「开发者本地重新生成快照」，
   措辞上我尽量说清楚了，但这不是真正的双模式。
3. **单门店单渠道**：全部数据来自上海一家门店（1450713）、
   orderType=1/beType=1。换城市/门店的差异完全没有被覆盖。
4. **`query-meal-detail` 脚本支持但页面未使用**：集成文档里列了它，
   但游戏里没用到，属于「说了但没做」。
5. **营养表只覆盖常驻单品**：套餐和限定品一律「暂无可靠数据」，
   8 强能全部精确匹配是因为我**特意挑**了能匹配的 8 款
   —— 这有选择性偏差，不是随机抽样。
"""


def sh(*args: str) -> str:
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                              encoding='utf-8', errors='replace').stdout.strip()
    except OSError:
        return ''


def snapshot_summary() -> str:
    p = ROOT / 'src/data/snapshot.json'
    if not p.exists():
        return '_snapshot.json 不存在_'
    d = json.loads(p.read_text(encoding='utf-8'))
    rows = ['| code | 商品 | 菜单价 | 官方核价 | 价格来源 | 热量 | 采集时间 |',
            '|---|---|---:|---:|---|---:|---|']
    for i in d['items']:
        q = i.get('quotePriceCents')
        m = i.get('menuPriceCents')
        fmt = lambda c: '-' if c is None else f'¥{c / 100:g}'
        chk = ''
        if q is not None and m is not None:
            chk = ' ✓一致' if q == m else ' ✗**不一致**'
        n = i.get('nutrition')
        rows.append(
            f"| {i['code']} | {i['name']} | {fmt(m)} | {fmt(q)}{chk} | "
            f"{i.get('priceSource')} | {n['energyKcal'] if n else '无'} | "
            f"{i.get('collectedAt', '-')} |")
    cov = d.get('lastRun') or {}
    quoted = sum(1 for i in d['items'] if i.get('quotePriceCents'))
    return '\n'.join([
        f"- 门店：**{d['store']['name']}**（{d['store']['code']}）",
        f"- 渠道：{d.get('orderType')}",
        f"- 采集时间：{d.get('collectedFrom', d['collectedAt'])} ~ "
        f"{d.get('collectedTo', d['collectedAt'])} {d.get('collectedAtTimezone', '')}",
        f"- `mode`：`{d.get('mode')}`　`capturedWith`：`{d.get('capturedWith')}`",
        f"- 使用的 Tool：{', '.join(d.get('toolsUsed') or [])}",
        f"- **核价验证覆盖：{quoted}/{len(d['items'])}**"
        f"（上次运行新采 {cov.get("freshThisRun", 0)} 条、沿用 {cov.get("carriedFromPrevious", 0)} 条）",
        '',
        '\n'.join(rows),
    ])


def embed(path: str) -> str:
    p = ROOT / path
    if not p.exists():
        return f'_（{path} 不存在）_'
    text = p.read_text(encoding='utf-8')
    lang = 'python' if path.endswith('.py') else 'ts'
    return f'```{lang}\n{text}\n```'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='REVIEW_PACKET.md')
    ap.add_argument('--no-tests', action='store_true', help='omit the test file')
    args = ap.parse_args()

    files = list(SOURCES) + ([] if args.no_tests else [TEST_FILE])
    parts = [
        '# McBracket · 外部审查包',
        '',
        '> 自包含审查材料：项目背景 + 数据证据 + 全部源码 + 待审问题。',
        '> 重新生成：`python scripts/make_review_packet.py`（代码改了记得重跑）。',
        '',
        '### 怎么用',
        '',
        '1. **整篇复制粘贴**给 GPT / Claude 等外部模型（约 65KB，长上下文模型无压力）。',
        '2. 粘贴时**不要删 §0 的审查指令** —— 那段决定了它审什么；'
        '只丢源码进去，模型会退化成「夸一遍代码写得不错」。',
        '3. 若上下文实在不够，优先级：`§0 指令` → `§2 数据证据` → '
        '`§5 源码里的 types.ts / tournament.ts / fetch_snapshot.py`。',
        '4. **拿到回复后**：重点看它挑出的「说了但没做到」和「证据不足」，'
        '这两类问题我自己看不见。它夸的部分基本可以忽略。',
        '',
        '**审查目的**：我（作者）已在这个项目上投入大量上下文，存在明显盲区，',
        '需要外部视角找出**我说错、夸大或证据不足**的地方。',
        '**不需要客套，请直接指出问题。**',
        '',
        '---',
        '',
        '## 0. 给审查者的指令',
        '',
        QUESTIONS,
        '---',
        '',
        '## 1. 项目是什么',
        '',
        'McBracket 是一个参加「麦当劳中国开发者创新挑战赛」的网页小游戏：',
        '从 8 款**真实**麦当劳餐品中，通过 7 场一对一对决（8进4→4进2→决赛），',
        '选出用户最喜欢的餐品，生成可分享的冠军卡 PNG。',
        '',
        '比赛排名**只看 GitHub Star 数**（截止 2026-10-25），所以「能不能让人',
        '想点 Star」和「数据是否真实」同等重要。',
        '',
        '技术栈：React + TypeScript + Vite，纯前端，无后端、无数据库、无登录。',
        '数据来自麦当劳官方 MCP（`https://mcp.mcd.cn`）的**只读**采集快照。',
        '',
        '## 2. 数据证据（请逐条核）',
        '',
        snapshot_summary(),
        '',
        '## 3. 已知问题（作者自述）',
        '',
        KNOWN_ISSUES,
        '## 4. 项目元数据',
        '',
        '```',
        f'git log: {sh("git", "log", "--oneline", "-5")}',
        f'status : {sh("git", "status", "--short") or "(clean)"}',
        '```',
        '',
        '## 5. 源码',
        '',
    ]
    for f in files:
        parts += [f'### `{f}`', '', embed(f), '']

    parts += ['---', '', '## 6. 审查完请回答', '',
              '1. **有没有任何一处「说了但没做到」？**（最高优先级）',
              '2. 数据真实性上，最可能被评委抓出来的漏洞是什么？',
              '3. 如果只能改一件事来提高 Star 数，改什么？',
              '']

    out = ROOT / args.out
    out.write_text('\n'.join(parts), encoding='utf-8')
    size = out.stat().st_size
    print(f'written: {out}  ({size / 1024:.1f} KB)')
    print(f'files  : {len(files)}')
    print(f'建议：整篇复制粘贴；若上下文受限，先给 §0 + §2 + §5 的核心文件。')


if __name__ == '__main__':
    main()
