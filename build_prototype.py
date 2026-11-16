from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "static" / "prototype"
OUT.mkdir(parents=True, exist_ok=True)

SHIELD = '''<svg viewBox="0 0 48 54" fill="none" aria-hidden="true"><path d="M24 2 44 10v17c0 13-20 25-20 25S4 40 4 27V10Z" stroke="currentColor" stroke-width="2"/><path d="M24 8 38 14v13c0 8-14 18-14 18S10 35 10 27V14Z" fill="currentColor"/><path d="m24 14 2.4 6.7 7 .2-5.6 4.3 2 6.8-5.8-4-5.8 4 2-6.8-5.6-4.3 7-.2Z" fill="#fff3d9"/><path d="M17 36h14" stroke="#fff3d9" stroke-width="2"/></svg>'''
ART = '''<svg viewBox="0 0 360 320" fill="none" aria-hidden="true"><circle cx="206" cy="144" r="113" stroke="#e6bc79" stroke-opacity=".25"/><circle cx="206" cy="144" r="98" stroke="#e6bc79" stroke-opacity=".15"/><path d="m206 54 64 25v61c0 51-64 87-64 87s-64-36-64-87V79Z" fill="#d3a158" fill-opacity=".1" stroke="#e4bd82" stroke-width="2"/><path d="m206 85 8 23 25 1-20 15 7 24-20-14-20 14 7-24-20-15 25-1Z" fill="#e9c58d"/><path d="M173 169h66m-58 13h50m-42 13h34" stroke="#e9c58d" stroke-width="3"/><path d="M0 283h31v-31h17v-27h9v27h21v-46h14v-14h8v14h15v77h20v-38h14v-17h12v17h18v38h21v-25h22v-55h12v-17h9v17h17v80h21v-40h17v-30h9v30h22v40h31v37H0Z" fill="#f1d3a0" fill-opacity=".15"/><path d="M0 301c67-22 111 6 176-11s118-17 184 1" stroke="#e9c58d" stroke-opacity=".3"/></svg>'''


def header(user="李*明"):
    return f'''<header class="site-header"><div class="header-inner"><a class="brand" href="#"><span class="brand-text"><span class="brand-title">呼伦贝尔市深化扫黑除恶专项斗争有奖答题活动</span><span class="brand-subtitle">全民参与 · 共建平安</span></span></a><button class="user-chip" type="button">{user}</button></div></header>'''


def nav(active):
    items = [("home", "home", "首页"), ("rules", "rules", "规则"), ("ranking", "ranking", "榜单"), ("awards", "gift", "奖品")]
    return '<nav class="mobile-nav" aria-label="移动导航">' + "".join(
        f'<a href="#" class="{"active" if key == active else ""}"><span class="nav-symbol" aria-hidden="true">{icon(name)}</span>{label}</a>'
        for key, name, label in items
    ) + '</nav>'


ICONS = {
    "home": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></svg>',
    "rules": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4"/><path d="M9 11h7M9 15h7M9 7h3"/></svg>',
    "ranking": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h16"/><path d="M6 20v-7h3v7M15 20V6h3v14"/><path d="M10.5 20V10h3v10"/></svg>',
    "gift": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10h16v11H4z"/><path d="M2 7h20v3H2z"/><path d="M12 7v14"/><path d="M12 7C10 3 6 3 6 5.5S12 7 12 7Zm0 0c2-4 6-4 6-1.5S12 7 12 7Z"/></svg>',
    "list": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h.01M4 12h.01M4 18h.01"/></svg>',
    "trophy": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H4v2a4 4 0 0 0 4 4M16 6h4v2a4 4 0 0 1-4 4"/><path d="M12 13v4M8 21h8M9 21v-2h6v2"/></svg>',
    "coin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><path d="M9 9h6M9 12h6M12 8v8"/></svg>'
}

def icon(name):
    return f'<span class="ui-icon" aria-hidden="true">{ICONS.get(name, "")}</span>'


def doc(title, screen_class, body, extra_css=""):
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#A9C2EA"><title>{title}</title><link rel="stylesheet" href="../style.css"><link rel="stylesheet" href="../mobile.css"><link rel="stylesheet" href="prototype.css"><link rel="stylesheet" href="../theme.css"><style>{extra_css}</style></head><body class="proto {screen_class}">{body}</body></html>'''


