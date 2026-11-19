"""轻量压测：读接口和一次完整答题写链路。仅用于本机 127.0.0.1:8080。"""
import argparse
import http.client
import json
import os
import statistics
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.environ.get('LOAD_BASE', 'http://127.0.0.1:8080')
parsed = urllib.parse.urlparse(BASE)
HOST = parsed.hostname
PORT = parsed.port or 80
ORIGIN = os.environ.get('LOAD_ORIGIN', 'https://demo.jevious.top')


def request(method, path, body=None, cookie=None):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=float(os.getenv('LOAD_TIMEOUT', '15')))
    headers = {'Accept': 'application/json', 'Origin': ORIGIN}
    raw = None
    if body is not None:
        raw = json.dumps(body, ensure_ascii=False).encode()
        headers['Content-Type'] = 'application/json'
    if cookie:
        headers['Cookie'] = cookie
    conn.request(method, path, body=raw, headers=headers)
    response = conn.getresponse()
    data = response.read(1024 * 1024)
    set_cookie = response.getheader('Set-Cookie') or ''
    conn.close()
    parsed_body = json.loads(data.decode('utf-8')) if data else {}
    return response.status, parsed_body, set_cookie.split(';')[0]


def read_one(i):
    start = time.perf_counter()
    path = '/api/health' if i % 2 == 0 else '/api/bootstrap'
    try:
        status, _, _ = request('GET', path)
    except Exception:
        status = 0
    return status, time.perf_counter() - start


def write_one(i):
    start = time.perf_counter()
    nickname = f'load-{i}-{int(time.time() * 1000)}'
    try:
        status, _, cookie = request('POST', '/api/auth/demo', {'nickname': nickname})
    except Exception:
        return 0, time.perf_counter() - start
    if status != 200:
        return status, time.perf_counter() - start
    status, _, _ = request('POST', '/api/rules/accept', {}, cookie)
    if status != 200:
        return status, time.perf_counter() - start
    status, attempt, _ = request('POST', '/api/attempts/start', {}, cookie)
    if status != 200 or not attempt.get('id'):
        return status, time.perf_counter() - start
    status, _, _ = request('POST', f"/api/attempts/{attempt['id']}/submit", {'answers': {}}, cookie)
    return status, time.perf_counter() - start


def run(kind, total, workers):
    fn = write_one if kind == 'write' else read_one
    results = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fn, i) for i in range(total)]
        for future in as_completed(futures):
            results.append(future.result())
    elapsed = time.perf_counter() - started
    latencies = sorted(ms * 1000 for _, ms in results)
    errors = sum(1 for status, _ in results if status != 200)
    def pct(p):
        if not latencies:
            return 0
        return latencies[min(len(latencies) - 1, int(len(latencies) * p))]
    print(json.dumps({
        'kind': kind,
        'total': total,
        'workers': workers,
        'seconds': round(elapsed, 3),
        'rps': round(total / elapsed, 1),
        'errors': errors,
        'p50_ms': round(pct(.50), 1),
        'p95_ms': round(pct(.95), 1),
        'p99_ms': round(pct(.99), 1),
        'max_ms': round(max(latencies), 1),
    }, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kind', choices=['read', 'write'], default='read')
    parser.add_argument('--total', type=int, default=500)
    parser.add_argument('--workers', type=int, default=50)
    args = parser.parse_args()
    run(args.kind, args.total, args.workers)