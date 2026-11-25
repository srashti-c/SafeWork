import hashlib, sys, time
from pathlib import Path
import httpx

c = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30)
bad = []

def check(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        bad.append(msg)

try:
    c.get("/health")
except httpx.ConnectError:
    sys.exit("Server not running. Start: uvicorn app.main:app --reload")

email, pw = "tester@example.com", "TestPass12345"
c.post("/auth/register", json={"email": email, "full_name": "Test User", "password": pw})
r = c.post("/auth/login", data={"username": email, "password": pw})
check(r.status_code == 200, "login")
if r.status_code != 200:
    sys.exit(r.text)
h = {"Authorization": "Bearer " + r.json()["access_token"]}

r = c.post("/complaints", headers=h, json={"category_id": 1, "privacy_mode": "confidential",
           "title": "Live check", "description": "Created by live_check.py"})
check(r.status_code == 201, "create complaint")
cid = r.json()["id"]

data = ("SafeWork live check " + str(time.time())).encode()
r = c.post(f"/complaints/{cid}/evidence", headers=h, files={"file": ("a.txt", data, "text/plain")})
check(r.status_code == 201, "upload (201)")
ev = r.json()
eid = ev["id"]
check(ev["sha256"] == hashlib.sha256(data).hexdigest(), "server hash equals my hash")
check("uploaded_by" not in ev and "user_id" not in ev, "no uploader field in reply")

v = f"/complaints/{cid}/evidence/{eid}/verify"
check(c.post(v, headers=h).json()["integrity_ok"] is True, "verify before change")
r = c.get(f"/complaints/{cid}/evidence/{eid}/download", headers=h)
check(r.content == data, "download returns same bytes")
r = c.post(f"/complaints/{cid}/evidence", headers=h,
           files={"file": ("virus.exe", b"MZ..", "application/x-msdownload")})
check(r.status_code == 415, "bad type refused (415)")

target = sorted(Path("uploads").iterdir(), key=lambda p: p.stat().st_mtime)[-1]
with open(target, "ab") as f:
    f.write(b"tampered")
b = c.post(v, headers=h).json()
check(b["integrity_ok"] is False, "verify after change: " + b["message"])
target.write_bytes(data)
check(c.post(v, headers=h).json()["integrity_ok"] is True, "verify after restore")

print("ALL CHECKS PASSED" if not bad else str(len(bad)) + " CHECK(S) FAILED")