PROTO_CSS = r'''
/* ===== 客户评审用移动端原型 ===== */
html, body.proto { width: 375px; min-height: 812px; margin: 0; overflow: hidden; background: var(--paper); }
body.proto { height: 812px; }
body.proto .site-header { height: 69px; }
body.proto .header-inner { padding: 0 17px; }
body.proto .brand-mark { width: 32px; height: 38px; }
body.proto .brand-title { font-size: 15px; letter-spacing: 1px; }
body.proto .brand-subtitle { font-size: 7px; letter-spacing: 1.3px; margin-top: 3px; }
body.proto .user-chip { min-height: 38px; padding: 7px 12px; font-size: 11px; max-width: 42vw; }
body.proto .page { width: 375px; max-width: none; margin: 0; padding: 15px 16px 82px; }
body.proto .footer { display: none; }
body.proto .card { padding: 18px; border-radius: 12px; }
body.proto .mobile-nav { height: 61px; }
body.proto .mobile-nav a { min-height: 47px; padding-top: 4px; }
body.proto .mobile-nav .nav-symbol { font-size: 19px; }

body.proto .hero { min-height: 0; padding: 23px 22px 21px; align-items: flex-start; border-radius: 14px; }
body.proto .hero .eyebrow { font-size: 8px; letter-spacing: 1.2px; margin-bottom: 9px; }
body.proto .hero h1 { font-size: 25px; line-height: 1.5; letter-spacing: .5px; margin-bottom: 9px; }
body.proto .hero p { font-size: 11px; line-height: 1.8; margin-bottom: 14px; max-width: 240px; }
body.proto .hero-meta { font-size: 9px; gap: 5px; }
body.proto .hero-meta span { padding: 4px 7px; }
body.proto .hero-art { width: 190px; height: 180px; right: -42px; bottom: -6px; opacity: .26; }
body.proto .home-grid { display: block; margin-top: 13px; }
body.proto .card-title { font-size: 15px; margin-bottom: 12px; }
body.proto .stats { margin: 10px 0 14px; }
body.proto .stat strong { font-size: 28px; }
body.proto .stat span { font-size: 10px; }
body.proto .btn { min-height: 45px; font-size: 14px; border-radius: 9px; }
body.proto .help { font-size: 10px; line-height: 1.7; }
body.proto .steps { margin-top: 13px; gap: 5px; }
body.proto .step { font-size: 9px; padding: 7px 2px; }
body.proto .step b { font-size: 9px; }
body.proto .proto-prize-strip { display: flex; gap: 5px; margin-top: 12px; flex-wrap: wrap; }
body.proto .proto-prize-strip span { background: #faf3e6; color: #8a6828; border: 1px solid #f0e2c6; border-radius: 20px; font-size: 9px; padding: 4px 8px; }

body.proto .back { font-size: 11px; margin-bottom: 8px; min-height: 26px; }
body.proto .page-heading { margin-bottom: 12px; }
body.proto .page-heading h1 { font-size: 21px; margin-bottom: 4px; }
body.proto .page-heading p { font-size: 11px; line-height: 1.6; }
body.proto .eyebrow { font-size: 8px; letter-spacing: 1.2px; }
body.proto .chip { font-size: 9px; padding: 3px 7px; }
body.proto .rules-list .rule-item { padding: 5px 0; }
body.proto .rule-item h3 { font-size: 13px; margin-bottom: 3px; }
body.proto .rule-item p { font-size: 10px; line-height: 1.7; margin: 0; }
body.proto .notice-box { font-size: 9px; padding: 8px 10px; line-height: 1.65; margin: 8px 0; }
body.proto .text-link { font-size: 10px; min-height: 30px; }

body.proto .question-head { margin-bottom: 9px; }
body.proto .question-head strong { font-size: 12px; }
body.proto .timer { font-size: 19px; }
body.proto .progress-track { height: 3px; margin-bottom: 10px; }
body.proto .question-stem { font-size: 16px; line-height: 1.55; margin-bottom: 11px; }
body.proto .options { gap: 7px; }
body.proto .option { min-height: 47px; padding: 10px 11px; gap: 10px; font-size: 12px; line-height: 1.55; border-radius: 8px; }
body.proto .option-letter { width: 27px; height: 27px; flex-basis: 27px; font-size: 10px; }
body.proto .question-actions { gap: 7px; margin-top: 10px; }
body.proto .question-actions .btn { min-height: 42px; font-size: 12px; padding: 8px 14px; }
body.proto .question-map { gap: 5px; margin-top: 9px; }
body.proto .question-map button { width: 28px; height: 28px; font-size: 9px; border-radius: 6px; }
body.proto .question-map button:nth-child(n+9) { display: none; }
body.proto .proto-map-note { font-size: 8px; color: var(--muted); margin-top: 5px; }
body.proto .save-status { font-size: 8px; margin-top: 7px; }

body.proto .result-header h2 { font-size: 19px; margin-bottom: 3px; }
body.proto .score { font-size: 62px; margin: 5px 0 2px; }
body.proto .score small { font-size: 11px; }
body.proto .result-header .help { font-size: 10px; margin-bottom: 0; }
body.proto .action-row { margin-top: 12px; gap: 7px; }
body.proto .action-row .btn { min-height: 41px; font-size: 11px; padding: 8px 10px; }
body.proto .analysis { margin-top: 12px; }
body.proto .analysis h3 { font-size: 13px; margin-bottom: 8px; }
body.proto details { padding: 7px 0; font-size: 10px; }
body.proto details p { font-size: 9px; line-height: 1.65; margin: 5px 0 0; }
body.proto .proto-breakdown { display: flex; gap: 6px; margin: 8px 0 0; }
body.proto .proto-breakdown span { flex: 1; background: #fbf7f0; border: 1px solid var(--line); border-radius: 7px; padding: 6px 4px; text-align: center; font-size: 9px; color: var(--muted); }
body.proto .proto-breakdown b { display: block; font-size: 14px; color: var(--ink); margin-bottom: 2px; }
body.proto.result .order-card { padding: 8px 11px; margin-bottom: 6px; }
body.proto.result .order-card h3 { font-size: 11px; margin-bottom: 2px; }
body.proto.result .order-card p { font-size: 8.5px; line-height: 1.5; margin: 2px 0; }

body.proto .lottery-stage { margin: 10px 0 12px; padding: 14px 10px 18px; }
body.proto .flip-card { width: 138px; height: 170px; border-width: 4px; }
body.proto .flip-card b { font-size: 46px; }
body.proto .flip-card span { font-size: 11px; }
body.proto .proto-prize-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; }
body.proto .proto-prize-grid div { border: 1px solid var(--line); background: #fffdf8; border-radius: 8px; padding: 7px 8px; display: flex; align-items: center; gap: 7px; }
body.proto .proto-prize-grid i { font-style: normal; width: 24px; height: 24px; border-radius: 7px; background: #faf1df; color: var(--gold); display: grid; place-items: center; font-size: 12px; flex: 0 0 24px; }
body.proto .proto-prize-grid b { display: block; font-size: 10px; line-height: 1.3; }
body.proto .proto-prize-grid small { display: block; color: var(--muted); font-size: 8px; margin-top: 2px; }

body.proto .rank-me { padding: 10px 12px; margin-bottom: 9px; }
body.proto .rank-me strong { font-size: 11px; }
body.proto .rank-me span { font-size: 11px; color: var(--red); font-weight: 700; }
body.proto .proto-rank-list { display: block; }
body.proto .proto-rank-row { display: grid; grid-template-columns: 30px minmax(0, 1fr) auto; grid-template-areas: "rank name points" "rank name time"; column-gap: 8px; padding: 8px 2px; border-bottom: 1px solid var(--line); align-items: center; }
body.proto .proto-rank-row:last-child { border-bottom: 0; }
body.proto .proto-rank-row .rk { grid-area: rank; font: 700 17px Georgia, serif; color: var(--gold); text-align: center; }
body.proto .proto-rank-row .nm { grid-area: name; font-size: 11px; font-weight: 600; }
body.proto .proto-rank-row .pt { grid-area: points; font-size: 13px; font-weight: 700; color: var(--red); text-align: right; }
body.proto .proto-rank-row .tm { grid-area: time; font-size: 8px; color: var(--muted); text-align: right; }
body.proto .proto-rank-row.top .rk { color: var(--red); }

body.proto .order-card { padding: 11px 12px; margin-bottom: 8px; border-radius: 9px; }
body.proto .order-card h3 { font-size: 12px; margin-bottom: 3px; }
body.proto .order-card p { font-size: 9px; line-height: 1.65; margin: 3px 0; }
body.proto .order-top { gap: 6px; }
body.proto .order-card .chip { font-size: 8px; }
body.proto .proto-award-card { background: linear-gradient(135deg, #fff7ea, #fffdf8); border: 1px solid #eeddbb; border-radius: 10px; padding: 10px 12px; margin: 9px 0 10px; }
body.proto .proto-award-card b { font-size: 11px; color: #7d5c22; }
body.proto .proto-award-card p { font-size: 9px; line-height: 1.65; color: #8b744e; margin: 3px 0 0; }

body.proto.modal-screen .page { filter: none; }
body.proto.modal-screen .modal-overlay { position: fixed; inset: 0; display: flex; align-items: flex-end; padding: 0; background: #24161b99; backdrop-filter: blur(2px); z-index: 90; }
body.proto.modal-screen .modal { width: 375px; max-width: none; max-height: 650px; border-radius: 18px 18px 0 0; padding: 18px 18px calc(18px + env(safe-area-inset-bottom)); }
body.proto.modal-screen .modal h2 { font-size: 18px; margin-bottom: 10px; }
body.proto.modal-screen .modal-close { width: 34px; height: 34px; font-size: 18px; }
body.proto.modal-screen .field { font-size: 11px; margin-bottom: 9px; gap: 4px; }
body.proto.modal-screen .field input, body.proto.modal-screen .field textarea { min-height: 40px; font-size: 13px; padding: 9px 10px; }
body.proto.modal-screen .field textarea { min-height: 58px; }
body.proto.modal-screen .field.check { font-size: 10px; min-height: 30px; }
body.proto.modal-screen .field.check input { width: 16px; height: 16px; }
body.proto.modal-screen .btn { min-height: 42px; font-size: 13px; }
body.proto.modal-screen .help { font-size: 9px; }
'''

