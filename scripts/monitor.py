"""轻量健康检查：应用、数据库和磁盘。"""
import json
import os
import shutil
import time
import urllib.request
from pathlib import Path

log_path = Path(os.environ.get('MONITOR_LOG', '/var/lib/hulunbuir-quiz/monitor.log'))
url = os.environ.get('MONITOR_URL', 'http://127.0.0.1:8080/api/health')
webhook = os.environ.get('ALERT_WEBHOOK', '').strip()
log_path.parent.mkdir(parents=True, exist_ok=True)

problems = []
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        body = response.read(4096).decode('utf-8', 'ignore')
        payload = json.loads(body)
        if response.status != 200 or not payload.get('ok') or not payload.get('db'):
            problems.append('health failed: ' + body[:160])
except Exception as exc:
    problems.append('health exception: ' + str(exc)[:160])

disk = shutil.disk_usage('/')
disk_pct = disk.used / disk.total * 100
if disk_pct >= 90:
    problems.append(f'disk usage {disk_pct:.1f}%')

line = time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + ('ALERT ' + '; '.join(problems) if problems else 'OK') + f' disk={disk_pct:.1f}%'
with log_path.open('a', encoding='utf-8') as fh:
    fh.write(line + '\n')
print(line)

if problems and webhook:
    try:
        req = urllib.request.Request(
            webhook,
            data=json.dumps({'text': '呼伦贝尔答题系统告警：' + '; '.join(problems)}).encode(),
            headers={'Content-Type': 'application/json'},
        )
        urllib.request.urlopen(req, timeout=5).read(1024)
    except Exception as exc:
        with log_path.open('a', encoding='utf-8') as fh:
            fh.write('webhook failed: ' + str(exc)[:160] + '\n')
if problems:
    raise SystemExit(1)