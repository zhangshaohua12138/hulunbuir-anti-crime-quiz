"""每日活动概览邮件。

环境变量：
  SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / MAIL_TO / MAIL_FROM
未配置 SMTP 时只打印报告，不发送。
"""
import json
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

sys.path.insert(0, '/opt/hulunbuir-quiz')
import server

TZ = timezone(timedelta(hours=8))


def money(cents):
    return f'{int(cents or 0) / 100:.2f}'


def build():
    today = datetime.now(TZ).strftime('%Y-%m-%d')
    with server.transaction() as c:
        cfg = server.config(c)
        users_total = c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        users_new = c.execute("SELECT COUNT(*) FROM users WHERE date(created,'unixepoch','+8 hours')=?", (today,)).fetchone()[0]
        attempts = c.execute("SELECT COUNT(*) FROM attempts WHERE day=? AND status='submitted'", (today,)).fetchone()[0]
        passed = c.execute("SELECT COUNT(*) FROM attempts WHERE day=? AND status='submitted' AND passed=1", (today,)).fetchone()[0]
        orders_today = c.execute('SELECT COUNT(*) FROM orders WHERE day=?', (today,)).fetchone()[0]
        cash_today = c.execute("SELECT COALESCE(SUM(amountCents),0) FROM orders WHERE day=? AND type='cash'", (today,)).fetchone()[0]
        cash_total = c.execute("SELECT COALESCE(SUM(amountCents),0) FROM orders WHERE type='cash'").fetchone()[0]
        pending_cash = c.execute("SELECT COUNT(*) FROM orders WHERE type='cash' AND status IN ('pending','processing','retrying','wait_confirm','sent','held')").fetchone()[0]
        pending_grant = c.execute("SELECT COUNT(*) FROM orders WHERE type='phone' AND status!='granted'").fetchone()[0]
        board = c.execute('''WITH submitted AS (SELECT * FROM attempts WHERE status='submitted'),
            best_day AS (SELECT p.*, ROW_NUMBER() OVER (PARTITION BY user_id,day ORDER BY score DESC, seconds ASC, submitted ASC) rn FROM submitted p),
            agg AS (SELECT user_id, SUM(score) points FROM best_day WHERE rn=1 GROUP BY user_id)
            SELECT u.nickname, COALESCE(u.bonus_points,0)+a.points points FROM users u JOIN agg a ON a.user_id=u.id
            ORDER BY points DESC LIMIT 5''').fetchall()
        state = server.state(cfg)
        frozen = bool(c.execute("SELECT 1 FROM settings WHERE key='frozen'").fetchone())

    daily_budget = server.effective_daily_budget(cfg)
    rows = ''.join(
        f'<tr><td style="padding:6px 10px">{i+1}</td><td style="padding:6px 10px">{r[0]}</td>'
        f'<td style="padding:6px 10px;text-align:right">{r[1]}</td></tr>'
        for i, r in enumerate(board)
    ) or '<tr><td colspan="3" style="padding:8px 10px;color:#777">暂无上榜记录</td></tr>'

    html = f'''<div style="font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;color:#12233c">
<h2 style="margin:0 0 4px">{cfg.get('title','活动')}</h2>
<p style="color:#66758a;margin:0 0 16px">每日活动概览 · {today} · 活动状态：{state}{'（已封榜）' if frozen else ''}</p>
<table style="border-collapse:collapse;font-size:14px">
<tr><td style="padding:6px 10px;color:#66758a">新增用户</td><td style="padding:6px 10px"><b>{users_new}</b> / 累计 {users_total}</td></tr>
<tr><td style="padding:6px 10px;color:#66758a">当日答题</td><td style="padding:6px 10px"><b>{attempts}</b> 套，达标 {passed} 套</td></tr>
<tr><td style="padding:6px 10px;color:#66758a">当日中奖订单</td><td style="padding:6px 10px"><b>{orders_today}</b> 笔</td></tr>
<tr><td style="padding:6px 10px;color:#66758a">当日红包支出</td><td style="padding:6px 10px">¥{money(cash_today)}（每日预算 ¥{money(daily_budget)}）</td></tr>
<tr><td style="padding:6px 10px;color:#66758a">累计红包支出</td><td style="padding:6px 10px">¥{money(cash_total)} / 总预算 ¥{money(cfg.get('budgetCents'))}</td></tr>
<tr><td style="padding:6px 10px;color:#66758a">待处理</td><td style="padding:6px 10px">红包待确认/待发 {pending_cash} 笔，话费待发放 {pending_grant} 笔</td></tr>
</table>
<h3 style="margin:20px 0 8px;font-size:15px">积分榜前 5</h3>
<table style="border-collapse:collapse;font-size:14px;min-width:320px">
<tr style="background:#f4f7fb"><th style="padding:6px 10px;text-align:left">排名</th><th style="padding:6px 10px;text-align:left">昵称</th><th style="padding:6px 10px;text-align:right">积分</th></tr>
{rows}
</table>
<p style="color:#98a6b8;font-size:12px;margin-top:18px">本邮件由活动系统自动发送。</p>
</div>'''
    subject = f"[{cfg.get('title','活动')}] {today} 活动概览"
    return subject, html


def main():
    subject, html = build()
    host = os.getenv('SMTP_HOST', '').strip()
    user = os.getenv('SMTP_USER', '').strip()
    password = os.getenv('SMTP_PASS', '').strip()
    to_addr = os.getenv('MAIL_TO', '1141892805@qq.com').strip()
    from_addr = os.getenv('MAIL_FROM', user).strip() or user
    port = int(os.getenv('SMTP_PORT', '465'))

    if not (host and user and password and to_addr):
        print('SMTP_NOT_CONFIGURED')
        print(subject)
        print(html[:500])
        return 0

    msg = MIMEText(html, 'html', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = formataddr(('活动系统', from_addr))
    msg['To'] = to_addr

    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, timeout=20)
    else:
        smtp = smtplib.SMTP(host, port, timeout=20)
        smtp.starttls()
    try:
        smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], msg.as_string())
    finally:
        smtp.quit()
    print('MAIL_SENT', to_addr, subject)
    return 0


if __name__ == '__main__':
    sys.exit(main())