(OUT / "prototype.css").write_text(PROTO_CSS, encoding="utf-8")

screens = []

# 01 首页
home = f'''{header()}<main class="page"><section class="hero"><div class="hero-copy"><div class="eyebrow">深化扫黑除恶 · 共建平安家园</div><h1>呼伦贝尔市深化扫黑除恶专项斗争<br><span>有奖答题活动</span></h1><p>让法治精神深入人心，让平安建设与你同行。</p><div class="hero-meta"><span>● 活动进行中</span><span>11.13 — 11.20</span><span>全民参与</span></div></div></section><section class="card"><div class="card-title">{icon('list')}今天，也为平安加一分</div><div class="stats"><div class="stat"><strong>1</strong><span>今日剩余机会</span></div><div class="stat"><strong>86</strong><span>我的累计积分</span></div><div class="stat"><strong>80</strong><span>抽奖达标分数</span></div></div><button class="btn full" type="button">开始答题，赢取好礼 <span>→</span></button><p class="help center">每套 10 题 · 每题 2 分钟 · 满分 100 分</p><div class="steps"><span class="step"><b>01</b> 学习知识</span><span class="step"><b>02</b> 答题达标</span><span class="step"><b>03</b> 抽取好礼</span><span class="step"><b>04</b> 积分评优</span></div><div class="proto-prize-strip"><span>现金红包 0.5–2 元</span><span>积分 +10 / +20</span><span>前 50 名评优</span></div></section><section class="card" style="margin-top:10px;padding:12px 14px"><div style="display:flex;align-items:center;justify-content:space-between;gap:10px"><div><div style="font-size:12px;font-weight:700">积分前 50 名 · 三档评优</div><p class="help" style="margin:3px 0 0">第 1—10 名约 300 元 · 11—30 名约 150 元 · 31—50 名约 80 元</p></div><button class="btn small secondary" type="button">看榜单</button></div></section></main>{nav("home")}'''
screens.append(("01", "活动首页", "home", home, "首页聚合活动主题、剩余机会、累计积分、达标线和开始答题入口，并提示答题规则与奖品类型。"))

