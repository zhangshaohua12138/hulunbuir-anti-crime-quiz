"""19:00 一次性任务：设置活动时间并重置活动数据。"""
import json
import sys

sys.path.insert(0, '/opt/hulunbuir-quiz')
import server

START = '2026-11-23T09:00:00+08:00'
END = '2026-11-29T23:59:00+08:00'

with server.transaction() as c:
    cfg = server.config(c)
    cfg['startAt'] = START
    cfg['endAt'] = END
    cfg['paused'] = False
    server.saveconfig(c, cfg)
    counts = server.reset_activity(c)
    server.audit(c, 'activity.schedule', {'startAt': START, 'endAt': END, 'counts': counts})

print('SCHEDULE_APPLIED', json.dumps({'startAt': START, 'endAt': END, 'counts': counts}, ensure_ascii=False), flush=True)