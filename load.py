"""Run locally on Windows; no pip dependencies. Displays worker distribution."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import statistics
import time
import urllib.request

parser = argparse.ArgumentParser(description="Yuklama generatori")
parser.add_argument("--requests", type=int, default=2000)
parser.add_argument("--workers", type=int, default=20)
parser.add_argument("--delay-ms", type=int, default=150)
parser.add_argument("--url", default=os.environ.get("LAB_URL", "http://127.0.0.1:8080"))
args = parser.parse_args()
url = f"{args.url.rstrip('/')}/api?ms={args.delay_ms}"


def request(_):
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=10) as result:
            payload = json.loads(result.read())
        return (payload.get("instance", "noma'lum"), time.perf_counter() - t0, None)
    except Exception as error:
        return (None, time.perf_counter() - t0, str(error))


print(f"Manzil: {url}; so'rovlar: {args.requests}; parallel ulanishlar: {args.workers}")
t0 = time.perf_counter()
counts, latency, errors = Counter(), [], Counter()
with ThreadPoolExecutor(max_workers=args.workers) as pool:
    for instance, duration, error in pool.map(request, range(args.requests)):
        if error:
            errors[error] += 1
        else:
            counts[instance] += 1
            latency.append(duration)
elapsed = time.perf_counter() - t0
print(f"Jami vaqt: {elapsed:.2f} s; throughput: {args.requests / elapsed:.1f} req/s")
print(f"Muvaffaqiyatli: {sum(counts.values())}; xatolar: {sum(errors.values())}")
print("So'rovlar taqsimoti:")
for host, number in counts.most_common():
    print(f"  {host}: {number}")
if latency:
    values = sorted(latency)
    p95 = values[min(len(values)-1, int(0.95 * len(values)))]
    print(f"O'rtacha kechikish: {statistics.mean(latency)*1000:.1f} ms; P95: {p95*1000:.1f} ms")
for message, count in errors.items():
    print(f"Xato: {message}: {count}")