# 02 规则
rules_rows = [
    ("答题与达标", "每套 10 题：单选 5 题 × 8 分，多选 5 题 × 12 分。多选须全部选对，漏选、错选均不得分；达到 80 分获得抽奖资格。"),
    ("每题限时", "每题 2 分钟，超时自动进入下一题，未作答不得分；整卷最多 20 分钟。"),
    ("机会与复活", "每日免费答题 1 次；本次未达标可申请复活 1 次，当日有效，不跨天累计。复活后重新开始一套新题并重新计时，不继承上一套剩余时间；不设额外恢复有效期。"),
    ("抽奖奖品", "谢谢惠顾、积分 +10、积分 +20、现金红包 0.5 元 / 1 元 / 2 元。库存、预算与个人中奖上限由系统校验。"),
    ("积分与话费奖励", "取单套最高分（80 分及以上）转为积分，加抽奖积分；多套不累计。前 50 名话费奖励：第 1—10 名每人 300 元、第 11—30 名每人 150 元、第 31—50 名每人 100 元；活动结束后填写手机号，统一发放。"),
]
rules = f'''{header()}<main class="page"><a class="back" href="#">← 返回首页</a><div class="page-heading"><div><div class="eyebrow">活动说明</div><h1>活动规则</h1><p>开始前花一分钟，了解这场知识之旅。</p></div><span class="chip green">正式规则</span></div><section class="card rules-list">{"".join(f'<div class="rule-item"><h3>{a}</h3><p>{b}</p></div>' for a,b in rules_rows)}<div class="notice-box">主办单位：中共呼伦贝尔市委政法委员会　活动时间：2026.11.13—11.20</div><button class="btn full" type="button">我已了解，进入活动 →</button></section></main>{nav("rules")}'''
screens.append(("02", "活动规则", "rules", rules, "规则页明确题型分值、80 分达标线、每题 2 分钟、复活次数、六类奖品和评优三档，减少“答对 8 题为何不达标”的咨询。"))

