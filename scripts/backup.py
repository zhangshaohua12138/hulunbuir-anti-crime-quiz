"""SQLite 在线备份：不锁业务库，保留最近 14 天。"""
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

src = Path(os.environ.get('DATABASE_PATH', '/var/lib/hulunbuir-quiz/quiz.db'))
outdir = Path(os.environ.get('BACKUP_DIR', '/var/backups/hulunbuir-quiz'))
retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '14'))
outdir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
dest = outdir / f'quiz-{stamp}.db'

source = sqlite3.connect(str(src), timeout=30)
target = sqlite3.connect(str(dest))
try:
    source.backup(target)
    check = target.execute('PRAGMA integrity_check').fetchone()[0]
    if check != 'ok':
        raise RuntimeError('backup integrity check failed: ' + str(check))
finally:
    target.close()
    source.close()

os.chmod(dest, 0o600)
cutoff = time.time() - retention_days * 86400
for old in outdir.glob('quiz-*.db'):
    try:
        if old.stat().st_mtime < cutoff:
            old.unlink()
    except OSError:
        pass
print(f'backup ok: {dest} ({dest.stat().st_size} bytes)')