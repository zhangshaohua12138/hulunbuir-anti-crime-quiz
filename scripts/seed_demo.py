"""Seed clearly-labelled demo data without creating cash orders."""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta

DB = os.environ.get('DATABASE_PATH', '/var/lib/hulunbuir-quiz/quiz.db')
TZ = timezone(timedelta(hours=8))
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
now = time.time()
today = datetime.fromtimestamp(now, TZ).strftime('%Y-%m-%d')
cfg = json.loads(c.execute("SELECT value FROM settings WHERE key='config'").fetchone()[0])


def uid():
    import secrets
    return secrets.token_hex(16)


def clean_seed():
    users = [r['id'] for r in c.execute("SELECT id FROM users WHERE openid LIKE 'demo-seed-%'")]
    for user_id in users:
        c.execute('DELETE FROM orders WHERE user_id=?', (user_id,))
        c.execute('DELETE FROM draws WHERE user_id=?', (user_id,))
        c.execute('DELETE FROM revives WHERE user_id=?', (user_id,))
        c.execute('DELETE FROM attempts WHERE user_id=?', (user_id,))
        c.execute('DELETE FROM users WHERE id=?', (user_id,))
    c.execute("DELETE FROM prizes WHERE name='演示纪念品'")


def build_attempt(user_id, index, score):
    qs = [json.loads(r['payload']) for r in c.execute("SELECT payload FROM questions WHERE enabled=1 ORDER BY rowid LIMIT 10")]
    # pick the first n questions correct; derive score from question types
    answers = {}
    actual = 0
    for pos, q in enumerate(qs):
        correct = q['answers']
        if pos < score:
            answers[q['id']] = correct
            actual += 8 if q['type'] == 'single' else 12
        else:
            wrong = next((o['id'] for o in q['options'] if o['id'] not in correct), 'A')
            answers[q['id']] = [wrong]
    score_value = actual
    aid = uid()
    created = now - (index + 1) * 3600
    c.execute('''INSERT INTO attempts(id,user_id,day,revived,status,created,deadline,expires,submitted,questions,answers,score,passed,points,seconds,ip,policy)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (aid, user_id, today, 0, 'submitted', created, created + 1200, created + 1200, created + 540,
               json.dumps(qs, ensure_ascii=False), json.dumps(answers, ensure_ascii=False),
               score_value, int(score_value >= int(cfg.get('passScore', 80))), score_value, 540, '127.0.0.1',
               json.dumps(cfg, ensure_ascii=False)))
    return aid, score_value


clean_seed()
point_prizes = [r['id'] for r in c.execute("SELECT id FROM prizes WHERE type='points' AND enabled=1 ORDER BY points")]
names = ['演示-平安志愿者', '演示-社区网格员', '演示-政法小课堂', '演示-法治宣传员', '演示-平安家庭', '演示-答题达人',
         '演示-呼伦贝尔市民', '演示-海拉尔居民', '演示-满洲里居民', '演示-牙克石居民', '演示-扎兰屯居民', '演示-额尔古纳居民']
for index, name in enumerate(names):
    user_id = uid()
    openid = 'demo-seed-' + user_id[:12]
    c.execute('INSERT INTO users(id,openid,nickname,followed,rules,created,blocked,bonus_points,is_test,avatar) VALUES(?,?,?,?,?,?,?,?,?,?)',
              (user_id, openid, name, 1, 1, now - index * 600, 0, 0, 0, ''))
    attempt_id, score = build_attempt(user_id, index, max(1, 10 - (index % 6)))
    if score >= int(cfg.get('passScore', 80)) and point_prizes:
        pid = point_prizes[index % len(point_prizes)]
        prize = c.execute('SELECT * FROM prizes WHERE id=?', (pid,)).fetchone()
        did = uid()
        c.execute('INSERT INTO draws VALUES(?,?,?,?,?,?,?,?)', (did, user_id, attempt_id, pid, now - index * 60, today, 1, '恭喜中奖，感谢参与'))
        oid = uid()
        c.execute('INSERT INTO orders(id,draw_id,user_id,prize_id,prize_name,type,amountCents,created,day,status,recipient,tracking,failure,tries,provider_id,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (oid, did, user_id, pid, prize['name'], 'points', 0, now - index * 60, today, 'granted', '{}', '', '', 0, '', 'lottery'))
c.commit()
print('demo users:', c.execute("SELECT COUNT(*) FROM users WHERE openid LIKE 'demo-seed-%'").fetchone()[0])
print('demo attempts:', c.execute("SELECT COUNT(*) FROM attempts a JOIN users u ON u.id=a.user_id WHERE u.openid LIKE 'demo-seed-%'").fetchone()[0])
print('demo orders:', c.execute("SELECT COUNT(*) FROM orders o JOIN users u ON u.id=o.user_id WHERE u.openid LIKE 'demo-seed-%'").fetchone()[0])
c.close()