# 03 单选
single = f'''{header()}<main class="page"><div class="question-head"><span><span class="chip red">单项选择</span> <span class="muted" style="font-size:10px">选对得 8 分</span></span><span class="timer">01:47</span></div><section class="card"><div class="question-head"><strong>第 03 题 <span class="muted">/ 10</span></strong><span class="muted" style="font-size:10px">已完成 2 题</span></div><div class="progress-track"><i style="width:20%"></i></div><h1 class="question-stem">发现涉黑涉恶违法犯罪线索，应当如何处理？</h1><div class="options"><button class="option selected" type="button"><span class="option-letter">①</span><span>依法向有关机关举报</span></button><button class="option" type="button"><span class="option-letter">②</span><span>在网络编造未经核实的信息</span></button><button class="option" type="button"><span class="option-letter">③</span><span>采取暴力方式私自报复</span></button><button class="option" type="button"><span class="option-letter">④</span><span>帮助违法人员隐瞒事实</span></button></div><p class="help">本题为单选题，请选择一个答案。</p><p class="help">本题限时 120 秒，超时自动进入下一题，未作答不得分。</p><div class="question-actions"><button class="btn" type="button">下一题 →</button></div><div class="question-map" aria-label="答题进度"><button class="done" type="button">1</button><button class="done" type="button">2</button><button class="current" type="button">3</button><button type="button">4</button><button type="button">5</button><button type="button">6</button><button type="button">7</button><button type="button">8</button><button type="button">9</button><button type="button">10</button></div><div class="save-status">进度已同步，退出后可在有效期内续答</div><div class="proto-map-note">题号仅展示进度，按顺序作答，不能返回已跳过的题目</div></section><div class="action-row"><button class="text-link" type="button">保存并返回首页</button><button class="text-link" type="button">提前交卷</button></div></main>{nav("home")}'''
screens.append(("03", "答题页 · 单选", "quiz", single, "单选每题 8 分，选项整行可点；右上角显示本题倒计时，底部题号展示进度但不可跳转。"))

# 04 多选
multi = f'''{header()}<main class="page"><div class="question-head"><span><span class="chip red">多项选择</span> <span class="muted" style="font-size:10px">全部选对得 12 分</span></span><span class="timer">01:32</span></div><section class="card"><div class="question-head"><strong>第 04 题 <span class="muted">/ 10</span></strong><span class="muted" style="font-size:10px">已完成 3 题</span></div><div class="progress-track"><i style="width:30%"></i></div><h1 class="question-stem">参与平安建设，以下哪些做法是正确的？</h1><div class="options"><button class="option selected" type="button"><span class="option-letter">①</span><span>依法向有关机关举报</span></button><button class="option selected" type="button"><span class="option-letter">②</span><span>保护个人安全并保留线索</span></button><button class="option" type="button"><span class="option-letter">③</span><span>采取暴力方式私自报复</span></button><button class="option" type="button"><span class="option-letter">④</span><span>帮助违法人员隐瞒事实</span></button></div><p class="help">本题为多选题，请选出全部正确答案。</p><p class="help">本题限时 120 秒，超时自动进入下一题，未作答不得分。</p><div class="question-actions"><button class="btn" type="button">下一题 →</button></div><div class="question-map" aria-label="答题进度"><button class="done" type="button">1</button><button class="done" type="button">2</button><button class="done" type="button">3</button><button class="current" type="button">4</button><button type="button">5</button><button type="button">6</button><button type="button">7</button><button type="button">8</button><button type="button">9</button><button type="button">10</button></div><div class="save-status">进度已同步，退出后可在有效期内续答</div><div class="proto-map-note">已选 2 项；漏选、错选均不得分</div></section></main>{nav("home")}'''
screens.append(("04", "答题页 · 多选", "quiz multi", multi, "多选必须全部选对才得 12 分，漏选、多选、错选均为 0 分；已选项用红色描边反馈。"))

