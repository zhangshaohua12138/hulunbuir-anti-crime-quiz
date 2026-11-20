"""HTTP integration regressions. Run: python -m unittest -v test_server.

Every case owns a temporary SQLite database and loopback server. No worker runs;
all outbound urllib requests are forbidden or replaced with explicit payment mocks.
Deterministic fixtures use SQLite; API tests use real HTTP requests, while payment
worker entry points are called directly with mocked external providers.
"""
import http.client
import io
import json
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import server
from openpyxl import Workbook


class QuietHandler(server.Handler):
    def log_message(self, *args):
        pass


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='quiz-tests-')
        self.addCleanup(self.tmp.cleanup)
        self.clock = 1794362400.0
        self.patches = [
            patch.object(server, 'DB_PATH', str(Path(self.tmp.name) / 'quiz.db')),
            patch.object(server, 'MODE', 'demo'),
            patch.object(server, 'now', side_effect=lambda: self.clock),
            patch.dict(os.environ, {'ADMIN_PASSWORD': 'test-admin-password', 'PUBLIC_URL': ''}),
            patch.object(server, 'remote_json', side_effect=AssertionError('External network forbidden')),
            patch.object(server.urllib.request, 'urlopen', side_effect=AssertionError('External network forbidden')),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)
        server.LOGIN_LIMIT.clear()
        server.init_db()
        self.configure(startAt=server.iso(self.clock-3600), endAt=server.iso(self.clock+86400))
        self.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)

    def configure(self, **values):
        with server.transaction() as c:
            cfg = server.config(c)
            cfg.update(values)
            server.saveconfig(c, cfg)

    def sql(self, query, args=()):
        with server.transaction() as c:
            return [dict(r) for r in c.execute(query, args)]

    def request(self, path, method='GET', data=None, cookie=None, headers=None, raw=None):
        h = dict(headers or {})
        if cookie:
            h['Cookie'] = cookie
        if raw is None and data is not None:
            raw = json.dumps(data).encode()
            h.setdefault('Content-Type', 'application/json')
        con = http.client.HTTPConnection(*self.httpd.server_address, timeout=5)
        try:
            con.request(method, path, body=raw, headers=h)
            response = con.getresponse()
            body = response.read()
            payload = json.loads(body) if 'application/json' in response.getheader('Content-Type', '') else body
            return response.status, payload, dict(response.getheaders())
        finally:
            con.close()

    def ok(self, path, method='GET', data=None, cookie=None, **kwargs):
        status, result, _ = self.request(path, method, data, cookie, **kwargs)
        self.assertEqual(status, 200, (path, result))
        return result

    def login(self, nickname='测试姓名', rules=True):
        status, _, headers = self.request('/api/auth/demo', 'POST', {'nickname': nickname})
        self.assertEqual(status, 200)
        cookie = headers['Set-Cookie'].split(';')[0]
        if rules:
            self.ok('/api/rules/accept', 'POST', {}, cookie)
        return cookie

    def admin(self):
        status, _, headers = self.request('/api/admin/login', 'POST', {'username':'admin','password':'test-admin-password'})
        self.assertEqual(status, 200)
        return headers['Set-Cookie'].split(';')[0]

    def start(self, cookie):
        return self.ok('/api/attempts/start', 'POST', {}, cookie)

    def answers(self, attempt, single=5, multiple=5):
        row = self.sql('SELECT questions FROM attempts WHERE id=?', (attempt['id'],))[0]
        questions = json.loads(row['questions'])
        remaining = {'single':single, 'multiple':multiple}
        result = {}
        for q in questions:
            if remaining[q['type']] > 0:
                result[q['id']] = list(reversed(q['answers']))
                remaining[q['type']] -= 1
        return result

    def submit(self, cookie, attempt, answers=None):
        return self.ok('/api/attempts/'+attempt['id']+'/submit', 'POST', {'answers': answers if answers is not None else self.answers(attempt)}, cookie)

    def prize(self, stock=10, daily=10, amount=100):
        self.sql('DELETE FROM prizes')
        pid = server.uid()
        self.sql('INSERT INTO prizes(id,name,type,amountCents,stock,dailyLimit,weight,enabled,points) VALUES(?,?,?,?,?,?,?,1,0)', (pid,'确定实物','physical',amount,stock,daily,1))
        return pid

    def test_login_cookie_logout_and_expired_session(self):
        status, _, headers = self.request('/api/auth/demo', 'POST', {'nickname':'同名'})
        self.assertEqual(status, 200)
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Lax', headers['Set-Cookie'])
        cookie = headers['Set-Cookie'].split(';')[0]
        other = self.login('同名')
        self.assertNotEqual(self.ok('/api/bootstrap', cookie=cookie)['user']['id'], self.ok('/api/bootstrap', cookie=other)['user']['id'])
        self.ok('/api/logout', 'POST', {}, cookie)
        self.assertEqual(self.request('/api/attempts/start', 'POST', {}, cookie)[0], 401)
        self.sql('UPDATE sessions SET expires=?', (self.clock-1,))
        self.assertEqual(self.request('/api/attempts/start', 'POST', {}, other)[0], 401)

    def test_wechat_oauth_state_binding_replay_and_unique_openid(self):
        with patch.dict(os.environ, {'WECHAT_APP_ID':'test-app', 'WECHAT_APP_SECRET':'test-secret', 'PUBLIC_URL':'https://quiz.example'}), patch.object(server, 'remote_json', return_value={'openid':'fixed-openid'}) as remote, patch.object(server, 'wx_follow', return_value=True):
            def authorize():
                status,_,headers=self.request('/api/auth/wechat')
                self.assertEqual(status,302)
                state=server.urllib.parse.parse_qs(server.urllib.parse.urlsplit(headers['Location']).query)['state'][0]
                cookie=headers['Set-Cookie'].split(';')[0]
                return state,cookie
            state,cookie=authorize()
            callback='/api/auth/callback?state='+state+'&code=fake-code'
            self.assertEqual(self.request(callback)[0],403)
            self.assertEqual(self.request('/api/auth/callback?state=wrong&code=fake',cookie=cookie)[0],403)
            remote.assert_not_called()
            status,_,headers=self.request(callback,cookie=cookie)
            self.assertEqual(status,302)
            first=self.ok('/api/bootstrap',cookie=headers['Set-Cookie'].split(';')[0])['user']['id']
            self.assertEqual(self.request(callback,cookie=cookie)[0],403)
            self.assertEqual(remote.call_count,1)
            state,cookie=authorize()
            status,_,headers=self.request('/api/auth/callback?state='+state+'&code=second',cookie=cookie)
            self.assertEqual(status,302)
            second=self.ok('/api/bootstrap',cookie=headers['Set-Cookie'].split(';')[0])['user']['id']
            self.assertEqual(first,second)
            self.assertEqual(len(self.sql('SELECT * FROM users')),1)
            state,cookie=authorize()
            self.clock+=601
            self.assertEqual(self.request('/api/auth/callback?state='+state+'&code=expired',cookie=cookie)[0],403)
            self.assertEqual(remote.call_count,2)

    def test_daily_best_includes_failed_and_revived_scores(self):
        self.configure(countFailed=False,countRevived=False)
        user=self.login(); first=self.start(user)
        self.configure(countFailed=True)
        self.submit(user,first,self.answers(first,5,3))
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],76)
        self.ok('/api/revive','POST',{'attemptId':first['id']},user)
        second=self.start(user)
        self.submit(user,second)
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],100)
        self.assertEqual(self.sql('SELECT score FROM attempts ORDER BY created')[1]['score'],100)

    def test_daily_scores_are_summed_across_days(self):
        user=self.login()
        first=self.start(user)
        self.submit(user,first,self.answers(first,5,3))
        self.sql("UPDATE attempts SET day=date(?, '-1 day') WHERE id=?",(server.day(),first['id']))
        second=self.start(user)
        self.submit(user,second)
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],176)
        board=self.ok('/api/leaderboard',cookie=user)
        self.assertEqual(board['rows'][0]['points'],176)
        user_id=self.ok('/api/bootstrap',cookie=user)['user']['id']
        self.assertEqual(board['rows'][0]['totalSeconds'],sum(r['seconds'] for r in self.sql('SELECT seconds FROM attempts WHERE user_id=?',(user_id,))))

    def test_question_shortage_does_not_create_attempt(self):
        user=self.login()
        self.sql("UPDATE questions SET enabled=0 WHERE type='multiple'")
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],400)
        self.assertEqual(self.sql('SELECT * FROM attempts'),[])
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['freeRemaining'],1)

    def test_admin_marks_test_account_with_password(self):
        user=self.login('测试候选人')
        boot=self.ok('/api/bootstrap',cookie=user)
        uid=boot['user']['id']
        admin=self.admin()
        self.assertEqual(self.request('/api/admin/users/'+uid+'/test','POST',{'enabled':True,'password':'wrong'},admin)[0],403)
        marked=self.ok('/api/admin/users/'+uid+'/test','POST',{'enabled':True,'password':'jevious'},admin)
        self.assertEqual(marked['is_test'],1)
        boot=self.ok('/api/bootstrap',cookie=user)
        self.assertEqual(boot['user']['is_test'],1)
        self.assertGreaterEqual(boot['account']['freeRemaining'],999)
        for _ in range(2):
            attempt=self.start(user)
            result=self.submit(user,attempt,{})
            self.assertEqual((result['score'],result['passed']),(100,True))
        third=self.start(user)
        self.assertTrue(third['id'])
        self.ok('/api/admin/users/'+uid+'/test','POST',{'enabled':False,'password':'jevious'},admin)
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['user']['is_test'],0)
        normal=self.login('普通用户')
        self.assertEqual(self.ok('/api/bootstrap',cookie=normal)['user']['is_test'],0)

    def test_ranking_ties_use_time_and_allow_shared_rank(self):
        users=[self.login('排名'+str(i)) for i in range(3)]
        for user in users:
            attempt=self.start(user); self.submit(user,attempt)
        ids=[self.ok('/api/bootstrap',cookie=user)['user']['id'] for user in users]
        self.sql('UPDATE attempts SET seconds=20,submitted=?',(self.clock,))
        self.sql('UPDATE attempts SET seconds=10 WHERE user_id IN (?,?)',(ids[1],ids[2]))
        board=self.ok('/api/leaderboard',cookie=users[0])
        self.assertEqual([r['rank'] for r in board['rows']],[1,1,3])
        self.assertEqual(board['me']['rank'],3)
        self.configure(leaderboardLimit=1)
        truncated=self.ok('/api/leaderboard',cookie=users[0])
        self.assertEqual(len(truncated['rows']),1)
        self.assertEqual(truncated['me']['rank'],3)
        self.configure(winnerCount=1)
        winners=self.ok('/api/leaderboard?winners=1',cookie=users[0])
        self.assertEqual([r['rank'] for r in winners['rows']],[1,1])

    def test_admin_auth_and_bruteforce_limit(self):
        for _ in range(10):
            self.assertEqual(self.request('/api/admin/login','POST',{'username':'admin','password':'wrong'})[0],401)
        self.assertEqual(self.request('/api/admin/login','POST',{'username':'admin','password':'test-admin-password'})[0],429)
        self.clock += 301
        self.ok('/api/admin/dashboard', cookie=self.admin())

    def test_unauthenticated_and_unprivileged_admin_access(self):
        user = self.login()
        for cookie in [None, user]:
            for path in ['/api/admin/questions','/api/admin/config','/api/admin/export?kind=orders']:
                with self.subTest(path=path, cookie=bool(cookie)):
                    self.assertEqual(self.request(path,cookie=cookie)[0],401)
        self.assertEqual(self.request('/api/attempts/start','POST',{})[0],401)

    def test_follow_rules_blocked_and_activity_gates(self):
        user = self.login(rules=False)
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],400)
        self.ok('/api/rules/accept','POST',{},user)
        self.sql('UPDATE users SET followed=0')
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],403)
        self.sql('UPDATE users SET followed=1,blocked=1')
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],403)
        self.sql('UPDATE users SET blocked=0')
        self.configure(paused=True)
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],400)
        self.configure(paused=False,startAt=server.iso(self.clock+60))
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],400)

    def test_five_plus_five_no_answer_leak_and_resume(self):
        user = self.login()
        attempt = self.start(user)
        self.assertEqual(len(attempt['questions']),10)
        self.assertEqual(sum(q['type']=='single' for q in attempt['questions']),5)
        self.assertEqual(sum(q['type']=='multiple' for q in attempt['questions']),5)
        self.assertEqual(len({q['id'] for q in attempt['questions']}),10)
        for result in [attempt,self.ok('/api/attempts/'+attempt['id'],cookie=user),self.ok('/api/bootstrap',cookie=user)['activeAttempt']]:
            self.assertNotIn('analysis',result)
            for q in result['questions']:
                self.assertEqual(set(q),{'id','type','stem','options'})
        saved = self.answers(attempt,1,1)
        self.ok('/api/attempts/'+attempt['id']+'/answers','PUT',{'answers':saved},user)
        resumed = self.start(user)
        self.assertEqual(resumed['id'],attempt['id'])
        self.assertEqual(resumed['answers'],saved)
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['freeRemaining'],1)

    def test_scores_76_80_100_and_lottery_qualification(self):
        self.prize()
        for singles,multiples,score in [(5,3,76),(4,4,80),(5,5,100)]:
            with self.subTest(score=score):
                user=self.login(); attempt=self.start(user)
                result=self.submit(user,attempt,self.answers(attempt,singles,multiples))
                self.assertEqual(result['score'],score)
                self.assertEqual(result['passed'],score>=80)
                status,_,_=self.request('/api/lottery','POST',{'attemptId':attempt['id']},user)
                self.assertEqual(status,200 if score>=80 else 400)

    def test_multiple_requires_exact_set(self):
        for wrong in [['A'],['A','B','C'],['C','D'],[]]:
            with self.subTest(wrong=wrong):
                user=self.login(); attempt=self.start(user); answers=self.answers(attempt)
                q=next(q for q in attempt['questions'] if q['type']=='multiple')
                answers[q['id']]=wrong
                self.assertEqual(self.submit(user,attempt,answers)['score'],88)

    def test_invalid_answers_do_not_submit_or_consume_chance(self):
        user=self.login(); attempt=self.start(user)
        single=next(q['id'] for q in attempt['questions'] if q['type']=='single')
        for answers in [{single:['A','A']},{single:['A','B']},{single:['Z']},{'unknown':['A']},[],{single:[['A']]}]:
            with self.subTest(answers=answers):
                self.assertEqual(self.request('/api/attempts/'+attempt['id']+'/submit','POST',{'answers':answers},user)[0],400)
        self.assertEqual(self.sql('SELECT status FROM attempts')[0]['status'],'active')
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['freeRemaining'],1)

    def test_duplicate_submit_concurrent_is_idempotent(self):
        user=self.login(); attempt=self.start(user); answers=self.answers(attempt)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _: self.request('/api/attempts/'+attempt['id']+'/submit','POST',{'answers':answers},user),range(4)))
        self.assertTrue(all(r[0]==200 and r[1]['score']==100 for r in results))
        self.assertEqual(self.submit(user,attempt,{})['score'],100)
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],100)
        self.assertEqual(len(self.sql('SELECT * FROM attempts')),1)
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],400)

    def test_show_answers_disabled(self):
        self.configure(showAnswers=False)
        user=self.login(); attempt=self.start(user)
        result=self.submit(user,attempt)
        self.assertNotIn('analysis',result)
        self.assertNotIn('analysis',self.ok('/api/bootstrap',cookie=user)['latestResult'])

    def test_revive_idempotent_limit_and_question_dedup(self):
        user=self.login(); first=self.start(user); self.clock+=600; self.submit(user,first,{})
        for _ in range(2):
            result=self.ok('/api/revive','POST',{'attemptId':first['id'],'channel':'manual'},user)
            self.assertEqual(result['account']['reviveRemaining'],1)
        second=self.start(user)
        self.assertTrue(second['revived'])
        self.assertAlmostEqual(server.epoch(second['deadlineAt'])-self.clock,1200,delta=2)
        row=self.sql('SELECT deadline,expires FROM attempts WHERE id=?',(second['id'],))[0]
        self.assertEqual(row['expires'],row['deadline'])
        self.assertFalse({q['id'] for q in first['questions']} & {q['id'] for q in second['questions']})
        self.submit(user,second,{})
        self.assertEqual(self.request('/api/revive','POST',{'attemptId':second['id']},user)[0],400)
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],400)
        self.assertEqual(len(self.sql('SELECT * FROM revives')),1)

    def test_passed_attempt_cannot_revive(self):
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        self.assertEqual(self.request('/api/revive','POST',{'attemptId':attempt['id']},user)[0],400)

    def test_expiry_returns_chance_and_midnight_resets(self):
        user=self.login(); attempt=self.start(user)
        self.sql('UPDATE attempts SET expires=? WHERE id=?',(self.clock-1,attempt['id']))
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['freeRemaining'],1)
        self.assertEqual(self.sql('SELECT status FROM attempts')[0]['status'],'expired')
        second=self.start(user); self.submit(user,second,{})
        self.ok('/api/revive','POST',{'attemptId':second['id']},user)
        self.clock+=86400
        self.configure(endAt=server.iso(self.clock+86400))
        self.sql('UPDATE sessions SET expires=?',(self.clock+86400,))
        account=self.ok('/api/bootstrap',cookie=user)['account']
        self.assertEqual((account['freeRemaining'],account['reviveRemaining']),(1,0))

    def test_deadline_autosubmits_saved_answers(self):
        user=self.login(); attempt=self.start(user)
        self.ok('/api/attempts/'+attempt['id']+'/answers','PUT',{'answers':self.answers(attempt,4,4)},user)
        self.clock+=1201
        result=self.ok('/api/attempts/'+attempt['id'],cookie=user)
        self.assertEqual((result['status'],result['score']),('submitted',80))
        self.assertEqual(self.submit(user,attempt,self.answers(attempt))['score'],80)

    def test_check_answer_returns_correct_answer_after_selection(self):
        user=self.login()
        attempt=self.start(user)
        correct=self.answers(attempt)
        qid=attempt['questions'][0]['id']
        qnext=next(q for q in attempt['questions'] if q['id']==qid)
        wrong=next(o['id'] for o in qnext['options'] if o['id'] not in correct[qid])
        checked=self.ok('/api/attempts/'+attempt['id']+'/check','POST',{'questionId':qid,'answers':[wrong]},user)
        self.assertFalse(checked['correct'])
        self.assertEqual(set(checked['correctAnswers']),set(correct[qid]))
        again=self.ok('/api/attempts/'+attempt['id']+'/check','POST',{'questionId':qid,'answers':correct[qid]},user)
        self.assertTrue(again['correct'])

    def test_submitted_attempt_includes_answer_review(self):
        user=self.login()
        attempt=self.start(user)
        self.assertNotIn('review',self.ok('/api/attempts/'+attempt['id'],cookie=user))
        self.submit(user,attempt,self.answers(attempt,4,3))
        detail=self.ok('/api/attempts/'+attempt['id'],cookie=user)
        self.assertEqual(len(detail['review']),10)
        self.assertEqual(sum(1 for q in detail['review'] if q['corrected']),7)
        self.assertTrue(all(q['correct'] for q in detail['review']))

    def test_below_pass_scores_join_ranking(self):
        user=self.login()
        first=self.start(user)
        failed=self.submit(user,first,self.answers(first,5,3))
        self.assertEqual((failed['score'],failed['passed']),(76,False))
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],76)
        board=self.ok('/api/leaderboard',cookie=user)
        self.assertEqual(board['rows'][0]['points'],76)
        self.assertEqual(board['me']['points'],76)
        self.configure(dailyFree=2)
        second=self.start(user)
        passed=self.submit(user,second,self.answers(second))
        self.assertEqual((passed['score'],passed['passed']),(100,True))
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],100)
        board=self.ok('/api/leaderboard',cookie=user)
        self.assertEqual(board['rows'][0]['points'],100)
        self.assertEqual(board['me']['points'],100)

    def test_ranking_uses_best_single_score_not_sum(self):
        self.configure(dailyFree=2)
        user=self.login()
        first=self.start(user)
        self.assertEqual(self.submit(user,first,self.answers(first,3,5))['score'],84)
        second=self.start(user)
        self.assertEqual(self.submit(user,second,self.answers(second))['score'],100)
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],100)
        board=self.ok('/api/leaderboard',cookie=user)
        self.assertEqual(board['rows'][0]['points'],100)

    def test_phone_award_claim_and_admin_grant(self):
        user=self.login('话费用户'); attempt=self.start(user); self.submit(user,attempt)
        admin=self.admin(); self.configure(endAt=server.iso(self.clock-1))
        self.ok('/api/admin/freeze','POST',{},admin)
        order=self.sql("SELECT * FROM orders WHERE source='ranking'")[0]
        self.assertEqual(order['type'],'phone')
        self.assertIn('话费奖励',order['prize_name'])
        self.ok('/api/orders/'+order['id']+'/claim','PUT',{'phone':'13800138000'},user)
        saved=self.sql('SELECT * FROM orders WHERE id=?',(order['id'],))[0]
        self.assertEqual((saved['status'],json.loads(saved['recipient'])['phone']),('ready','13800138000'))
        self.ok('/api/admin/orders/'+order['id'],'PUT',{'status':'granted'},admin)
        self.assertEqual(self.sql('SELECT status FROM orders WHERE id=?',(order['id'],))[0]['status'],'granted')

    def test_phone_award_tiers_follow_rank_bands(self):
        admin=self.admin()
        self.configure(endAt=server.iso(self.clock-1))
        rows=[]
        for rank in [1,10,11,30,31,50,51]:
            user_id=server.uid()
            self.sql('INSERT INTO users(id,openid,nickname,created) VALUES(?,?,?,?)',(user_id,'tier-'+user_id,'tier',self.clock))
            rows.append(dict(user_id=user_id,nickname='tier',points=100-rank,totalSeconds=rank,firstPass=self.clock,lastPass=self.clock,rank=rank))
        with patch.object(server,'ranking_rows',return_value=rows):
            self.ok('/api/admin/freeze','POST',{},admin)
        saved={r['prize_name']:0 for r in self.sql("SELECT * FROM orders WHERE source='ranking'")}
        amounts=[r['prize_name'] for r in self.sql("SELECT * FROM orders WHERE source='ranking' ORDER BY rowid")]
        self.assertEqual(len(amounts),6)
        self.assertEqual(amounts.count('话费奖励 300 元'),2)
        self.assertEqual(amounts.count('话费奖励 150 元'),2)
        self.assertEqual(amounts.count('话费奖励 100 元'),2)

    def test_winning_draw_concurrent_idempotence(self):
        self.prize(stock=1)
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:self.request('/api/lottery','POST',{'attemptId':attempt['id']},user),range(4)))
        self.assertTrue(all(r[0]==200 and r[1]['won'] for r in results))
        self.assertEqual(len({r[1]['order']['id'] for r in results}),1)
        self.assertEqual(len(self.sql('SELECT * FROM draws')),1)
        self.assertEqual(len(self.sql('SELECT * FROM orders')),1)
        self.assertEqual(self.sql('SELECT SUM(amountCents) n FROM orders')[0]['n'],100)
        detail=self.ok('/api/attempts/'+attempt['id'],cookie=user)
        self.assertTrue(detail['drawn'])
        self.assertEqual(detail['lottery']['prize'],'确定实物')

    def test_losing_draw_response_is_idempotent(self):
        self.prize()
        self.sql('INSERT INTO prizes(id,name,type,amountCents,stock,dailyLimit,weight,enabled,points) VALUES(?,?,?,?,?,?,?,1,0)',(server.uid(),'谢谢参与','none',0,0,0,1))
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        with patch.object(server.secrets,'randbelow',return_value=1):
            first=self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)
        second=self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)
        self.assertFalse(first['won'])
        self.assertEqual(first,second)
        self.assertEqual(len(self.sql('SELECT * FROM draws')),1)
        self.assertEqual(len(self.sql('SELECT * FROM orders')),0)

    def test_points_prize_credits_once_and_joins_ranking(self):
        self.sql('DELETE FROM prizes')
        pid=server.uid()
        self.sql('INSERT INTO prizes(id,name,type,amountCents,stock,dailyLimit,weight,enabled,points) VALUES(?,?,?,?,?,?,?,1,?)',(pid,'积分 +10','points',0,1000,1000,1,10))
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        first=self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)
        self.assertTrue(first['won'])
        self.assertEqual(first['prize']['points'],10)
        self.assertEqual(first['order']['type'],'points')
        self.assertEqual(first['order']['status'],'granted')
        bootstrap=self.ok('/api/bootstrap',cookie=user)
        self.assertEqual(bootstrap['account']['points'],110)
        self.assertEqual(len(self.sql('SELECT * FROM orders')),1)
        self.assertEqual(self.sql('SELECT SUM(amountCents) n FROM orders')[0]['n'],0)
        board=self.ok('/api/leaderboard',cookie=user)
        self.assertEqual(board['rows'][0]['points'],110)
        second=self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)
        self.assertEqual(first,second)
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['account']['points'],110)

    def test_stock_daily_cap_and_budgets_preserve_draw(self):
        for constraint in ['stock','daily','total_budget','daily_budget']:
            with self.subTest(constraint=constraint):
                self.sql('DELETE FROM orders'); self.sql('DELETE FROM draws')
                self.configure(budgetCents=10000,dailyBudgetCents=10000,budgetAutoDaily=False)
                self.prize(stock=1 if constraint=='stock' else 10,daily=1 if constraint=='daily' else 10)
                if constraint in ['total_budget','daily_budget']:
                    self.sql("UPDATE prizes SET type='cash'")
                    self.configure(budgetCents=100) if constraint=='total_budget' else self.configure(dailyBudgetCents=100)
                user=self.login(); attempt=self.start(user); self.submit(user,attempt)
                self.assertTrue(self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)['won'])
                other=self.login(); next_attempt=self.start(other); self.submit(other,next_attempt)
                self.assertEqual(self.request('/api/lottery','POST',{'attemptId':next_attempt['id']},other)[0],400)
                self.assertEqual(len(self.sql('SELECT * FROM draws')),1)
                self.assertEqual(self.sql('SELECT SUM(amountCents) n FROM orders')[0]['n'],100)

    def test_budget_exhaustion_falls_back_to_none(self):
        self.sql('DELETE FROM prizes')
        self.sql("INSERT INTO prizes(id,name,type,amountCents,stock,dailyLimit,weight,enabled,points) VALUES(?,?,?,?,?,?,?,1,0)",(server.uid(),'谢谢参与','none',0,0,0,1))
        self.sql("INSERT INTO prizes(id,name,type,amountCents,stock,dailyLimit,weight,enabled,points) VALUES(?,?,?,?,?,?,?,1,0)",(server.uid(),'现金红包','cash',100,100,100,1))
        self.configure(budgetCents=50,dailyBudgetCents=50,budgetAutoDaily=False)
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        result=self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)
        self.assertFalse(result['won'])
        self.assertEqual(self.sql('SELECT COUNT(*) n FROM orders')[0]['n'],0)

    def test_auto_daily_budget_is_total_over_days(self):
        cfg={'startAt':'2026-11-13T00:00:00+08:00','endAt':'2026-11-15T00:00:00+08:00','budgetCents':101,'dailyBudgetCents':999,'budgetAutoDaily':True}
        self.assertEqual(server.effective_daily_budget(cfg),50)
        cfg['budgetAutoDaily']=False
        self.assertEqual(server.effective_daily_budget(cfg),999)

    def test_personal_win_limits(self):
        self.configure(dailyFree=3,dailyWinLimit=1,totalWinLimit=1)
        self.prize()
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)
        second=self.start(user); self.submit(user,second)
        self.assertEqual(self.request('/api/lottery','POST',{'attemptId':second['id']},user)[0],400)
        self.configure(dailyWinLimit=10)
        self.assertEqual(self.request('/api/lottery','POST',{'attemptId':second['id']},user)[0],400)
        self.assertEqual(len(self.sql('SELECT * FROM draws')),1)

    def cash_order(self):
        self.prize()
        self.sql("UPDATE prizes SET type='cash'")
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        return self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)['order']

    def test_demo_payment_never_calls_network(self):
        order=self.cash_order()
        server.pay_order(order['id'])
        result=self.sql('SELECT * FROM orders WHERE id=?',(order['id'],))[0]
        self.assertEqual(result['status'],'demo_paid')
        self.assertEqual(result['provider_id'],'DEMO-'+order['id'])
        self.assertEqual(result['tries'],0)
        server.urllib.request.urlopen.assert_not_called()
        server.pay_order(order['id'])
        self.assertEqual(self.sql('SELECT * FROM orders')[0],result)

    def test_gateway_initial_plus_three_retries_hold_same_order(self):
        order=self.cash_order()
        with patch.object(server,'MODE','production'), patch.dict(os.environ,{'PAYMENT_PROVIDER':'gateway','PAYMENT_GATEWAY_URL':'https://payments.invalid/mock','PAYMENT_GATEWAY_SECRET':'mock-secret'}), patch.object(server.urllib.request,'urlopen',side_effect=TimeoutError('simulated timeout')) as gateway:
            for i in range(4):
                server.pay_order(order['id'])
                result=self.sql('SELECT * FROM orders WHERE id=?',(order['id'],))[0]
                self.assertEqual(result['tries'],i+1)
                self.assertEqual(result['status'],'held' if i==3 else 'retrying')
            server.pay_order(order['id'])
            self.assertEqual(gateway.call_count,4)
            for call in gateway.call_args_list:
                request=call.args[0]
                self.assertEqual(json.loads(request.data)['orderId'],order['id'])
                self.assertEqual(request.get_header('Idempotency-key'),order['id'])
        self.assertEqual(len(self.sql('SELECT * FROM orders')),1)

    def test_gateway_paid_response_prevents_second_payment(self):
        order=self.cash_order()
        with patch.object(server,'MODE','production'), patch.dict(os.environ,{'PAYMENT_PROVIDER':'gateway','PAYMENT_GATEWAY_URL':'https://payments.invalid/mock','PAYMENT_GATEWAY_SECRET':'mock-secret'}), patch.object(server.urllib.request,'urlopen',return_value=io.BytesIO(b'{"status":"paid","transactionId":"provider-123"}')) as gateway:
            server.pay_order(order['id']); server.pay_order(order['id'])
            self.assertEqual(gateway.call_count,1)
        result=self.sql('SELECT * FROM orders')[0]
        self.assertEqual((result['status'],result['provider_id'],result['tries']),('paid','provider-123',1))

    def test_wechat_bill_number_creation_date_and_cross_day_stability(self):
        import wechat_pay
        from datetime import datetime as RealDatetime
        # UTC 16:00 is midnight of the following day in China.
        created=server.epoch('2026-11-10T16:00:00+00:00')
        order={'id':'a'*32,'created':created,'amountCents':100,'prize_name':'测试红包'}
        env={'WECHAT_MCH_ID':'1234567890','WECHAT_APP_ID':'test-app','WECHAT_CLIENT_IP':'127.0.0.1'}
        with patch.dict(os.environ,env):
            number=wechat_pay.billno(order['id'],created)
            self.assertRegex(number,r'^123456789020261111\d{10}$')
            self.assertEqual(len(number),28)
            self.assertNotEqual(number,wechat_pay.billno('b'*32,created))
            with patch.object(wechat_pay,'datetime',wraps=RealDatetime) as date_clock, patch.object(wechat_pay,'request_xml',return_value={'result_code':'SUCCESS','status':'SENT'}) as xml:
                for current in ['2026-11-11T23:59:59+08:00','2026-11-12T00:00:01+08:00']:
                    date_clock.now.return_value=RealDatetime.fromisoformat(current)
                    self.clock=server.epoch(current)
                    result=wechat_pay.transfer(order,{'openid':'mock-openid'})
                    self.assertEqual(result['transactionId'],number)
                    self.assertEqual(xml.call_args.args[1]['mch_billno'],number)
                self.assertEqual(xml.call_count,2)

    def test_wechat_transfer_queries_before_send_and_reuses_bill(self):
        import wechat_pay
        order={'id':server.uid(),'amountCents':100,'prize_name':'测试红包'}
        user={'openid':'mock-openid'}
        env={'WECHAT_MCH_ID':'1234567890','WECHAT_APP_ID':'test-app','WECHAT_CLIENT_IP':'127.0.0.1'}
        with patch.dict(os.environ,env):
            for status,expected in [('RECEIVED','paid'),('SENT','sent'),('SENDING','sent')]:
                with self.subTest(status=status), patch.object(wechat_pay,'request_xml',return_value={'result_code':'SUCCESS','status':status,'detail_id':'existing'}) as xml:
                    self.assertEqual(wechat_pay.transfer(order,user),{'status':expected,'transactionId':'existing'})
                    self.assertEqual(xml.call_count,1)
                    self.assertTrue(xml.call_args.args[0].endswith('/gethbinfo'))
            with patch.object(wechat_pay,'request_xml',side_effect=[{'result_code':'FAIL','err_code':'NOT_FOUND'},{'result_code':'SUCCESS','send_listid':'new-send'}]) as xml:
                self.assertEqual(wechat_pay.transfer(order,user),{'status':'sent','transactionId':'new-send'})
                query,send=xml.call_args_list
                self.assertEqual(query.args[1]['mch_billno'],send.args[1]['mch_billno'])
                self.assertEqual(send.args[1]['total_amount'],100)
                self.assertEqual(send.args[1]['re_openid'],'mock-openid')
                self.assertTrue(send.args[0].endswith('/sendredpack'))
            with patch.object(wechat_pay,'request_xml',return_value={'result_code':'FAIL','err_code':'SYSTEMERROR'}) as xml:
                with self.assertRaises(wechat_pay.PaymentPending): wechat_pay.transfer(order,user)
                self.assertEqual(xml.call_count,1)

    def test_wechat_sent_reconciliation_received_and_returned(self):
        import wechat_pay
        for provider_status,expected in [('RECEIVED','paid'),('REFUND','payment_returned'),('FAILED','payment_returned'),('SENT','sent')]:
            with self.subTest(status=provider_status):
                self.sql('DELETE FROM orders'); self.sql('DELETE FROM draws')
                order=self.cash_order()
                self.sql("UPDATE orders SET status='sent'")
                with patch.dict(os.environ,{'PAYMENT_PROVIDER':'wechat_redpack','WECHAT_MCH_ID':'1234567890','WECHAT_APP_ID':'mock-app'}), patch.object(wechat_pay,'request_xml',return_value={'result_code':'SUCCESS','status':provider_status}) as xml:
                    server.reconcile_sent()
                    self.assertEqual(xml.call_count,1)
                    self.assertEqual(xml.call_args.args[1]['mch_billno'],wechat_pay.billno(order['id'],order['created']))
                    self.assertEqual(self.sql('SELECT status FROM orders')[0]['status'],expected)
                    if expected!='sent':
                        server.reconcile_sent()
                        self.assertEqual(xml.call_count,1)

    def upload(self, cookie, rows):
        wb=Workbook(); ws=wb.active
        ws.append(['题型','题干','A','B','C','D','E','答案','解析'])
        for row in rows: ws.append(row)
        buf=io.BytesIO(); wb.save(buf)
        boundary='TestQuizBoundary'
        raw=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="questions.xlsx"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n'.encode()+buf.getvalue()+f'\r\n--{boundary}--\r\n'.encode())
        return self.request('/api/admin/questions/import','POST',cookie=cookie,raw=raw,headers={'Content-Type':'multipart/form-data; boundary='+boundary})

    def test_import_valid_and_atomic_validation(self):
        admin=self.admin()
        valid=['单选','导入有效题','a','b','c','d',None,'A','解析']
        multi=['多选','导入多选题','a','b','c','d','e','A， B','解析']
        status,result,_=self.upload(admin,[valid,multi])
        self.assertEqual((status,result),(200,{'imported':2}))
        count=len(self.sql('SELECT * FROM questions'))
        invalids=[['单选','缺选项','a','b','c',None,None,'A',''],['多选','单答案','a','b','c','d',None,'A',''],['单选','非法答案','a','b','c','d',None,'Z',''],valid,['单选','重复答案','a','b','c','d',None,'AA','']]
        for i,invalid in enumerate(invalids):
            with self.subTest(invalid=invalid):
                new=valid.copy(); new[1]='必须回滚'+str(i)
                status,body,_=self.upload(admin,[new,invalid])
                self.assertEqual(status,400,body)
                self.assertEqual(len(self.sql('SELECT * FROM questions')),count)
        repeated=valid.copy(); repeated[1]='文件内重复'
        self.assertEqual(self.upload(admin,[repeated,repeated])[0],400)
        self.assertEqual(len(self.sql('SELECT * FROM questions')),count)

    def test_malformed_question_options_are_client_error(self):
        admin=self.admin()
        status,body,_=self.request('/api/admin/questions','POST',{'type':'single','stem':'坏格式','options':['a','b','c','d'],'answers':['A']},admin)
        self.assertEqual(status,400,body)

    def test_wechat_user_must_follow_even_with_cached_flag(self):
        user=self.login('微信关注测试')
        # 直接用数据库把该用户改成真实微信 openid，模拟登录时缓存为已关注
        with server.transaction() as c:
            row=server.one(c,"SELECT * FROM users WHERE nickname='微信关注测试'")
            c.execute("UPDATE users SET openid='wx-real-openid',followed=1 WHERE id=?",(row['id'],))
        with patch.object(server,'wx_follow',return_value=False):
            status,body,_=self.request('/api/attempts/start','POST',{},user)
            self.assertEqual(status,403,body)

    def test_admin_can_unfreeze_and_reset_activity(self):
        user=self.login('重置测试'); attempt=self.start(user); self.submit(user,attempt)
        admin=self.admin()
        self.configure(endAt=server.iso(self.clock-1))
        self.ok('/api/admin/freeze','POST',{},admin)
        self.assertTrue(self.ok('/api/bootstrap',cookie=user)['rankingFrozen'])
        self.ok('/api/admin/unfreeze','POST',{},admin)
        self.assertFalse(self.ok('/api/bootstrap',cookie=user)['rankingFrozen'])
        self.assertEqual(self.sql('SELECT COUNT(*) n FROM ranking')[0]['n'],0)
        self.assertGreaterEqual(self.sql('SELECT COUNT(*) n FROM users')[0]['n'],1)
        self.assertEqual(self.request('/api/admin/reset','POST',{'password':'wrong','confirm':'RESET'},admin)[0],403)
        result=self.ok('/api/admin/reset','POST',{'password':'test-admin-password','confirm':'RESET'},admin)
        self.assertTrue(result['ok'])
        self.assertEqual(self.sql('SELECT COUNT(*) n FROM users')[0]['n'],0)
        self.assertGreater(self.sql('SELECT COUNT(*) n FROM questions')[0]['n'],0)
        self.assertGreater(self.sql('SELECT COUNT(*) n FROM prizes')[0]['n'],0)
        self.assertTrue(self.sql("SELECT value FROM settings WHERE key='config'"))

    def test_layout_endpoint_is_super_only(self):
        admin=self.admin()
        initial=self.ok('/api/admin/layout',cookie=admin)
        self.assertIsInstance(initial.get('layout'),dict)
        layout={'version':1,'blocks':[{'id':'hero','type':'hero','visible':True,'props':{}},{'id':'cta','type':'cta','visible':True,'props':{}}]}
        saved=self.ok('/api/admin/layout','PUT',{'layout':layout},admin)
        self.assertEqual([b['type'] for b in saved['layout']['blocks']],['hero','cta'])
        boot=self.ok('/api/bootstrap')
        self.assertEqual([b['type'] for b in boot['config']['layout']['blocks']],['hero','cta'])
        self.assertEqual(self.request('/api/admin/layout','PUT',{'layout':layout})[0],401)

    def test_custom_component_blocks_roundtrip(self):
        admin=self.admin()
        layout={'version':1,'blocks':[{'id':'hero','type':'hero','visible':True,'props':{}},{'id':'search1','type':'custom-search','visible':True,'props':{'placeholder':'查一查','buttonText':'搜索','action':'#/ranking','background':'#ffffff'}}]}
        saved=self.ok('/api/admin/layout','PUT',{'layout':layout},admin)
        block=saved['layout']['blocks'][1]
        self.assertEqual(block['type'],'custom-search')
        self.assertEqual(block['props']['placeholder'],'查一查')
        self.assertEqual(block['props']['action'],'#/ranking')
        bad=dict(layout); bad['blocks']=[{'id':'x','type':'custom-unknown','visible':True,'props':{}}]
        self.assertEqual(self.request('/api/admin/layout','PUT',{'layout':bad},admin)[0],400)

    def test_carousel_and_banner_blocks(self):
        admin=self.admin()
        layout={'version':1,'blocks':[
            {'id':'hero','type':'hero','visible':True,'props':{}},
            {'id':'carousel','type':'custom-carousel','visible':True,'props':{'slides':[{'src':'/static/theme-previews/template-1.png','link':'#/rules','title':'第一张'}],'height':'260'}},
            {'id':'banner','type':'custom-banner','visible':True,'props':{'image':'/static/theme-previews/template-2.png','title':'标题','subtitle':'副标题','buttonText':'了解','link':'#/rules','overlay':'0.6'}},
        ]}
        saved=self.ok('/api/admin/layout','PUT',{'layout':layout},admin)
        blocks={b['type']:b for b in saved['layout']['blocks']}
        self.assertEqual(blocks['custom-carousel']['props']['slides'][0]['title'],'第一张')
        self.assertEqual(blocks['custom-banner']['props']['title'],'标题')

    def test_layout_templates_crud(self):
        admin=self.admin()
        layout={'version':1,'blocks':[{'id':'hero','type':'hero','visible':True,'props':{}}]}
        created=self.ok('/api/admin/layout/templates','POST',{'name':'我的模板','layout':layout},admin)
        tid=created['template']['id']
        self.assertEqual(len(created['templates']),1)
        listing=self.ok('/api/admin/layout',cookie=admin)
        self.assertEqual(listing['templates'][0]['name'],'我的模板')
        deleted=self.ok('/api/admin/layout/templates/'+tid,'DELETE',{},admin)
        self.assertEqual(deleted['templates'],[])
        self.assertEqual(self.request('/api/admin/layout/templates','POST',{'name':'x','layout':layout})[0],401)

    def test_nickname_special_characters_are_safe(self):
        self.assertEqual(server.clean_text('A😀\x00\ud800<b>',40),'A😀<b>')
        user=self.login('测试😀<b>')
        boot=self.ok('/api/bootstrap',cookie=user)
        self.assertEqual(boot['user']['nickname'],'测试😀<b>')

    def test_super_and_operator_permissions(self):
        admin=self.admin()
        me=self.ok('/api/admin/me',cookie=admin)
        self.assertEqual(me['role'],'super')
        created=self.ok('/api/admin/accounts','POST',{'username':'operator1','password':'operator-pass','role':'operator'},admin)
        self.assertEqual(created['role'],'operator')
        status,_,headers=admin=self.request('/api/admin/login','POST',{'username':'operator1','password':'operator-pass'})
        self.assertEqual(status,200)
        op=headers['Set-Cookie'].split(';')[0]
        self.assertEqual(self.ok('/api/admin/me',cookie=op)['role'],'operator')
        cfg=self.ok('/api/admin/config',cookie=op)
        cfg['themeColor']='#123456'
        self.assertEqual(self.request('/api/admin/config','PUT',cfg,op)[0],403)
        self.assertEqual(self.request('/api/admin/integrations',cookie=op)[0],403)
        self.assertEqual(self.request('/api/admin/accounts',cookie=op)[0],403)

    def test_admin_user_directory_is_read_only(self):
        user=self.login('UserA')
        attempt=self.start(user); self.submit(user,attempt)
        admin=self.admin()
        data=self.ok('/api/admin/users?q=UserA',cookie=admin)
        self.assertEqual(data['total'],1)
        row=data['rows'][0]
        self.assertEqual((row['nickname'],row['attempts'],row['best']),('UserA',1,100))
        self.assertTrue(row['openid'].startswith('demo-'))
        self.assertEqual(self.request('/api/admin/users',cookie=user)[0],401)

    def test_admin_questions_are_paginated(self):
        admin=self.admin()
        first=self.ok('/api/admin/questions',cookie=admin)
        self.assertEqual(first['page'],1)
        self.assertLessEqual(len(first['questions']),20)
        self.assertGreaterEqual(first['total'],1)
        if first['pages']>1:
            second=self.ok('/api/admin/questions?page=2',cookie=admin)
            self.assertEqual(second['page'],2)

    def test_test_account_can_freeze_and_unfreeze_for_acceptance(self):
        user=self.login('封榜测试')
        uid=self.ok('/api/bootstrap',cookie=user)['user']['id']
        admin=self.admin()
        self.ok('/api/admin/users/'+uid+'/test','POST',{'enabled':True,'password':'jevious'},admin)
        attempt=self.start(user); self.submit(user,attempt)
        self.assertEqual(self.request('/api/test/freeze','POST',{},user)[0],200)
        self.assertTrue(self.ok('/api/bootstrap',cookie=user)['rankingFrozen'])
        self.assertEqual(self.ok('/api/leaderboard',cookie=user)['frozen'],True)
        self.assertEqual(self.request('/api/test/unfreeze','POST',{},user)[0],200)
        self.assertFalse(self.ok('/api/bootstrap',cookie=user)['rankingFrozen'])
        self.assertEqual(self.sql("SELECT COUNT(*) n FROM ranking")[0]['n'],0)

    def test_admin_records_filter_by_user(self):
        users=[self.login('UserA'),self.login('UserB')]
        ids=[]
        for user in users:
            attempt=self.start(user); self.submit(user,attempt)
            ids.append(self.ok('/api/bootstrap',cookie=user)['user']['id'])
        admin=self.admin()
        rows=self.ok('/api/admin/records?kind=attempts&userId='+ids[0],cookie=admin)['rows']
        self.assertEqual([r['nickname'] for r in rows],['UserA'])
        self.assertEqual(self.ok('/api/admin/records?kind=attempts&userId='+ids[1],cookie=admin)['rows'][0]['nickname'],'UserB')

    def test_admin_integrations_are_masked_and_persisted(self):
        admin=self.admin()
        initial=self.ok('/api/admin/integrations',cookie=admin)
        self.assertNotIn('wechatAppSecret',initial)
        saved=self.ok('/api/admin/integrations','PUT',{
            'wechatAppId':'wx1234567890abcdef','wechatAppSecret':'secret-value',
            'wechatMchId':'1900000109','wechatPayKey':'pay-key','paymentProvider':'wechat_redpack',
            'wechatCertPath':'/etc/quiz/cert.pem','wechatKeyPath':'/etc/quiz/key.pem','wechatClientIp':'203.0.113.8'},admin)
        self.assertEqual(saved['wechatAppId'],'wx1234567890abcdef')
        self.assertTrue(saved['hasWechatAppSecret']); self.assertTrue(saved['hasWechatPayKey'])
        self.assertNotIn('wechatAppSecret',saved); self.assertNotIn('wechatPayKey',saved)
        kept=self.ok('/api/admin/integrations','PUT',{'wechatAppSecret':'','wechatPayKey':''},admin)
        self.assertTrue(kept['hasWechatAppSecret']); self.assertTrue(kept['hasWechatPayKey'])
        status,body,_=self.request('/api/admin/integrations','PUT',{'wechatAppId':'bad'},admin)
        self.assertEqual(status,400,body)

    def test_admin_prize_toggle_and_delete(self):
        pid=self.prize()
        admin=self.admin()
        payload={'name':'确定实物','type':'physical','amountCents':100,'stock':10,'dailyLimit':10,'weight':1,'enabled':False,'points':0}
        self.ok(f'/api/admin/prizes/{pid}','POST',payload,admin)
        boot=self.ok('/api/bootstrap')
        self.assertNotIn(pid,[p['id'] for p in boot['prizes']])
        self.ok(f'/api/admin/prizes/{pid}','DELETE',{},admin)
        self.assertEqual(self.sql('SELECT COUNT(*) n FROM prizes')[0]['n'],0)

    def test_admin_prize_inventory_and_draw_records(self):
        self.prize(stock=10)
        user=self.login(); attempt=self.start(user); self.submit(user,attempt)
        self.ok('/api/lottery','POST',{'attemptId':attempt['id']},user)
        admin=self.admin()
        prizes=self.ok('/api/admin/prizes',cookie=admin)['prizes']
        prize=next(p for p in prizes if p['name']=='确定实物')
        self.assertEqual((prize['issued'],prize['remaining']),(1,9))
        draws=self.ok('/api/admin/records?kind=draws',cookie=admin)['rows']
        self.assertEqual(len(draws),1)
        self.assertEqual((draws[0]['prize_name'],bool(draws[0]['won'])),('确定实物',True))

    def test_freeze_snapshot_privacy_and_award_idempotence(self):
        user=self.login('真实完整姓名'); attempt=self.start(user); self.submit(user,attempt)
        admin=self.admin()
        self.assertEqual(self.request('/api/admin/freeze','POST',{},admin)[0],400)
        self.configure(endAt=server.iso(self.clock-1))
        board=self.ok('/api/leaderboard',cookie=user)
        self.assertTrue(board['frozen'])
        self.assertEqual(board['rows'][0]['nickname'],'真***名')
        self.assertEqual(set(board['rows'][0]),{'rank','nickname','points','totalSeconds'})
        self.assertEqual(board['me'],board['rows'][0])
        for _ in range(2): self.ok('/api/admin/freeze','POST',{},admin)
        self.assertEqual(len(self.sql("SELECT * FROM orders WHERE source='ranking'")),1)
        self.sql('UPDATE attempts SET points=9999')
        self.sql("UPDATE users SET nickname='改名'")
        self.assertEqual(self.ok('/api/leaderboard',cookie=user),board)
        self.assertEqual(self.request('/api/admin/config','PUT',{'winnerCount':999},admin)[0],400)
        self.assertEqual(self.request('/api/attempts/start','POST',{},user)[0],400)
        public=self.ok('/api/bootstrap')
        self.assertIsNone(public['user']); self.assertEqual(public['orders'],[])
        self.assertNotIn('openid',json.dumps(board))

    def test_other_user_cannot_read_modify_draw_or_claim(self):
        self.prize(); owner=self.login(); other=self.login(); attempt=self.start(owner)
        for suffix,method,data in [('', 'GET',None),('/answers','PUT',{'answers':{}}),('/submit','POST',{'answers':{}})]:
            self.assertEqual(self.request('/api/attempts/'+attempt['id']+suffix,method,data,other)[0],404)
        self.submit(owner,attempt)
        self.assertEqual(self.request('/api/lottery','POST',{'attemptId':attempt['id']},other)[0],400)
        order=self.ok('/api/lottery','POST',{'attemptId':attempt['id']},owner)['order']
        recipient={'name':'收件人','phone':'13800138000','address':'私密地址','pickup':''}
        self.assertEqual(self.request('/api/orders/'+order['id']+'/claim','PUT',recipient,other)[0],404)
        self.ok('/api/orders/'+order['id']+'/claim','PUT',recipient,owner)
        self.assertEqual(self.ok('/api/orders',cookie=other)['orders'],[])
        self.assertNotIn('私密地址',json.dumps(self.ok('/api/bootstrap',cookie=other),ensure_ascii=False))

    def test_csrf_cross_origin_and_fetch_site_rejected_without_mutation(self):
        user=self.login(rules=False)
        for headers in [{'Origin':'https://evil.example'},{'Sec-Fetch-Site':'cross-site'},{'Origin':'null'}]:
            with self.subTest(headers=headers):
                self.assertEqual(self.request('/api/rules/accept','POST',{},user,headers=headers)[0],403)
                self.assertEqual(self.ok('/api/bootstrap',cookie=user)['user']['rules'],0)
        origin='http://%s:%s'%self.httpd.server_address
        self.ok('/api/rules/accept','POST',{},user,headers={'Origin':origin,'Sec-Fetch-Site':'same-origin'})
        self.assertEqual(self.ok('/api/bootstrap',cookie=user)['user']['rules'],1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
