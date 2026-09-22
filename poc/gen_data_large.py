"""Same 40 incidents, but each file carries a bulky log tail.

Arm A must pull every byte into the context window to answer. Arm B can filter
inside the sandbox and print only the aggregate. This is the shape where
code-mode orchestration is supposed to pay for itself.
"""
import json, random, pathlib
random.seed(7)
SERVICES = ["checkout","search","auth","inventory","payments","notifications"]
CAUSES = ["deploy regression","db connection pool exhausted","upstream timeout",
          "cert expiry","memory leak","config drift","rate limit breach"]
LOG = ["INFO  health probe ok","WARN  latency p99 exceeded budget","ERROR upstream 503 from dependency",
       "INFO  retry scheduled with backoff","DEBUG connection pool size adjusted",
       "ERROR circuit breaker opened","INFO  circuit breaker half-open","WARN  queue depth rising"]
out = pathlib.Path("data/incidents_large"); out.mkdir(parents=True, exist_ok=True)
for p in out.glob("*.json"): p.unlink()
tot = {}
for i in range(1, 41):
    svc = random.choice(SERVICES); dt = random.randint(2,180)
    tot[svc] = tot.get(svc,0) + dt
    rec = {"incident_id": f"INC-{1000+i}", "service": svc,
           "severity": random.choice(["SEV1","SEV2","SEV3"]),
           "downtime_minutes": dt, "root_cause": random.choice(CAUSES),
           "log_tail": [f"2026-09-{random.randint(1,22):02d}T{random.randint(0,23):02d}:"
                        f"{random.randint(0,59):02d}:{random.randint(0,59):02d}Z "
                        f"{random.choice(LOG)} trace_id={random.getrandbits(64):016x}"
                        for _ in range(60)]}
    (out / f"{rec['incident_id']}.json").write_text(json.dumps(rec, indent=2))
files = sorted(out.glob("*.json"))
size = sum(f.stat().st_size for f in files)
print(f"wrote {len(files)} files, {size:,} bytes (~{size//4:,} tokens if fully read)")
print("GROUND TRUTH:", json.dumps(dict(sorted(tot.items(), key=lambda kv:-kv[1]))))