# 05 结果达标
result = f'''{header()}<main class="page"><section class="card"><div class="result-header"><div class="eyebrow">本次成绩</div><h2>答题达标，收获满满！</h2><div class="score">84<small>/ 100 分</small></div><p class="help">已达到 80 分抽奖门槛，快去揭晓你的好礼。</p><div class="proto-breakdown"><span><b>3 / 5</b>单选答对</span><span><b>5 / 5</b>多选答对</span><span><b>84</b>本次得分</span></div></div><div class="action-row"><button class="btn" type="button">去转盘，抽好礼 →</button><button class="btn secondary" type="button">查看积分榜</button><button class="btn secondary" type="button">返回首页</button></div></section><section class="card" style="margin-top:10px"><h3>接下来</h3><div class="order-card" style="margin:0 0 6px"><div class="order-top"><h3>转盘抽奖</h3><span class="chip gold">待参与</span></div><p>本次 84 分已达标，可参加一次转盘抽奖。</p></div><div class="order-card" style="margin:0 0 6px"><div class="order-top"><h3>积分排名</h3><span class="chip green">已计入</span></div><p>84 分计入排名；抽奖积分另计，仅 80 分以上答题积分生效。</p></div><div class="order-card" style="margin:0"><div class="order-top"><h3>话费奖励</h3><span class="chip">前 50 名</span></div><p>活动结束后填写手机号，按三档统一发放话费。</p></div></section></main>{nav("home")}'''
screens.append(("05", "结果页 · 达标", "result", result, "结果页展示得分、达标状态和“单选/多选答对”构成；84 分示例对应 3 道单选 + 5 道多选，直观解释 80 分临界规则。"))

# 06 结果未达标
fail = f'''{header()}<main class="page"><section class="card"><div class="result-header"><div class="eyebrow">继续加油</div><h2>再接再厉，平安知识多一分</h2><div class="score">76<small>/ 100 分</small></div><p class="help">本次未达到 80 分抽奖门槛，可申请当日复活机会。</p><div class="proto-breakdown"><span><b>5 / 5</b>单选答对</span><span><b>3 / 5</b>多选答对</span><span><b>76</b>本次得分</span></div></div><div class="notice-box">答对 8 题不一定达标：5 道单选 + 3 道多选 = 40 + 36 = 76 分。多选必须全部选对才得分。</div><div class="action-row"><button class="btn" type="button">申请复活，再答一次 →</button><button class="btn secondary" type="button">查看今日机会</button></div></section><section class="card analysis"><h3>今日机会</h3><div class="order-card" style="margin:0"><div class="order-top"><h3>免费答题机会</h3><span class="chip">已使用</span></div><p>每日 1 次 · 次日 0 点重置</p></div><div class="order-card" style="margin:0"><div class="order-top"><h3>复活答题机会</h3><span class="chip gold">可申请 1 次</span></div><p>仅本次未达标可申请，当日有效</p></div></section></main>{nav("home")}'''
screens.append(("06", "结果页 · 未达标与复活", "result", fail, "未达标页用 76 分算例解释“答对 8 题仍可能不达标”，并提供当日复活入口；达标用户不展示复活。"))

