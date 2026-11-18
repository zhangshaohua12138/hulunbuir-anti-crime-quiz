"""Static admin asset load test against the local app server."""
import http.client
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HOST = '127.0.0.1'
PORT = 8080
INDEX = '/vue/'


def fetch(path):
    conn = http.client.HTTPConnection(HOST, PORT, timeout=15)
    start = time.perf_counter()
    try:
        conn.request('GET', path)
        response = conn.getresponse()
        body = response.read()
        return response.status, len(body), time.perf_counter() - start
    finally:
        conn.close()


def main():
    _, _, _ = fetch(INDEX)
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    conn.request('GET', INDEX)
    html = conn.getresponse().read().decode('utf-8', 'ignore')
    conn.close()
    assets = re.findall(r'/vue/assets/[^"\']+\.(?:js|css)', html)

    def run(path, total, workers):
        results = []
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(fetch, path) for _ in range(total)]
            for future in as_completed(futures):
                results.append(future.result())
        elapsed = time.perf_counter() - started
        latencies = sorted(value[2] * 1000 for value in results)
        return {
            'path': path,
            'total': total,
            'workers': workers,
            'rps': round(total / elapsed, 1),
            'errors': sum(1 for value in results if value[0] != 200),
            'p50_ms': round(latencies[int(len(latencies) * .5)], 1),
            'p95_ms': round(latencies[int(len(latencies) * .95)], 1),
        }

    print(json.dumps(run(INDEX, 500, 50), ensure_ascii=False))
    for asset in assets:
        print(json.dumps(run(asset, 200, 20), ensure_ascii=False))


if __name__ == '__main__':
    main()