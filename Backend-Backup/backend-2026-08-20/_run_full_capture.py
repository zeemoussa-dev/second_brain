import sys
sys.path.insert(0, ".")
from app.business.email_classification import classify_recent_emails

results = classify_recent_emails(limit=320)
print(f"PROCESSED={len(results)}")
errors = [r for r in results if "error" in r]
print(f"ERRORS={len(errors)}")
for r in results[-5:]:
    print(r.get("subject"), "->", r.get("customer"), "/", r.get("kind"))
print("DONE")