# 07 抽奖
prizes = [("谢谢惠顾", "本次未中奖", "◇"), ("积分 +10", "直接计入总积分", "＋"), ("积分 +20", "直接计入总积分", "＋"), ("现金红包 0.5 元", "微信红包", "¥"), ("现金红包 1 元", "微信红包", "¥"), ("现金红包 2 元", "微信红包", "¥")]
lottery = f'''{header()}<main class="page"><div class="page-heading" style="margin-bottom:8px"><div><div class="eyebrow">答题有礼</div><h1>答题有礼，好运开启</h1><p>本次 84 分 · 已获得抽奖资格</p></div><span class="chip gold">待抽奖</span></div><section class="card"><div class="wheel-wrap"><div class="wheel-pointer"></div><div class="wheel"><div class="wheel-label on-red" style="--a:30deg">谢谢惠顾</div><div class="wheel-label on-cream" style="--a:90deg">积分 +10</div><div class="wheel-label on-red" style="--a:150deg">积分 +20</div><div class="wheel-label on-cream" style="--a:210deg">红包 0.5 元</div><div class="wheel-label on-red" style="--a:270deg">红包 1 元</div><div class="wheel-label on-cream" style="--a:330deg">红包 2 元</div></div><button class="wheel-center" type="button">抽奖</button></div><p class="help center" style="margin:8px 0 0">每套达标成绩仅可抽取一次，重复点击返回原结果。</p></section><div class="notice-box" style="margin-top:10px">库存、每日投放量、红包预算和个人中奖上限由服务端实时校验；奖品抽完时保留抽奖机会。</div></main>{nav("home")}'''
screens.append(("07", "抽奖页", "lottery", lottery, "抽奖页采用六格转盘，六类奖品一屏可见；积分奖品抽中后直接入账，现金红包进入发放流程。"))

# 08 排行榜
rows = [("1", "张*明", "186", "18分22秒"), ("2", "李*娜", "172", "16分51秒"), ("3", "王*刚", "164", "19分06秒"), ("4", "刘*洋", "158", "17分44秒"), ("5", "赵*敏", "151", "20分13秒"), ("6", "陈*杰", "146", "18分39秒"), ("7", "孙*丽", "140", "21分02秒")]
rank = f'''{header()}<main class="page"><div class="page-heading" style="margin-bottom:9px"><div><div class="eyebrow">共同进步</div><h1>每一分努力，都值得被看见</h1><p>榜单实时更新，活动结束后冻结最终排名</p></div><span class="chip green">实时榜单</span></div><section class="card rank-me"><div class="question-head" style="margin:0"><strong>我的排名 · 第 28 名</strong><span>86 积分</span></div></section><section class="card"><div class="section-heading" style="margin:0 0 4px"><h2 style="font-size:15px">积分榜前100名</h2><span class="text-link" style="font-size:9px">获奖公示 →</span></div><div class="proto-rank-list">{"".join(f'<div class="proto-rank-row {"top" if i<3 else ""}"><span class="rk">{r}</span><span class="nm">{n}</span><span class="pt">{p}</span><span class="tm">用时 {t}</span></div>' for i,(r,n,p,t) in enumerate(rows))}</div><p class="help center" style="margin:7px 0 0">按单套最高分（80 分以上）加抽奖积分排名；多套不累计，昵称已脱敏，同分依次比较用时</p></section></main>{nav("ranking")}'''
screens.append(("08", "排行榜", "ranking", rank, "榜单展示前 100 名、本人排名和脱敏昵称；手机端采用卡片式行布局，无需左右拖动。"))

# 09 我的奖品
awards = f'''{header()}<main class="page"><div class="page-heading" style="margin-bottom:8px"><div><div class="eyebrow">我的奖品</div><h1>我的奖品</h1><p>记录每一份收获，也感谢你的每一次参与。</p></div><a class="text-link" href="#" style="font-size:9px">获奖公示 →</a></div><section class="card"><article class="order-card"><div class="order-top"><h3>现金红包 1 元</h3><span class="chip green">已领取</span></div><p>订单号：HB202611130028<br>获得时间：2026-11-13 10:26</p></article><article class="order-card"><div class="order-top"><h3>积分 +10</h3><span class="chip green">已发放</span></div><p>订单号：PT202611130016<br>获得时间：2026-11-13 10:18<br>已计入累计积分，无需填写收货信息。</p></article><article class="order-card"><div class="order-top"><h3>话费奖励 150 元</h3><span class="chip gold">待填写手机号</span></div><p>第 11—30 名每人 150 元；活动结束后由主办方统一发放。</p><button class="btn small secondary" type="button" style="margin-top:4px">填写手机号</button></article><div class="proto-award-card"><b>评优奖励说明</b><p>第 1—10 名每人 300 元，第 11—30 名每人 150 元，第 31—50 名每人 100 元；活动结束后填写手机号，统一发放话费。</p></div><div class="privacy-note">您的手机号仅用于本次活动话费奖励发放，不会用于其他用途，也不会向无关第三方泄露。</div></section></main>{nav("awards")}'''
screens.append(("09", "我的奖品", "awards", awards, "我的奖品区分现金红包、已入账积分和评优实物；积分奖励无需登记，评优实物进入领奖信息填写。"))

