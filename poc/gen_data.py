"""Generate a synthetic incident dataset: many small files, one aggregate question."""
import json, random, pathlib
random.seed(7)
SERVICES = ["checkout", "search", "auth", "inventory", "payments", "notifications"]
CAUSES = ["deploy regression", "db connection pool exhausted", "upstream timeout",
          "cert expiry", "memory leak", "config drift", "rate limit breach"]
out = pathlib.Path("data/incidents"); out.mkdir(parents=True, exist_ok=True)
for p in out.glob("*.json"): p.unlink()
for i in range(1, 41):
    svc = random.choice(SERVICES)
    rec = {
        "incident_id": f"INC-{1000+i}",
        "service": svc,
        "severity": random.choice(["SEV1", "SEV2", "SEV3"]),
        "downtime_minutes": random.randint(2, 180),
        "root_cause": random.choice(CAUSES),
        "detected_by": random.choice(["alerting", "customer report", "synthetic check"]),
        "notes": " ".join(random.choice(
            ["Paged the on-call engineer immediately.","Rollback restored service.",
             "Mitigation applied before customer impact widened.","Postmortem scheduled.",
             "Root cause confirmed via trace sampling.","Runbook was out of date."]) for _ in range(6)),
    }
    (out / f"{rec['incident_id']}.json").write_text(json.dumps(rec, indent=2))
files = sorted(out.glob("*.json"))
print(f"wrote {len(files)} files, {sum(f.stat().st_size for f in files)} bytes total")
# ground truth
tot = {}
for f in files:
    r = json.loads(f.read_text()); tot[r["service"]] = tot.get(r["service"],0) + r["downtime_minutes"]
print("GROUND TRUTH:", json.dumps(dict(sorted(tot.items(), key=lambda kv:-kv[1])), indent=2))
