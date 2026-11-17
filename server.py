"""呼伦贝尔有奖答题服务：Python 3.11+，SQLite，标准库 HTTP。"""
import os, json, sqlite3, secrets, time, hashlib, hmac, threading, io, re, csv, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from contextlib import contextmanager
from http.cookies import SimpleCookie
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get('DATABASE_PATH', str(ROOT / 'data' / 'quiz.db'))
MODE = os.environ.get('APP_MODE', 'demo')
TZ = timezone(timedelta(hours=8))
LOCK = threading.RLock()

def now(): return time.time()
def test_mark_password(): return os.getenv('TEST_MARK_PASSWORD', 'jevious')
def is_test_user(user): return bool(user and user.get('is_test'))
def iso(t): return datetime.fromtimestamp(t, TZ).isoformat()
def epoch(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def day(t=None): return datetime.fromtimestamp(t if t is not None else now(), TZ).strftime('%Y-%m-%d')
def dumps(x): return json.dumps(x, ensure_ascii=False)
def uid(): return secrets.token_hex(16)
class Error(Exception):
    def __init__(self, message, status=400): self.message, self.status = message, status

def connect():
    c=sqlite3.connect(DB_PATH, timeout=30); c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA busy_timeout=30000'); return c
@contextmanager
def transaction():
    with LOCK:
        c=connect()
        try:
            c.execute('BEGIN IMMEDIATE'); yield c; c.commit()
        except Exception: c.rollback(); raise
        finally: c.close()
def one(c,q,args=()):
    r=c.execute(q,args).fetchone(); return dict(r) if r else None
def allrows(c,q,args=()): return [dict(r) for r in c.execute(q,args)]
def config(c): return json.loads(c.execute('SELECT value FROM settings WHERE key="config"').fetchone()[0])
def saveconfig(c,x): c.execute('UPDATE settings SET value=? WHERE key="config"',(dumps(x),))

INTEGRATION_ENV={
 'wechatAppId':'WECHAT_APP_ID','wechatAppSecret':'WECHAT_APP_SECRET','wechatMchId':'WECHAT_MCH_ID',
 'wechatPayKey':'WECHAT_PAY_KEY','wechatApiV3Key':'WECHAT_API_V3_KEY','wechatCertPath':'WECHAT_CERT_PATH','wechatKeyPath':'WECHAT_KEY_PATH',
 'wechatClientIp':'WECHAT_CLIENT_IP','paymentProvider':'PAYMENT_PROVIDER','wechatSendName':'WECHAT_SEND_NAME',
 'wechatWishing':'WECHAT_WISHING','wechatActName':'WECHAT_ACT_NAME','wechatTransferSceneId':'WECHAT_TRANSFER_SCENE_ID',
 'wechatTransferSceneInfoType':'WECHAT_TRANSFER_SCENE_INFO_TYPE','wechatTransferSceneInfoContent':'WECHAT_TRANSFER_SCENE_INFO_CONTENT',
 'wechatTransferSceneReward':'WECHAT_TRANSFER_SCENE_REWARD','wechatTransferRemark':'WECHAT_TRANSFER_REMARK',
 'wechatUserRecvPerception':'WECHAT_USER_RECV_PERCEPTION','wechatUserRecvStyle':'WECHAT_USER_RECV_STYLE'}
INTEGRATION_DEFAULTS={'wechatAppId':'','wechatAppSecret':'','wechatMchId':'','wechatPayKey':'','wechatApiV3Key':'','wechatCertPath':'','wechatKeyPath':'','wechatClientIp':'','paymentProvider':'demo','wechatSendName':'活动主办方','wechatWishing':'感谢参与平安建设','wechatActName':'扫黑除恶知识答题','wechatTransferSceneId':'1000','wechatTransferSceneInfoType':'活动名称','wechatTransferSceneInfoContent':'呼伦贝尔市深化扫黑除恶专项斗争有奖答题活动','wechatTransferSceneReward':'有奖答题活动奖励','wechatTransferRemark':'有奖答题活动奖励','wechatUserRecvPerception':'活动奖励','wechatUserRecvStyle':'RED_PACKET'}
def integrations(c):
    row=one(c,'SELECT value FROM settings WHERE key="integrations"')
    stored=json.loads(row['value']) if row else {}
    out=dict(INTEGRATION_DEFAULTS)
    for k,env in INTEGRATION_ENV.items():
        if stored.get(k): out[k]=stored[k]
        elif os.getenv(env): out[k]=os.getenv(env)
    return out
def save_integrations(c,x):
    c.execute('INSERT INTO settings(key,value) VALUES("integrations",?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(dumps(x),))
def public_integrations(c):
    i=integrations(c)
    return dict(wechatAppId=i['wechatAppId'],hasWechatAppSecret=bool(i['wechatAppSecret']),wechatMchId=i['wechatMchId'],hasWechatPayKey=bool(i['wechatPayKey']),hasWechatApiV3Key=bool(i['wechatApiV3Key']),wechatCertPath=i['wechatCertPath'],wechatKeyPath=i['wechatKeyPath'],wechatClientIp=i['wechatClientIp'],paymentProvider=i['paymentProvider'],wechatSendName=i['wechatSendName'],wechatWishing=i['wechatWishing'],wechatActName=i['wechatActName'],wechatTransferSceneId=i['wechatTransferSceneId'],wechatTransferSceneInfoType=i['wechatTransferSceneInfoType'],wechatTransferSceneInfoContent=i['wechatTransferSceneInfoContent'],wechatTransferSceneReward=i['wechatTransferSceneReward'],wechatTransferRemark=i['wechatTransferRemark'],wechatUserRecvPerception=i['wechatUserRecvPerception'],wechatUserRecvStyle=i['wechatUserRecvStyle'],callbackUrl=os.getenv('PUBLIC_URL','').rstrip('/')+'/api/auth/callback')
def state(cfg):
    if now()>=epoch(cfg['endAt']): return 'ended'
    if now()<epoch(cfg['startAt']): return 'pending'
    return 'paused' if cfg['paused'] else 'active'

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with transaction() as c:
        c.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,openid TEXT UNIQUE NOT NULL,nickname TEXT,avatar TEXT DEFAULT '',followed INTEGER DEFAULT 0,rules INTEGER DEFAULT 0,created REAL,blocked INTEGER DEFAULT 0,bonus_points INTEGER DEFAULT 0,is_test INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT,admin INTEGER DEFAULT 0,expires REAL);
        CREATE TABLE IF NOT EXISTS questions(id TEXT PRIMARY KEY,type TEXT,stem TEXT UNIQUE,payload TEXT,enabled INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),day TEXT,revived INTEGER,status TEXT,created REAL,deadline REAL,expires REAL,submitted REAL,questions TEXT,answers TEXT DEFAULT '{}',score INTEGER,passed INTEGER,points INTEGER DEFAULT 0,seconds INTEGER DEFAULT 0,ip TEXT,policy TEXT);
        CREATE INDEX IF NOT EXISTS idx_attempt_user ON attempts(user_id,day,status);
        CREATE TABLE IF NOT EXISTS revives(user_id TEXT,day TEXT,attempt_id TEXT,channel TEXT,created REAL,PRIMARY KEY(user_id,day,attempt_id));
        CREATE TABLE IF NOT EXISTS prizes(id TEXT PRIMARY KEY,name TEXT,type TEXT,amountCents INTEGER,stock INTEGER,dailyLimit INTEGER,weight INTEGER,enabled INTEGER,points INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS draws(id TEXT PRIMARY KEY,user_id TEXT,attempt_id TEXT UNIQUE,prize_id TEXT,created REAL,day TEXT,won INTEGER,message TEXT);
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,draw_id TEXT UNIQUE,user_id TEXT,prize_id TEXT,prize_name TEXT,type TEXT,amountCents INTEGER,created REAL,day TEXT,status TEXT,recipient TEXT DEFAULT '{}',tracking TEXT DEFAULT '',failure TEXT DEFAULT '',tries INTEGER DEFAULT 0,provider_id TEXT DEFAULT '',package_info TEXT DEFAULT '',transfer_state TEXT DEFAULT '',source TEXT DEFAULT 'lottery');
        CREATE TABLE IF NOT EXISTS ranking(user_id TEXT PRIMARY KEY,rank INTEGER,nickname TEXT,points INTEGER,totalSeconds INTEGER);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,created REAL,action TEXT,detail TEXT);
        CREATE TABLE IF NOT EXISTS oauth_states(state TEXT PRIMARY KEY,expires REAL);
        ''')
        # 旧库平滑升级：SQLite 增加列；新库 CREATE TABLE 已包含。
        for table,column,ddl in [('users','bonus_points','ALTER TABLE users ADD COLUMN bonus_points INTEGER DEFAULT 0'),('users','is_test','ALTER TABLE users ADD COLUMN is_test INTEGER DEFAULT 0'),('users','avatar',"ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT ''"),('orders','package_info',"ALTER TABLE orders ADD COLUMN package_info TEXT DEFAULT ''"),('orders','transfer_state',"ALTER TABLE orders ADD COLUMN transfer_state TEXT DEFAULT ''"),('prizes','points','ALTER TABLE prizes ADD COLUMN points INTEGER DEFAULT 0')]:
            if column not in {r['name'] for r in c.execute(f'PRAGMA table_info({table})')}: c.execute(ddl)
        if not one(c,'SELECT * FROM settings WHERE key="config"'):
            start=datetime.now(TZ).replace(hour=0,minute=0,second=0,microsecond=0)
            cfg=dict(title='呼伦贝尔市深化扫黑除恶专项斗争有奖答题活动',organizer='中共呼伦贝尔市委政法委员会',startAt=start.isoformat(),endAt=(start+timedelta(days=7)).isoformat(),dailyFree=1,reviveLimit=1,passScore=80,timeLimitSeconds=1200,resumeSeconds=1200,showAnswers=False,leaderboardLimit=100,winnerCount=50,shareMode='manual',shareUrl='',followUrl='',awardDescription='积分前50名话费奖励：第1—10名每人300元，第11—30名每人150元，第31—50名每人100元；活动结束后填写手机号，统一发放。',countFailed=True,countRevived=True,dedupDays=1,shuffleOptions=True,dailyWinLimit=1,totalWinLimit=3,budgetCents=100000,dailyBudgetCents=20000,paused=False,confirmations={f'Q-{i:02}':False for i in range(1,14)},productionConfirmed=False)
            c.execute('INSERT INTO settings VALUES("config",?)',(dumps(cfg),))
        if MODE=='demo' and not one(c,'SELECT id FROM questions LIMIT 1'):
            for typ in ['single','multiple']:
                for i in range(30):
                    q=dict(id=uid(),type=typ,stem=f'【演示题 {i+1}】'+('发现涉黑涉恶违法犯罪线索，应当如何处理？' if typ=='single' else '参与平安建设，以下哪些做法是正确的？'),options=[{'id':'A','text':'依法向有关机关举报'},{'id':'B','text':'保护个人安全并保留线索' if typ=='multiple' else '在网络编造未经核实的信息'},{'id':'C','text':'采取暴力私自报复'},{'id':'D','text':'帮助违法人员隐瞒事实'}],answers=['A'] if typ=='single' else ['A','B'],explanation='此题仅用于功能演示，正式题库须由主办方审核并导入。',enabled=True)
                    c.execute('INSERT INTO questions VALUES(?,?,?,?,1)',(q['id'],typ,q['stem'],dumps(q)))
            for p in [('谢谢惠顾','none',0,0,0,55,0),('积分 +10','points',0,1000000,100000,20,10),('积分 +20','points',0,1000000,100000,10,20),('现金红包 0.5 元','cash',50,20000,3000,9,0),('现金红包 1 元','cash',100,9000,1300,5,0),('现金红包 2 元','cash',200,3000,450,1,0)]:
                c.execute('INSERT INTO prizes(id,name,type,amountCents,stock,dailyLimit,weight,enabled,points) VALUES(?,?,?,?,?,?,?,1,?)',(uid(),*p))

def audit(c,action,detail): c.execute('INSERT INTO audit(created,action,detail) VALUES(?,?,?)',(now(),action,dumps(detail)))
def ranking_rows(c):
    rows=allrows(c,'''WITH submitted AS (
        SELECT * FROM attempts WHERE status='submitted' AND (passed=1 OR points>0)
    ), best AS (
        SELECT p.*, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY points DESC, seconds ASC, submitted ASC) rn
        FROM submitted p
    ), agg AS (
        SELECT user_id, MIN(submitted) firstPass, MAX(submitted) lastAnswer FROM submitted GROUP BY user_id
    )
    SELECT u.id user_id,u.nickname,COALESCE(u.bonus_points,0)+b.points points,b.seconds totalSeconds,a.firstPass,a.lastAnswer
    FROM users u JOIN best b ON b.user_id=u.id AND b.rn=1 JOIN agg a ON a.user_id=u.id
    ORDER BY points DESC,totalSeconds ASC,COALESCE(a.firstPass,1e30) ASC,a.lastAnswer ASC,u.id ASC''')
    previous=None; rank=0
    for i,r in enumerate(rows):
        key=(r['points'],r['totalSeconds'],r['firstPass'],r['lastAnswer'])
        if key!=previous: rank=i+1
        previous=key; r['rank']=rank; n=r['nickname'] or '参与者'; r['nickname']=n[0]+'***'+(n[-1] if len(n)>1 else '')
    return rows

def freeze(c,cfg,force=False):
    if (not force and state(cfg)!='ended') or one(c,'SELECT key FROM settings WHERE key="frozen"'): return
    for r in ranking_rows(c):
        c.execute('INSERT INTO ranking VALUES(?,?,?,?,?)',(r['user_id'],r['rank'],r['nickname'],r['points'],r['totalSeconds']))
        if r['rank']<=cfg['winnerCount']:
            amount=300 if r['rank']<=10 else 150 if r['rank']<=30 else 100
            c.execute('INSERT INTO orders(id,user_id,prize_name,type,amountCents,created,day,status,source) VALUES(?,?,?,?,?,?,?,?,?)',(uid(),r['user_id'],f'话费奖励 {amount} 元','phone',0,now(),day(),'pending','ranking'))
    c.execute('INSERT INTO settings VALUES("frozen",?)',(iso(now()),)); audit(c,'freeze',{})

def account(c,user,cfg):
    if is_test_user(user):
        points=c.execute("SELECT COALESCE(MAX(points),0)+COALESCE((SELECT bonus_points FROM users WHERE id=?),0) FROM attempts WHERE user_id=? AND status='submitted'",(user['id'],user['id'])).fetchone()[0]
        return dict(freeRemaining=999,reviveRemaining=999,canRevive=True,points=points)
    records=allrows(c,"SELECT * FROM attempts WHERE user_id=? AND day=? AND status='submitted'",(user['id'],day()))
    grants=c.execute('SELECT COUNT(*) FROM revives WHERE user_id=? AND day=?',(user['id'],day())).fetchone()[0]
    points=c.execute("SELECT COALESCE(MAX(points),0)+COALESCE((SELECT bonus_points FROM users WHERE id=?),0) FROM attempts WHERE user_id=? AND status='submitted'",(user['id'],user['id'])).fetchone()[0]
    return dict(freeRemaining=max(0,cfg['dailyFree']-sum(not r['revived'] for r in records)),reviveRemaining=max(0,grants-sum(bool(r['revived']) for r in records)),canRevive=grants<cfg['reviveLimit'] and any(not r['passed'] for r in records),points=points)

def draw_info(c,a):
    d=one(c,'SELECT * FROM draws WHERE attempt_id=?',(a['id'],))
    if not d: return None
    p=one(c,'SELECT * FROM prizes WHERE id=?',(d['prize_id'],))
    return dict(won=bool(d['won']),message=d['message'],prize=p['name'] if d['won'] and p else None)

def public_attempt(a,cfg,draw=None):
    q=json.loads(a['questions']); result=dict(id=a['id'],questions=[{k:v for k,v in x.items() if k in ('id','type','stem','options')} for x in q],answers=json.loads(a['answers']),deadlineAt=iso(min(a['deadline'],a['expires'])),status=a['status'],score=a['score'],passed=bool(a['passed']),revived=bool(a['revived']),drawn=bool(draw),lottery=draw)
    if a['status']=='submitted' and cfg['showAnswers']: result['analysis']=q
    return result

def validate_answers(a,answers):
    if not isinstance(answers,dict): raise Error('答案格式错误')
    qs={q['id']:q for q in json.loads(a['questions'])}
    for key,values in answers.items():
        if key not in qs or not isinstance(values,list) or len(values)!=len(set(values)) or any(v not in [o['id'] for o in qs[key]['options']] for v in values): raise Error('答案包含无效选项')
        if qs[key]['type']=='single' and len(values)>1: raise Error('单选题只能选一项')
    return answers

def submit(c,a,cfg,answers=None,force=False):
    if a['status']=='submitted': return a
    if a['status']!='active': raise Error('本套题已失效')
    if not force and (now()>=a['expires'] or a['day']!=day() or state(cfg)=='ended'):
        c.execute("UPDATE attempts SET status='expired' WHERE id=?",(a['id'],)); raise Error('本套题已超时作废，机会未扣除')
    if state(cfg)!='active': raise Error('活动尚未开放或已暂停')
    selected=json.loads(a['answers']) if answers is None or now()>a['deadline'] else validate_answers(a,answers)
    policy=json.loads(a['policy']); qs=json.loads(a['questions'])
    score=sum((8 if q['type']=='single' else 12) for q in qs if set(selected.get(q['id'],[]))==set(q['answers']))
    if is_test_user(one(c,'SELECT * FROM users WHERE id=?',(a['user_id'],))):
        score=100
    passed=score>=policy['passScore']; points=score if (passed or policy.get('countFailed')) and (not a['revived'] or policy['countRevived']) else 0
    c.execute("UPDATE attempts SET status='submitted',answers=?,submitted=?,score=?,passed=?,points=?,seconds=? WHERE id=?",(dumps(selected),min(now(),a['deadline']),score,int(passed),points,max(0,int(min(now(),a['deadline'])-a['created'])),a['id']))
    return one(c,'SELECT * FROM attempts WHERE id=?',(a['id'],))

def maintain(c,cfg):
    if state(cfg)=='active':
        for a in allrows(c,"SELECT * FROM attempts WHERE status='active' AND deadline<=?",(now(),)): submit(c,a,cfg,force=True)
    c.execute("UPDATE attempts SET status='expired' WHERE status='active' AND (expires<=? OR day!=?)",(now(),day()))
    if state(cfg)=='ended': c.execute("UPDATE attempts SET status='expired' WHERE status='active'")
    freeze(c,cfg)

def validate_question(q):
    if q.get('type') not in ['single','multiple'] or not str(q.get('stem','')).strip(): raise Error('题型或题干无效')
    opts=q.get('options',[]); answers=q.get('answers',[])
    if not isinstance(opts,list) or any(not isinstance(o,dict) for o in opts): raise Error('选项格式错误')
    if not isinstance(answers,list) or any(not isinstance(a,str) for a in answers): raise Error('正确答案格式错误')
    if len(opts) not in ([4] if q['type']=='single' else [4,5]): raise Error('单选须4项，多选须4至5项')
    ids=[o.get('id') for o in opts]
    if len(set(ids))!=len(ids) or any(not isinstance(x,str) or not x for x in ids) or any(not str(o.get('text','')).strip() for o in opts): raise Error('选项为空或标识重复')
    if not isinstance(answers,list) or len(set(answers))!=len(answers) or any(x not in ids for x in answers) or (len(answers)!=1 if q['type']=='single' else len(answers)<2): raise Error('正确答案不完整')
    return dict(id=q.get('id') or uid(),type=q['type'],stem=q['stem'].strip(),options=opts,answers=answers,explanation=str(q.get('explanation','')),enabled=bool(q.get('enabled',True)))

def readiness(c,cfg):
    checks=[]
    i=integrations(c)
    checks.append(dict(name='公众号 AppID',ok=bool(i['wechatAppId']),detail='后台微信配置或 WECHAT_APP_ID'))
    checks.append(dict(name='公众号 AppSecret',ok=bool(i['wechatAppSecret']),detail='后台微信配置或 WECHAT_APP_SECRET'))
    checks.append(dict(name='公网地址',ok=bool(os.getenv('PUBLIC_URL')),detail='环境变量 PUBLIC_URL'))
    checks.append(dict(name='管理员密码',ok=bool(os.getenv('ADMIN_PASSWORD')),detail='环境变量 ADMIN_PASSWORD'))
    if i['paymentProvider'] in ['wechat_redpack','wechat_transfer']:
        for name,key in [('微信商户号','wechatMchId'),('商户证书','wechatCertPath'),('商户私钥','wechatKeyPath'),('服务器出口IP','wechatClientIp')]:
            checks.append(dict(name=name,ok=bool(i[key]),detail='后台微信配置或环境变量'))
        if i['paymentProvider']=='wechat_transfer':
            checks.append(dict(name='APIv3密钥',ok=bool(i['wechatApiV3Key']),detail='后台微信配置或环境变量'))
            checks.append(dict(name='转账场景ID',ok=bool(i['wechatTransferSceneId']),detail='商家转账产品场景，现金营销为1000'))
        else:
            checks.append(dict(name='微信支付密钥',ok=bool(i['wechatPayKey']),detail='后台微信配置或环境变量'))
    else:
        for name,env in [('支付网关','PAYMENT_GATEWAY_URL'),('支付网关密钥','PAYMENT_GATEWAY_SECRET')]:
            checks.append(dict(name=name,ok=bool(os.getenv(env)),detail=f'环境变量 {env}'))
    demo=c.execute("SELECT COUNT(*) FROM questions WHERE stem LIKE '【演示题%' AND enabled=1").fetchone()[0]
    counts={r['type']:r['n'] for r in allrows(c,'SELECT type,COUNT(*) n FROM questions WHERE enabled=1 GROUP BY type')}
    checks.extend([dict(name='正式题库',ok=not demo and counts.get('single',0)>=5 and counts.get('multiple',0)>=5,detail='移除演示题并导入审核通过的题库'),dict(name='活动预算',ok=cfg['budgetCents']>0 and cfg['dailyBudgetCents']>0,detail='以分为单位')])
    return dict(ready=all(x['ok'] for x in checks),checks=checks)

def remote_json(url,data=None,headers=None):
    req=urllib.request.Request(url,data=None if data is None else dumps(data).encode(),headers=headers or {})
    with urllib.request.urlopen(req,timeout=15) as r: return json.load(r)
WX_CACHE={}
def wx_token(c):
    i=integrations(c)
    if not i['wechatAppId'] or not i['wechatAppSecret']: raise Error('公众号 AppID/AppSecret 未配置',503)
    if WX_CACHE.get('appid')!=i['wechatAppId']: WX_CACHE.clear(); WX_CACHE['appid']=i['wechatAppId']
    if WX_CACHE.get('expires',0)>now(): return WX_CACHE['token']
    q=urllib.parse.urlencode(dict(grant_type='client_credential',appid=i['wechatAppId'],secret=i['wechatAppSecret']))
    x=remote_json('https://api.weixin.qq.com/cgi-bin/token?'+q)
    if 'access_token' not in x: raise Error('公众号凭据不可用',503)
    WX_CACHE.update(token=x['access_token'],expires=now()+x.get('expires_in',7200)-300); return x['access_token']
def wx_follow(c,openid):
    x=remote_json('https://api.weixin.qq.com/cgi-bin/user/info?'+urllib.parse.urlencode(dict(access_token=wx_token(c),openid=openid,lang='zh_CN')))
    if 'subscribe' not in x: raise Error('暂时无法验证关注状态',503)
    return bool(x['subscribe'])

def pay_order(order_id):
    # 网关必须按订单号幂等，超时后使用相同订单号重试，绝不更换商户单号。
    with transaction() as c:
        o=one(c,'SELECT * FROM orders WHERE id=?',(order_id,))
        if not o or o['type']!='cash' or o['status'] not in ['pending','retrying']: return
        i=integrations(c)
        if MODE=='demo' or i['paymentProvider']=='demo': c.execute("UPDATE orders SET status='demo_paid',provider_id=? WHERE id=?",('DEMO-'+order_id,order_id)); return
        c.execute("UPDATE orders SET status='processing',tries=tries+1 WHERE id=?",(order_id,))
        user=one(c,'SELECT * FROM users WHERE id=?',(o['user_id'],))
    try:
        if i['paymentProvider']=='wechat_transfer':
            from wechat_transfer import create_transfer
            response=create_transfer(o,user,i)
            state=str(response.get('state') or '')
            with transaction() as c:
                if state=='WAIT_USER_CONFIRM':
                    c.execute("UPDATE orders SET status='wait_confirm',provider_id=?,package_info=?,transfer_state=?,failure='' WHERE id=?",(response.get('out_bill_no') or o['id'],response.get('package_info') or '',state,order_id))
                elif state=='SUCCESS':
                    c.execute("UPDATE orders SET status='paid',provider_id=?,package_info='',transfer_state=?,failure='' WHERE id=?",(response.get('out_bill_no') or o['id'],state,order_id))
                else:
                    c.execute("UPDATE orders SET status='held',provider_id=?,package_info='',transfer_state=?,failure=? WHERE id=?",(response.get('out_bill_no') or o['id'],state,str(response.get('fail_reason') or response.get('message') or '转账未完成')[:200],order_id))
            return
        if i['paymentProvider']=='wechat_redpack':
            from wechat_pay import transfer
            response=transfer(o,user,i)
            with transaction() as c:
                c.execute('UPDATE orders SET status=?,provider_id=?,failure=\'\' WHERE id=?',('paid' if response['status']=='paid' else 'sent',response['transactionId'],order_id))
            return
        url=os.environ['PAYMENT_GATEWAY_URL']; secret=os.environ['PAYMENT_GATEWAY_SECRET']
        if not url.startswith('https://'): raise ValueError('支付网关必须使用HTTPS')
        payload=dict(orderId=o['id'],openid=user['openid'],amountCents=o['amountCents'],description=o['prize_name'])
        body=dumps(payload).encode(); stamp=str(int(now())); signature=hmac.new(secret.encode(),stamp.encode()+b'.'+body,hashlib.sha256).hexdigest()
        req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json','X-Timestamp':stamp,'X-Signature':signature,'Idempotency-Key':o['id']})
        with urllib.request.urlopen(req,timeout=15) as r: response=json.load(r)
        if response.get('status')!='paid' or not response.get('transactionId'): raise ValueError('网关尚未确认到账')
        with transaction() as c: c.execute("UPDATE orders SET status='paid',provider_id=?,failure='' WHERE id=?",(response['transactionId'],order_id))
    except Exception as e:
        with transaction() as c:
            current=one(c,'SELECT tries FROM orders WHERE id=?',(order_id,))
            c.execute('UPDATE orders SET status=?,failure=? WHERE id=?',('held' if current['tries']>=4 else 'retrying',str(e)[:200],order_id))

def reconcile_sent():
    with transaction() as c:
        i=integrations(c)
        if i['paymentProvider']!='wechat_redpack': return
        orders=allrows(c,"SELECT id,created FROM orders WHERE type='cash' AND status='sent' LIMIT 100")
    from wechat_pay import request_xml, billno
    for order in orders:
        try:
            result=request_xml('/mmpaymkttransfers/gethbinfo',dict(mch_id=i['wechatMchId'],mch_billno=billno(order['id'],order['created'],i['wechatMchId']),appid=i['wechatAppId'],bill_type='MCHT'),i)
            status=result.get('status')
            if result.get('result_code')=='SUCCESS' and status in ['RECEIVED','REFUND','FAILED']:
                with transaction() as c:
                    c.execute('UPDATE orders SET status=?,failure=? WHERE id=? AND status=\'sent\'',('paid' if status=='RECEIVED' else 'payment_returned','' if status=='RECEIVED' else '微信红包已退回或失败，请商户平台核实',order['id']))
        except Exception: pass

def worker():
    last_reconcile=0
    while True:
        try:
            with transaction() as c:
                maintain(c,config(c)); pending=allrows(c,"SELECT id FROM orders WHERE type='cash' AND status IN ('pending','retrying') LIMIT 20")
            for o in pending: pay_order(o['id'])
            if now()-last_reconcile>=60:
                reconcile_sent(); last_reconcile=now()
        except Exception as e: print('worker:',type(e).__name__,flush=True)
        threading.Event().wait(2)

def is_wechat_request(headers):
    return 'MicroMessenger' in headers.get('User-Agent','')

def wechat_only_page():
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>请在微信中打开</title><style>
    *{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:#eef4fc;color:#17395f;font-family:-apple-system,BlinkMacSystemFont,"Microsoft YaHei",sans-serif;padding:24px}
    .card{width:min(420px,100%);background:#fff;border:1px solid #d8e5f3;border-radius:16px;padding:28px 24px;text-align:center;box-shadow:0 16px 40px #1b3b6014}
    .eyebrow{font-size:12px;color:#5f8bc4;letter-spacing:2px;margin-bottom:8px}h1{font-size:24px;margin:0 0 10px}p{font-size:14px;line-height:1.8;color:#5a7390;margin:0 0 18px}
    img{width:190px;height:190px;object-fit:contain;border:1px solid #d8e5f3;border-radius:12px;padding:6px;background:#fff}
    .small{font-size:12px;color:#7b91a8;margin-top:14px}</style></head><body><div class="card"><div class="eyebrow">呼伦贝尔市 · 有奖答题</div><h1>请在微信中打开</h1><p>本活动仅支持微信内参与。<br>请使用微信扫描下方二维码，关注公众号后从菜单进入。</p><img src="/static/follow-qr.jpg" alt="呼伦贝尔政法公众号二维码"><p class="small">长按识别二维码关注“呼伦贝尔政法”</p></div></body></html>"""

class Handler(BaseHTTPRequestHandler):
    server_version='Quiz/1.0'
    def log_message(self,fmt,*args):
        # 不记录 OAuth code、个人信息或会话凭据。
        print(self.command,urllib.parse.urlsplit(self.path).path,args[1] if len(args)>1 else '',flush=True)
    def respond(self,data,status=200,ctype='application/json; charset=utf-8',headers=None):
        body=dumps(data).encode() if ctype.startswith('application/json') else (data.encode() if isinstance(data,str) else data)
        self.send_response(status)
        self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(body))); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Referrer-Policy','same-origin'); self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' https://res.wx.qq.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://thirdwx.qlogo.cn; connect-src 'self'; frame-ancestors 'none'")
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(body)
    def session(self,c):
        cookie=SimpleCookie()
        try: cookie.load(self.headers.get('Cookie',''))
        except Exception: return None
        token=cookie.get('quiz_session')
        return one(c,'SELECT * FROM sessions WHERE token=? AND expires>?',(token.value,now())) if token else None
    def login(self,c,user_id=None,admin=False):
        token=secrets.token_urlsafe(32); c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(token,user_id,int(admin),now()+86400))
        self.cookie='quiz_session='+token+'; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400'+('; Secure' if MODE=='production' else '')
    def user(self,c):
        s=self.session(c); u=one(c,'SELECT * FROM users WHERE id=?',(s['user_id'],)) if s and s['user_id'] else None
        if not u: raise Error('请先登录',401)
        if u['blocked']: raise Error('账户已停用',403)
        return u
    def admin(self,c):
        s=self.session(c)
        if not s or not s['admin']: raise Error('请先登录管理后台',401)
    def follow_ok(self,c,u):
        # 测试账号只用于验收；真实微信用户每次都实时核对，不能只信登录时的缓存。
        if is_test_user(u): return True
        openid=str(u.get('openid',''))
        if openid.startswith('demo-'):
            # 演示登录只能在非微信环境使用，微信内必须走真实关注校验。
            return bool(u['followed']) and not is_wechat_request(self.headers)
        followed=wx_follow(c,openid)
        if bool(followed)!=bool(u['followed']):
            c.execute('UPDATE users SET followed=? WHERE id=?',(int(followed),u['id']))
            u['followed']=int(followed)
        return bool(followed)

    def require_active(self,c,cfg,u):
        if state(cfg)!='active': raise Error('活动未开始、已结束或已暂停')
        if MODE=='production' and not readiness(c,cfg)['ready']: raise Error('活动正式配置尚未完成',503)
        if not self.follow_ok(c,u): raise Error('请先关注公众号',403)
        if not u['rules']: raise Error('请先阅读并确认活动规则')
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n>5*1024*1024: raise Error('上传文件不能超过5MB',413)
        raw=self.rfile.read(n)
        if 'multipart/form-data' in self.headers.get('Content-Type',''): return raw
        try: return json.loads(raw) if raw else {}
        except Exception: raise Error('JSON格式错误')
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def do_PUT(self): self.handle_request()
    def handle_request(self):
        self.cookie=None
        try:
            parsed=urllib.parse.urlsplit(self.path); path=parsed.path; query=urllib.parse.parse_qs(parsed.query)
            if not path.startswith('/api/'):
                if self.command!='GET': raise Error('不支持的方法',405)
                if path in ['/','/admin','/admin/'] and path=='/' and not is_wechat_request(self.headers):
                    return self.respond(wechat_only_page(),ctype='text/html; charset=utf-8')
                if path in ['/','/admin','/admin/']:
                    target=ROOT/'static'/'index.html'
                else:
                    target=ROOT/'static'/(path.removeprefix('/static/').lstrip('/'))
                if not target.resolve().is_relative_to((ROOT/'static').resolve()) or not target.is_file(): raise Error('页面不存在',404)
                import mimetypes
                return self.respond(target.read_bytes(),ctype=(mimetypes.guess_type(str(target))[0] or 'application/octet-stream')+('; charset=utf-8' if target.suffix in ['.js','.css','.html'] else ''))
            if self.command in ['POST','PUT']:
                origin=self.headers.get('Origin')
                expected=os.getenv('PUBLIC_URL','').rstrip('/') or 'http://'+self.headers.get('Host','')
                if origin and origin!=expected: raise Error('请求来源不匹配',403)
                if self.headers.get('Sec-Fetch-Site')=='cross-site': raise Error('拒绝跨站请求',403)
            data=self.body() if self.command in ['POST','PUT'] else {}
            with transaction() as c:
                cfg=config(c); maintain(c,cfg)
                result=self.route(c,cfg,path,query,data)
            if isinstance(result,tuple): return self.respond(*result)
            self.respond(result,headers={'Set-Cookie':self.cookie} if self.cookie else None)
        except Error as e: self.respond({'error':e.message},e.status)
        except sqlite3.IntegrityError: self.respond({'error':'记录重复或数据关联无效'},409)
        except (ValueError,TypeError,KeyError) as e: self.respond({'error':'输入格式不正确：'+str(e)[:100]},400)
        except Exception as e:
            print('request error:',repr(e),flush=True); self.respond({'error':'服务暂时不可用，请稍后重试'},500)

    def route(self,c,cfg,path,query,data):
        method=self.command
        if path=='/api/health': return {'ok':True,'mode':MODE}
        if path=='/api/auth/demo' and method=='POST':
            if MODE!='demo': raise Error('演示登录已关闭',404)
            name=str(data.get('nickname','体验用户')).strip()[:24] or '体验用户'
            # 浏览器会话以随机 openid 标识，昵称绝不作为可冒用的身份凭据。
            u={'id':uid(),'openid':'demo-'+uid()}
            is_test=0
            c.execute('INSERT INTO users(id,openid,nickname,followed,created,is_test) VALUES(?,?,?,1,?,?)',(u['id'],u['openid'],name,now(),is_test)); self.login(c,u['id']); return {'ok':True}
        if path=='/api/auth/wechat':
            i=integrations(c)
            if not i['wechatAppId'] or not os.getenv('PUBLIC_URL'): raise Error('请先配置微信公众号',503)
            nonce=uid(); c.execute('INSERT INTO oauth_states VALUES(?,?)',(nonce,now()+600))
            callback=os.environ['PUBLIC_URL'].rstrip('/')+'/api/auth/callback'
            url='https://open.weixin.qq.com/connect/oauth2/authorize?'+urllib.parse.urlencode(dict(appid=i['wechatAppId'],redirect_uri=callback,response_type='code',scope='snsapi_userinfo',state=nonce))+'#wechat_redirect'
            return ('',302,'text/plain',{'Location':url,'Set-Cookie':'oauth_state='+nonce+'; HttpOnly; SameSite=Lax; Path=/; Max-Age=600'+('; Secure' if MODE=='production' else '')})
        if path=='/api/auth/callback':
            nonce=query.get('state',[''])[0]; ck=SimpleCookie(); ck.load(self.headers.get('Cookie',''))
            if not ck.get('oauth_state') or not hmac.compare_digest(ck['oauth_state'].value,nonce) or not one(c,'SELECT * FROM oauth_states WHERE state=? AND expires>?',(nonce,now())): raise Error('授权状态已失效',403)
            c.execute('DELETE FROM oauth_states WHERE state=?',(nonce,))
            i=integrations(c)
            x=remote_json('https://api.weixin.qq.com/sns/oauth2/access_token?'+urllib.parse.urlencode(dict(appid=i['wechatAppId'],secret=i['wechatAppSecret'],code=query.get('code',[''])[0],grant_type='authorization_code')))
            if not x.get('openid'): raise Error('微信授权失败，请重试',401)
            profile={}
            if 'snsapi_userinfo' in str(x.get('scope','')):
                try:
                    profile=remote_json('https://api.weixin.qq.com/sns/userinfo?'+urllib.parse.urlencode(dict(access_token=x.get('access_token',''),openid=x['openid'],lang='zh_CN')))
                except Exception: profile={}
            if not isinstance(profile,dict): profile={}
            followed=wx_follow(c,x['openid']); u=one(c,'SELECT * FROM users WHERE openid=?',(x['openid'],))
            nickname=str(profile.get('nickname') or '').strip()[:24]
            avatar=str(profile.get('headimgurl') or '').replace('http://','https://').strip()[:500]
            if not u:
                u={'id':uid()}; c.execute('INSERT INTO users(id,openid,nickname,avatar,followed,created) VALUES(?,?,?,?,?,?)',(u['id'],x['openid'],nickname or '参与者',avatar,int(followed),now()))
            else:
                c.execute('UPDATE users SET nickname=?,avatar=?,followed=? WHERE id=?',(nickname or u.get('nickname') or '参与者',avatar or u.get('avatar') or '',int(followed),u['id']))
            self.login(c,u['id']); return ('',302,'text/plain',{'Location':'/','Set-Cookie':self.cookie})
        if path=='/api/admin/login' and method=='POST':
            key=self.client_address[0]; bucket=LOGIN_LIMIT.setdefault(key,[]); bucket[:]=[t for t in bucket if now()-t<300]
            if len(bucket)>=10: raise Error('尝试过多，请5分钟后重试',429)
            bucket.append(now()); expected=os.getenv('ADMIN_PASSWORD','demo-admin-2026' if MODE=='demo' else '')
            if not expected or not hmac.compare_digest(str(data.get('username','')),'admin') or not hmac.compare_digest(str(data.get('password','')),expected): raise Error('账号或密码错误',401)
            bucket.clear(); self.login(c,admin=True); return {'ok':True}
        if path=='/api/logout' and method=='POST':
            s=self.session(c)
            if s: c.execute('DELETE FROM sessions WHERE token=?',(s['token'],))
            self.cookie='quiz_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0'; return {'ok':True}
        if path.startswith('/api/admin/'):
            self.admin(c); return self.admin_route(c,cfg,path,query,data)
        if path=='/api/bootstrap':
            s=self.session(c); u=one(c,'SELECT * FROM users WHERE id=?',(s['user_id'],)) if s else None
            a=one(c,"SELECT * FROM attempts WHERE user_id=? AND status='active' ORDER BY created DESC LIMIT 1",(u['id'],)) if u else None
            last=one(c,"SELECT * FROM attempts WHERE user_id=? AND status='submitted' ORDER BY submitted DESC LIMIT 1",(u['id'],)) if u else None
            return dict(mode=MODE,user={k:u[k] for k in ['id','nickname','avatar','followed','rules','is_test']} if u else None,config=cfg,state=state(cfg),account=account(c,u,cfg) if u else None,activeAttempt=public_attempt(a,cfg,draw_info(c,a)) if a else None,latestResult=public_attempt(last,cfg,draw_info(c,last)) if last else None,prizes=allrows(c,'SELECT id,name,type,amountCents,points FROM prizes WHERE enabled=1'),orders=self.orders(c,u['id']) if u else [],rankingFrozen=bool(one(c,'SELECT key FROM settings WHERE key="frozen"')),serverTime=iso(now()))
        if path=='/api/leaderboard':
            frozen=bool(one(c,'SELECT key FROM settings WHERE key="frozen"')); rows=allrows(c,'SELECT * FROM ranking ORDER BY rank,user_id') if frozen else ranking_rows(c)
            s=self.session(c); me=next((r for r in rows if s and r['user_id']==s['user_id']),None)
            def safe(r): return {k:r[k] for k in ['rank','nickname','points','totalSeconds']}
            visible=[r for r in rows if r['rank']<=cfg['winnerCount']] if query.get('winners',[''])[0]=='1' else rows[:cfg['leaderboardLimit']]
            return dict(rows=[safe(r) for r in visible],me=safe(me) if me else None,frozen=frozen)
        u=self.user(c)
        if path=='/api/rules/accept' and method=='POST': c.execute('UPDATE users SET rules=1 WHERE id=?',(u['id'],)); return {'ok':True}
        if path=='/api/demo/follow' and method=='POST':
            if MODE!='demo': raise Error('演示接口关闭',404)
            c.execute('UPDATE users SET followed=1 WHERE id=?',(u['id'],)); return {'ok':True}
        if path=='/api/follow/refresh' and method=='POST':
            followed=wx_follow(c,u['openid']); c.execute('UPDATE users SET followed=? WHERE id=?',(int(followed),u['id'])); return {'followed':followed}
        if path=='/api/test/freeze' and method=='POST':
            if not is_test_user(u): raise Error('仅测试账号可用',403)
            freeze(c,cfg,force=True); return {'ok':True,'frozen':True}
        if path=='/api/test/unfreeze' and method=='POST':
            if not is_test_user(u): raise Error('仅测试账号可用',403)
            c.execute('DELETE FROM settings WHERE key="frozen"')
            c.execute('DELETE FROM ranking')
            c.execute("DELETE FROM orders WHERE source='ranking'")
            audit(c,'test.unfreeze',{'user':u['id']}); return {'ok':True,'frozen':False}
        if path=='/api/attempts/start' and method=='POST':
            self.require_active(c,cfg,u)
            existing=one(c,"SELECT * FROM attempts WHERE user_id=? AND status='active'",(u['id'],))
            if existing: return public_attempt(existing,cfg,draw_info(c,existing))
            ac=account(c,u,cfg); revived=ac['freeRemaining']<=0
            if revived and ac['reviveRemaining']<=0: raise Error('今日答题机会已用完')
            used=set() if is_test_user(u) else set()
            if not is_test_user(u):
              for r in allrows(c,'SELECT questions FROM attempts WHERE user_id=? AND created>?',(u['id'],now()-cfg['dedupDays']*86400)):
                used.update(q['id'] for q in json.loads(r['questions']))
            qs=[]
            for typ in ['single','multiple']:
                pool=[json.loads(r['payload']) for r in allrows(c,'SELECT * FROM questions WHERE type=? AND enabled=1',(typ,)) if r['id'] not in used]
                if len(pool)<5: raise Error('去重窗口内可用题目不足，请联系主办方补充题库')
                qs.extend(secrets.SystemRandom().sample(pool,5))
            if cfg['shuffleOptions']:
                for q in qs: secrets.SystemRandom().shuffle(q['options'])
            stamp=now(); aid=uid(); deadline=min(stamp+(cfg['timeLimitSeconds'] or cfg['resumeSeconds']),epoch(cfg['endAt']))
            c.execute('INSERT INTO attempts(id,user_id,day,revived,status,created,deadline,expires,questions,ip,policy) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(aid,u['id'],day(),int(revived),'active',stamp,deadline,deadline,dumps(qs),self.client_address[0],dumps(cfg)))
            return public_attempt(one(c,'SELECT * FROM attempts WHERE id=?',(aid,)),cfg)
        m=re.fullmatch(r'/api/attempts/([a-f0-9]+)(/answers|/submit)?',path)
        if m:
            a=one(c,'SELECT * FROM attempts WHERE id=? AND user_id=?',(m[1],u['id']))
            if not a: raise Error('答题记录不存在',404)
            if a['status']=='active' and method in ['GET','PUT']:
                self.require_active(c,cfg,u)
            if m[2]=='/answers' and method=='PUT':
                if a['status']!='active' or now()>a['deadline']: raise Error('本套题已结束')
                answers=validate_answers(a,data.get('answers',{})); c.execute('UPDATE attempts SET answers=? WHERE id=?',(dumps(answers),a['id'])); a['answers']=dumps(answers)
            elif m[2]=='/submit' and method=='POST': a=submit(c,a,cfg,data.get('answers',{}))
            elif method!='GET': raise Error('不支持的方法',405)
            return public_attempt(a,cfg,draw_info(c,a))
        if path=='/api/revive' and method=='POST':
            self.require_active(c,cfg,u)
            a=one(c,"SELECT * FROM attempts WHERE id=? AND user_id=? AND status='submitted' AND day=? AND passed=0",(data.get('attemptId'),u['id'],day()))
            if not a: raise Error('仅当日未达标答题可解锁复活')
            existing=one(c,'SELECT * FROM revives WHERE user_id=? AND day=? AND attempt_id=?',(u['id'],day(),a['id']))
            if existing: return {'ok':True,'account':account(c,u,cfg)}
            if not account(c,u,cfg)['canRevive']: raise Error('今日复活次数已用完')
            if cfg['shareMode']=='disabled': raise Error('复活入口暂未开启')
            c.execute('INSERT INTO revives VALUES(?,?,?,?,?)',(u['id'],day(),a['id'],str(data.get('channel','manual'))[:30],now())); return {'ok':True,'account':account(c,u,cfg)}
        if path=='/api/lottery' and method=='POST': return self.lottery(c,cfg,u,data)
        m=re.fullmatch(r'/api/orders/([a-f0-9]+)/transfer/sync',path)
        if m and method=='POST':
            o=one(c,'SELECT * FROM orders WHERE id=? AND user_id=?',(m[1],u['id']))
            if not o or o['type']!='cash': raise Error('订单不存在',404)
            i=integrations(c)
            if i['paymentProvider']!='wechat_transfer': raise Error('当前不是商家转账模式')
            if o['status'] not in ['wait_confirm','pending','retrying','sent']: raise Error('当前订单无需同步')
            from wechat_transfer import query_transfer
            r=query_transfer(o.get('provider_id') or o['id'],i)
            tx_state=str(r.get('state') or '')
            status='paid' if tx_state=='SUCCESS' else 'held' if tx_state in ['FAIL','CANCELLED','CANCELING'] else 'wait_confirm'
            c.execute('UPDATE orders SET status=?,package_info=?,transfer_state=?,failure=? WHERE id=?',(status,(r.get('package_info') or '') if status=='wait_confirm' else '',tx_state,str(r.get('fail_reason') or '')[:200],o['id']))
            rows=self.orders(c,u['id'])
            return next((x for x in rows if x['id']==o['id']),{'ok':True})
        if path=='/api/orders': return {'orders':self.orders(c,u['id'])}
        m=re.fullmatch(r'/api/orders/([a-f0-9]+)/claim',path)
        if m and method=='PUT':
            o=one(c,'SELECT * FROM orders WHERE id=? AND user_id=?',(m[1],u['id']))
            if not o or o['type'] not in ['physical','souvenir','phone']: raise Error('无可登记的领奖信息',404)
            if o['status'] not in ['pending','ready','returned']: raise Error('奖品已发放，不能修改领奖信息')
            if any(not isinstance(data.get(k,''),str) for k in ['name','phone','address','pickup']): raise Error('领奖信息须为文本')
            phone=str(data.get('phone','')).strip()
            if not re.fullmatch(r'1[3-9]\d{9}',phone): raise Error('请填写有效的11位手机号')
            if o['type']=='phone':
                recipient={'phone':phone}
                c.execute("UPDATE orders SET recipient=?,status='ready' WHERE id=?",(dumps(recipient),o['id'])); return {'ok':True}
            recipient={k:str(data.get(k,'')).strip() for k in ['name','phone','address','pickup']}
            if not recipient['name'] or not (recipient['address'] or recipient['pickup']): raise Error('请填写姓名、有效手机号及地址或领取点')
            if any(len(v)>300 for v in recipient.values()): raise Error('收货信息过长')
            c.execute('UPDATE orders SET recipient=? WHERE id=?',(dumps(recipient),o['id'])); return {'ok':True}
        if path=='/api/share/config':
            url=query.get('url',[''])[0].split('#')[0]
            if not url.startswith(os.getenv('PUBLIC_URL','https://invalid')+'/'): raise Error('分享地址无效')
            ticket=remote_json('https://api.weixin.qq.com/cgi-bin/ticket/getticket?'+urllib.parse.urlencode(dict(access_token=wx_token(c),type='jsapi'))).get('ticket')
            if not ticket: raise Error('获取微信分享配置失败',503)
            nonce=uid(); stamp=int(now()); signature=hashlib.sha1(f'jsapi_ticket={ticket}&noncestr={nonce}&timestamp={stamp}&url={url}'.encode()).hexdigest()
            return dict(appId=integrations(c)['wechatAppId'],timestamp=stamp,nonceStr=nonce,signature=signature,imgUrl=os.getenv('PUBLIC_URL','').rstrip('/')+'/static/share-cover-v2.jpg')
        raise Error('接口不存在',404)

    def orders(self,c,user_id):
        rows=allrows(c,'SELECT * FROM orders WHERE user_id=? ORDER BY created DESC',(user_id,))
        i=integrations(c)
        for r in rows:
            r['recipient']=json.loads(r['recipient'])
            if r.get('type')=='cash':
                r['mchId']=i['wechatMchId']; r['appId']=i['wechatAppId']; r['packageInfo']=r.get('package_info') or ''
        return rows
    def lottery(self,c,cfg,u,data):
        a=one(c,'SELECT * FROM attempts WHERE id=? AND user_id=?',(data.get('attemptId'),u['id']))
        if not a or a['status']!='submitted' or not a['passed']: raise Error('本套成绩未达到抽奖条件')
        existing=one(c,'SELECT * FROM draws WHERE attempt_id=?',(a['id'],))
        if existing:
            o=one(c,'SELECT * FROM orders WHERE draw_id=?',(existing['id'],)); p=one(c,'SELECT * FROM prizes WHERE id=?',(existing['prize_id'],))
            if o and p and p['type']=='points': o['points']=int(p.get('points') or 0)
            return dict(won=bool(existing['won']),message=existing['message'],order=o,prize=p if existing['won'] else None)
        self.require_active(c,cfg,u)
        wins=allrows(c,"SELECT day FROM orders WHERE user_id=? AND source='lottery'",(u['id'],))
        if not is_test_user(u) and (len(wins)>=cfg['totalWinLimit'] or sum(x['day']==day() for x in wins)>=cfg['dailyWinLimit']): raise Error('已达到个人中奖上限')
        spent=c.execute("SELECT COALESCE(SUM(amountCents),0) FROM orders WHERE source='lottery'").fetchone()[0]
        daily=c.execute("SELECT COALESCE(SUM(amountCents),0) FROM orders WHERE source='lottery' AND day=?",(day(),)).fetchone()[0]
        pool=allrows(c,'SELECT * FROM prizes WHERE enabled=1 AND weight>0'); available=[]
        for p in pool:
            if p['type']=='none': continue
            total=c.execute('SELECT COUNT(*) FROM orders WHERE prize_id=?',(p['id'],)).fetchone()[0]
            today=c.execute('SELECT COUNT(*) FROM orders WHERE prize_id=? AND day=?',(p['id'],day())).fetchone()[0]
            if total<p['stock'] and today<p['dailyLimit'] and spent+p['amountCents']<=cfg['budgetCents'] and daily+p['amountCents']<=cfg['dailyBudgetCents']: available.append(p['id'])
        if not available: raise Error('今日奖品已抽完，抽奖机会保留')
        roll=secrets.randbelow(sum(p['weight'] for p in pool)); chosen=pool[-1]
        for p in pool:
            roll-=p['weight']
            if roll<0: chosen=p; break
        won=chosen['id'] in available; message='恭喜中奖，请在我的奖品中查看发放状态' if won else '本次未中奖，感谢参与'
        draw=uid(); c.execute('INSERT INTO draws VALUES(?,?,?,?,?,?,?,?)',(draw,u['id'],a['id'],chosen['id'],now(),day(),int(won),message)); order=None
        if won:
            status='pending'; prize_points=0
            if chosen['type']=='points':
                prize_points=int(chosen.get('points') or 0); status='granted'
                c.execute('UPDATE users SET bonus_points=COALESCE(bonus_points,0)+? WHERE id=?',(prize_points,u['id']))
                message=f'恭喜获得积分 +{prize_points}，已计入总积分'
                c.execute('UPDATE draws SET message=? WHERE id=?',(message,draw))
            oid=uid(); c.execute('INSERT INTO orders(id,draw_id,user_id,prize_id,prize_name,type,amountCents,created,day,status) VALUES(?,?,?,?,?,?,?,?,?,?)',(oid,draw,u['id'],chosen['id'],chosen['name'],chosen['type'],chosen['amountCents'],now(),day(),status))
            order=one(c,'SELECT * FROM orders WHERE id=?',(oid,)); order['points']=prize_points
        return dict(won=won,message=message,order=order,prize=chosen if won else None)

    def admin_route(self,c,cfg,path,query,data):
        method=self.command
        if path=='/api/admin/users' and method=='GET':
            q=query.get('q',[''])[0].strip()[:60]
            try: page=max(1,int(query.get('page',['1'])[0]))
            except Exception: page=1
            per=20
            where='WHERE (?="" OR u.nickname LIKE ?)' if q else ''
            args=('',f'%{q}%') if q else ()
            total=c.execute(f'SELECT COUNT(*) FROM users u {where}',args).fetchone()[0]
            pages=max(1,(total+per-1)//per); page=min(page,pages)
            rows=allrows(c,f'''SELECT u.id,u.nickname,u.avatar,u.followed,u.is_test,u.blocked,u.created,
                (SELECT COUNT(*) FROM attempts a WHERE a.user_id=u.id AND a.status='submitted') attempts,
                (SELECT COALESCE(MAX(a.points),0) FROM attempts a WHERE a.user_id=u.id AND a.status='submitted') best,
                (SELECT COUNT(*) FROM orders o WHERE o.user_id=u.id) orders
                FROM users u {where} ORDER BY u.created DESC LIMIT ? OFFSET ?''',args+(per,(page-1)*per))
            for r in rows:
                r['createdAt']=iso(r['created']); r.pop('created',None)
                r['avatar']=r['avatar'] or ''
            return dict(rows=rows,total=total,page=page,pages=pages)
        m=re.fullmatch(r'/api/admin/users/([a-f0-9]+)/test',path)
        if m:
            if method!='POST': raise Error('不支持的方法',405)
            target=one(c,'SELECT * FROM users WHERE id=?',(m[1],))
            if not target: raise Error('用户不存在',404)
            if not hmac.compare_digest(str(data.get('password','')),test_mark_password()): raise Error('测试账号密码错误',403)
            enabled=bool(data.get('enabled'))
            c.execute('UPDATE users SET is_test=? WHERE id=?',(int(enabled),target['id']))
            audit(c,'user.test_toggle',{'user':target['id'],'enabled':enabled})
            return {'ok':True,'id':target['id'],'is_test':int(enabled)}
        if path=='/api/admin/dashboard':
            counts={r['type']:r['n'] for r in allrows(c,'SELECT type,COUNT(*) n FROM questions WHERE enabled=1 GROUP BY type')}
            return dict(mode=MODE,stats=dict(users=c.execute('SELECT COUNT(*) FROM users').fetchone()[0],attempts=c.execute("SELECT COUNT(*) FROM attempts WHERE status='submitted'").fetchone()[0],passed=c.execute('SELECT COUNT(*) FROM attempts WHERE passed=1').fetchone()[0],orders=c.execute('SELECT COUNT(*) FROM orders').fetchone()[0],spentCents=c.execute('SELECT COALESCE(SUM(amountCents),0) FROM orders').fetchone()[0]),warnings=[f'{"单选" if t=="single" else "多选"}题可用数量{counts.get(t,0)}，建议补充' for t in ['single','multiple'] if counts.get(t,0)<50],pendingConfirmations=[k for k,v in cfg['confirmations'].items() if not v])
        if path=='/api/admin/readiness': return readiness(c,cfg)
        if path=='/api/admin/integrations':
            if method=='GET': return public_integrations(c)
            if method!='PUT': raise Error('不支持的方法',405)
            allowed=set(INTEGRATION_DEFAULTS)
            unknown=set(data)-allowed
            if unknown: raise Error('未知配置字段：'+','.join(sorted(unknown)))
            current=integrations(c)
            updated={**current}
            for k in allowed:
                if k not in data: continue
                val=data[k]
                if k in ['wechatAppSecret','wechatPayKey','wechatApiV3Key']:
                    if val in ('',None): continue
                if not isinstance(val,str): raise Error(k+'须为文本')
                updated[k]=val.strip()
            if updated['paymentProvider'] not in ['demo','wechat_redpack','wechat_transfer','gateway']: raise Error('支付模式无效')
            if updated['wechatApiV3Key'] and len(updated['wechatApiV3Key'])!=32: raise Error('APIv3 密钥须为32位')
            if not updated['wechatTransferSceneId'].isdigit(): raise Error('转账场景ID须为数字')
            if updated['wechatUserRecvStyle'] not in ['RED_PACKET','CONFIRM_PAGE']: raise Error('收款样式无效')
            for k in ['wechatTransferSceneInfoType','wechatTransferSceneInfoContent','wechatTransferSceneReward','wechatTransferRemark','wechatUserRecvPerception']:
                if len(updated[k])>32: raise Error(k+'过长')
            if updated['wechatAppId'] and not re.fullmatch(r'wx[0-9A-Za-z]{16}',updated['wechatAppId']): raise Error('AppID 格式不正确')
            if updated['wechatMchId'] and not re.fullmatch(r'[0-9]{6,32}',updated['wechatMchId']): raise Error('商户号格式不正确')
            for k in ['wechatCertPath','wechatKeyPath']:
                if updated[k] and not updated[k].startswith('/'): raise Error('证书路径须为服务器绝对路径')
            if any(len(updated[k])>2000 for k in allowed): raise Error('配置内容过长')
            save_integrations(c,updated); audit(c,'integrations.update',[k for k in data if k not in ('wechatAppSecret','wechatPayKey','wechatApiV3Key')])
            return public_integrations(c)
        if path=='/api/admin/integrations/test' and method=='POST':
            token=wx_token(c)
            return {'ok':True,'appId':integrations(c)['wechatAppId'],'tokenReady':bool(token)}
        if path=='/api/admin/config':
            if method=='PUT':
                unknown=set(data)-set(cfg)
                if unknown: raise Error('未知配置字段：'+','.join(unknown))
                updated={**cfg,**data}
                for k in ['dailyFree','reviveLimit','passScore','timeLimitSeconds','resumeSeconds','leaderboardLimit','winnerCount','dedupDays','dailyWinLimit','totalWinLimit','budgetCents','dailyBudgetCents']:
                    if type(updated[k]) is not int or updated[k]<0: raise Error(k+'必须为非负整数')
                if not 1<=updated['passScore']<=100 or updated['resumeSeconds']<60 or updated['dailyFree']<1 or updated['leaderboardLimit']<1: raise Error('配置数值超出范围')
                if epoch(updated['endAt'])<=epoch(updated['startAt']): raise Error('结束时间必须晚于开始时间')
                for k in ['paused','showAnswers','countFailed','countRevived','shuffleOptions','productionConfirmed']:
                    if type(updated[k]) is not bool: raise Error(k+'须为布尔值')
                if updated['shareMode'] not in ['manual','sdk','disabled','free']: raise Error('复活模式无效')
                if set(updated['confirmations'])!={f'Q-{i:02}' for i in range(1,14)} or any(type(v) is not bool for v in updated['confirmations'].values()): raise Error('确认清单不完整')
                for k in ['title','organizer','shareUrl','followUrl','awardDescription']:
                    if not isinstance(updated[k],str) or len(updated[k])>2000: raise Error('文案过长')
                for k in ['shareUrl','followUrl']:
                    if updated[k] and not updated[k].startswith('https://'): raise Error('公众号链接须使用https')
                if one(c,'SELECT key FROM settings WHERE key="frozen"') and any(updated[k]!=cfg[k] for k in ['startAt','endAt','winnerCount','awardDescription','countFailed','countRevived']): raise Error('活动已封榜，不能修改结算参数')
                saveconfig(c,updated); audit(c,'config.update',list(data)); return updated
            return cfg
        if path=='/api/admin/freeze' and method=='POST':
            if state(cfg)!='ended': raise Error('活动结束后才能封榜')
            freeze(c,cfg); return {'ok':True}
        if path=='/api/admin/questions/template':
            wb=Workbook(); ws=wb.active; ws.append(['题型','题干','A','B','C','D','E','答案','解析']); ws.append(['单选','请替换为正式题目','选项A','选项B','选项C','选项D','','A','解析']); ws.append(['多选','请替换为正式多选题','选项A','选项B','选项C','选项D','','AB','解析']); return self.xlsx(wb,'question-template.xlsx')
        if path=='/api/admin/questions/import' and method=='POST':
            from email.parser import BytesParser
            from email.policy import default
            msg=BytesParser(policy=default).parsebytes(('Content-Type: '+self.headers['Content-Type']+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+data)
            parts=[p for p in msg.iter_parts() if p.get_filename()]
            if len(parts)!=1: raise Error('请选择一个Excel文件')
            try: wb=load_workbook(io.BytesIO(parts[0].get_payload(decode=True)),read_only=True,data_only=True)
            except Exception: raise Error('无法读取Excel文件')
            rows=wb.active.iter_rows(values_only=True); next(rows,None); prepared=[]; seen=set()
            for i,row in enumerate(rows,2):
                if i>10002: raise Error('每次最多导入10000题')
                if not any(v is not None for v in row): continue
                vals=list(row)+[None]*9; typ={'单选':'single','多选':'multiple','single':'single','multiple':'multiple'}.get(str(vals[0]))
                try:
                    q=validate_question(dict(type=typ,stem=str(vals[1] or ''),options=[{'id':letter,'text':str(vals[2+j])} for j,letter in enumerate('ABCDE') if vals[2+j] is not None and str(vals[2+j]).strip()],answers=list(re.sub(r'[,，、\s]','',str(vals[7] or '')).upper()),explanation=str(vals[8] or '')))
                    if q['stem'] in seen or one(c,'SELECT id FROM questions WHERE stem=?',(q['stem'],)): raise Error('重复题干')
                    seen.add(q['stem']); prepared.append(q)
                except Error as e: raise Error(f'第{i}行：{e.message}，本次未导入任何题目')
            for q in prepared: c.execute('INSERT INTO questions VALUES(?,?,?,?,?)',(q['id'],q['type'],q['stem'],dumps(q),int(q['enabled'])))
            audit(c,'questions.import',{'count':len(prepared)}); return {'imported':len(prepared)}
        m=re.fullmatch(r'/api/admin/questions(?:/([a-f0-9]+))?',path)
        if m:
            if method=='GET':
                q=query.get('q',[''])[0].strip()[:80]
                try: page=max(1,int(query.get('page',['1'])[0]))
                except Exception: page=1
                per=20
                qs=[json.loads(r['payload']) for r in allrows(c,'SELECT * FROM questions ORDER BY rowid DESC')]
                counts={typ:sum(qq['type']==typ and qq['enabled'] for qq in qs) for typ in ['single','multiple']}
                if q: qs=[qq for qq in qs if q in qq.get('stem','')]
                total=len(qs); pages=max(1,(total+per-1)//per); page=min(page,pages)
                return {'questions':qs[(page-1)*per:page*per],'counts':counts,'total':total,'page':page,'pages':pages}
            q=validate_question({**data,**({'id':m[1]} if m[1] else {})})
            if m[1] and not one(c,'SELECT id FROM questions WHERE id=?',(m[1],)): raise Error('题目不存在',404)
            c.execute('INSERT INTO questions VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET type=excluded.type,stem=excluded.stem,payload=excluded.payload,enabled=excluded.enabled',(q['id'],q['type'],q['stem'],dumps(q),int(q['enabled']))); return q
        m=re.fullmatch(r'/api/admin/prizes(?:/([a-f0-9]+))?',path)
        if m:
            if method=='GET':
                prizes=allrows(c,'SELECT * FROM prizes')
                for p in prizes:
                    p['issued']=c.execute('SELECT COUNT(*) FROM orders WHERE prize_id=?',(p['id'],)).fetchone()[0]
                    p['todayIssued']=c.execute('SELECT COUNT(*) FROM orders WHERE prize_id=? AND day=?',(p['id'],day())).fetchone()[0]
                    p['remaining']=max(0,(p['stock'] or 0)-p['issued'])
                return {'prizes':prizes}
            p={k:data.get(k) for k in ['name','type','amountCents','stock','dailyLimit','weight','enabled','points']}
            if not p['name'] or p['type'] not in ['cash','physical','souvenir','none','points']: raise Error('奖品名称或类型无效')
            p['points']=p['points'] or 0
            if any(type(p[k]) is not int or p[k]<0 for k in ['amountCents','stock','dailyLimit','weight','points']): raise Error('奖品数值须为非负整数')
            if p['type']=='cash' and p['amountCents']<1: raise Error('红包金额必须大于0')
            if p['type']=='points' and p['points']<1: raise Error('积分奖品必须设置积分值')
            if p['type']!='points': p['points']=0
            pid=m[1] or uid()
            if m[1] and not one(c,'SELECT id FROM prizes WHERE id=?',(pid,)): raise Error('奖品不存在',404)
            c.execute('INSERT INTO prizes(id,name,type,amountCents,stock,dailyLimit,weight,enabled,points) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,type=excluded.type,amountCents=excluded.amountCents,stock=excluded.stock,dailyLimit=excluded.dailyLimit,weight=excluded.weight,enabled=excluded.enabled,points=excluded.points',(pid,p['name'],p['type'],p['amountCents'],p['stock'],p['dailyLimit'],p['weight'],int(bool(p['enabled'])),p['points'])); audit(c,'prize.save',{'id':pid}); return {'id':pid,**p}
        if path in ['/api/admin/records','/api/admin/export']:
            kind=query.get('kind',['attempts'])[0]; search=query.get('q',[''])[0]; date=query.get('date',[''])[0]; user_id=query.get('userId',[''])[0]
            if kind not in ['attempts','orders','draws']: raise Error('记录类型无效')
            if kind=='draws':
                rows=allrows(c,'''SELECT d.id,d.created,d.day,d.won,d.message,u.openid,u.nickname,p.name prize_name,p.type prize_type,o.id order_id,o.status order_status
                    FROM draws d JOIN users u ON u.id=d.user_id LEFT JOIN prizes p ON p.id=d.prize_id LEFT JOIN orders o ON o.draw_id=d.id
                    WHERE (?="" OR d.user_id=?) AND (?="" OR d.day=?) ORDER BY d.rowid DESC''',(user_id,user_id,date,date))
                for r in rows: r['createdAt']=iso(r['created'])
                if search: rows=[r for r in rows if any(search in str(r.get(k,'')) for k in ['openid','nickname','id','prize_name','message'])]
            else:
                table='attempts' if kind=='attempts' else 'orders'
                rows=allrows(c,f'SELECT t.*,u.openid,u.nickname FROM {table} t JOIN users u ON u.id=t.user_id WHERE (?="" OR t.user_id=?) AND (?="" OR t.day=?) ORDER BY t.rowid DESC',(user_id,user_id,date,date))
                if search: rows=[r for r in rows if search in r['openid'] or search in r['id'] or search in r.get('recipient','')]
            for r in rows:
                for k in ['questions','answers','policy']: r.pop(k,None)
                if 'recipient' in r:
                    rec=json.loads(r['recipient']); r['recipient']=rec
                    for key,val in rec.items(): r[key]=val
            if path.endswith('export'):
                wb=Workbook(); ws=wb.active; ws.title={'attempts':'答题数据','orders':'中奖发奖数据','draws':'抽奖记录'}[kind]
                keys=list(rows[0]) if rows else (['id','openid','score','passed'] if kind=='attempts' else ['id','prize_name','won','message'] if kind=='draws' else ['id','prize_name','status','name','phone','address'])
                ws.append(keys)
                for r in rows:
                    values=[]
                    for k in keys:
                        v=r.get(k,''); v=dumps(v) if isinstance(v,(dict,list)) else v
                        if isinstance(v,str) and v.startswith(('=','+','-','@')): v="'"+v
                        values.append(v)
                    ws.append(values)
                if kind=='attempts':
                    summary=wb.create_sheet('统计'); summary.append(['参与人数','答题套次','达标套次']); summary.append([len({r['user_id'] for r in rows}),sum(r['status']=='submitted' for r in rows),sum(bool(r['passed']) for r in rows)])
                audit(c,'export',{'kind':kind,'count':len(rows)}); return self.xlsx(wb,kind+'.xlsx')
            return {'rows':rows}
        m=re.fullmatch(r'/api/admin/orders/([a-f0-9]+)(/retry)?',path)
        if m:
            o=one(c,'SELECT * FROM orders WHERE id=?',(m[1],))
            if not o: raise Error('订单不存在',404)
            if m[2]=='/retry' and method=='POST':
                if o['type']!='cash' or o['status']!='held': raise Error('仅挂账红包可补发')
                c.execute("UPDATE orders SET status='retrying',tries=0 WHERE id=?",(o['id'],)); audit(c,'payment.retry',{'id':o['id']}); return {'ok':True}
            if method=='PUT':
                if o['type'] in ['cash','points']: raise Error('红包与积分状态由系统发放结果确定')
                status=data.get('status')
                if o['type']=='phone':
                    if status!='granted': raise Error('话费奖励仅可登记为已发放')
                    if not json.loads(o['recipient']).get('phone'): raise Error('获奖人尚未填写手机号')
                    c.execute("UPDATE orders SET status='granted',tracking=? WHERE id=?",(str(data.get('tracking',''))[:100],o['id'])); audit(c,'order.update',{'id':o['id'],'status':status}); return {'ok':True}
                allowed={'pending':['shipped'],'shipped':['received','returned'],'returned':['pending','shipped'],'received':[]}
                if status not in allowed.get(o['status'],[]): raise Error('不允许的发货状态变更')
                if status=='shipped' and not json.loads(o['recipient']).get('phone'): raise Error('请先登记收货信息')
                c.execute('UPDATE orders SET status=?,tracking=? WHERE id=?',(status,str(data.get('tracking',''))[:100],o['id'])); audit(c,'order.update',{'id':o['id'],'status':status}); return {'ok':True}
        raise Error('管理接口不存在',404)
    def xlsx(self,wb,name):
        buf=io.BytesIO(); wb.save(buf); return (buf.getvalue(),200,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',{'Content-Disposition':f'attachment; filename="{name}"'})

LOGIN_LIMIT={}
def main():
    if MODE not in ['demo','production']: raise SystemExit('APP_MODE must be demo or production')
    if MODE=='production' and (len(os.getenv('ADMIN_PASSWORD',''))<16 or not os.getenv('PUBLIC_URL','').startswith('https://')): raise SystemExit('Production requires ADMIN_PASSWORD >=16 characters and HTTPS PUBLIC_URL')
    init_db()
    with transaction() as c:
        # 进程崩溃时在途支付须先由同一幂等网关核实，不生成新商户订单。
        c.execute("UPDATE orders SET status='retrying' WHERE status='processing'")
    threading.Thread(target=worker,daemon=True).start()
    host=os.getenv('HOST','127.0.0.1'); port=int(os.getenv('PORT','8080'))
    print(f'Quiz running: http://{host}:{port} mode={MODE}',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
if __name__=='__main__': main()