# 10 领奖登记（底部弹层）
claim = f'''{header()}<main class="page" aria-hidden="true"><div class="page-heading" style="margin-bottom:8px"><div><div class="eyebrow">我的奖品</div><h1>我的奖品</h1><p>记录每一份收获，也感谢你的每一次参与。</p></div></div><section class="card"><article class="order-card"><div class="order-top"><h3>话费奖励 150 元</h3><span class="chip gold">待填写手机号</span></div><p>第 11—30 名每人 150 元；活动结束后统一发放。</p></article><article class="order-card"><div class="order-top"><h3>现金红包 1 元</h3><span class="chip green">已领取</span></div><p>订单号：HB202611130028</p></article></section></main>{nav("awards")}<div class="modal-overlay"><section class="modal" role="dialog" aria-modal="true" aria-label="填写话费领取手机号"><button class="modal-close" type="button" aria-label="关闭">×</button><h2>填写话费领取手机号</h2><form><label class="field">手机号<input value="138****6688" readonly></label><div class="privacy-note">您的手机号仅用于本次活动话费奖励发放，不会用于其他用途，也不会向无关第三方泄露。</div><p class="help">活动结束后由主办方统一发放话费，请确认号码准确。</p><button class="btn full" type="button">保存手机号</button></form></section></div>'''
screens.append(("10", "领奖信息登记", "modal-screen", claim, "领奖信息以底部弹层填写，支持快递地址或线下领取；姓名、手机号、地址仅用于本次活动履约。"))

for num, title, cls, body, _ in screens:
    (OUT / f"{num}-{cls.replace(' ', '-')}.html").write_text(doc(title, cls, body), encoding="utf-8")

# 总览看板
cards = "".join(f'''<figure><img src="screens/{num}-{cls.replace(' ', '-')}.png" alt="{title}"><figcaption><b>{num}</b>{title}</figcaption></figure>''' for num, title, cls, _, _ in screens)
board = f'''<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>活动页面原型总览</title><style>
:root{{--red:#A9C2EA;--ink:#12233c;--muted:#66758a;--paper:#f4f7fb;--line:#dbe5f0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",sans-serif}}
header{{padding:34px 40px 22px;display:flex;justify-content:space-between;align-items:flex-end;gap:20px;border-bottom:1px solid var(--line)}}
h1{{font-size:26px;margin:0 0 6px;letter-spacing:.5px}}p{{margin:0;color:var(--muted);font-size:13px;line-height:1.8}}
.badge{{color:var(--red);border:1px solid #d9b7b1;background:#fff7f4;border-radius:20px;padding:7px 12px;font-size:11px;white-space:nowrap}}
main{{display:grid;grid-template-columns:repeat(5,1fr);gap:26px 22px;padding:28px 40px 50px;max-width:1800px;margin:auto}}
figure{{margin:0;background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px;box-shadow:0 10px 30px #3b251508}}
figure img{{width:100%;display:block;border-radius:9px;border:1px solid #eee7dc}}
figcaption{{display:flex;gap:8px;align-items:center;font-size:12px;margin-top:10px;color:#544b48}}
figcaption b{{color:var(--red);font:700 11px Georgia,serif}}
footer{{padding:0 40px 38px;color:var(--muted);font-size:11px;line-height:1.8}}
@media(max-width:1200px){{main{{grid-template-columns:repeat(3,1fr)}}}}@media(max-width:720px){{main{{grid-template-columns:repeat(2,1fr);padding:20px}}header{{padding:24px 20px;display:block}}.badge{{display:inline-block;margin-top:12px}}}}
</style></head><body><header><div><h1>呼伦贝尔市深化扫黑除恶专项斗争有奖答题活动</h1><p>移动端活动页面原型 · 共 10 屏 · 视觉与交互示意</p></div><div class="badge">主办：中共呼伦贝尔市委政法委员会</div></header><main>{cards}</main><footer>说明：本原型用于客户评审，页面内数据、昵称、订单号为示意数据；正式题库、奖品档位与活动时间以主办方最终确认为准。</footer></body></html>'''
(OUT / "board.html").write_text(board, encoding="utf-8")

print("screens:", len(screens))
for num, title, cls, _, _ in screens:
    print(num, title, f"{num}-{cls.replace(' ', '-')}.html")
