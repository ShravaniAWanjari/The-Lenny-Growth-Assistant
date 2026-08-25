import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== STEP 1: Create Session A and Session B ===")
sA = client.post("/sessions", json={"metadata": {"title": "Burnout Discussion"}}).json()
sB = client.post("/sessions", json={"metadata": {"title": "MVP Discussion"}}).json()
session_a_id = sA["session_id"]
session_b_id = sB["session_id"]
print("Session A ID:", session_a_id)
print("Session B ID:", session_b_id)

print("\n=== STEP 2: Session A - Turn 1 (Andy Johns on Burnout) ===")
rA1 = client.post(
    "/chat",
    json={"session_id": session_a_id, "prompt": "What does Andy Johns say about burnout?", "provider": "gemini"},
).json()
print("A1 Response excerpt:", rA1["response"][:200])
print("A1 Sources count:", len(rA1["sources"]))

print("\n=== STEP 3: Session A - Turn 2 Follow-up (What did he do after that?) ===")
rA2 = client.post(
    "/chat",
    json={"session_id": session_a_id, "prompt": "What did he do after that?", "provider": "gemini"},
).json()
print("A2 Response excerpt:", rA2["response"][:300])

print("\n=== STEP 4: Session B - Turn 1 (Lenny on MVPs) ===")
rB1 = client.post(
    "/chat",
    json={"session_id": session_b_id, "prompt": "What does Lenny say about MVPs?", "provider": "gemini"},
).json()
print("B1 Response excerpt:", rB1["response"][:200])

print("\n=== STEP 5: Verify Session Messages & Complete Isolation ===")
msgsA = client.get(f"/sessions/{session_a_id}/messages").json()
msgsB = client.get(f"/sessions/{session_b_id}/messages").json()

print(f"Session A Message Count: {len(msgsA)}")
for i, m in enumerate(msgsA):
    print(f"  A[{i}] ({m['role']}): {m['content'][:80]}...")

print(f"Session B Message Count: {len(msgsB)}")
for i, m in enumerate(msgsB):
    print(f"  B[{i}] ({m['role']}): {m['content'][:80]}...")

# Assert complete isolation
assert len(msgsA) == 4
assert len(msgsB) == 2
assert all("Andy Johns" not in m["content"] for m in msgsB)
print("\nSESSION ISOLATION & MULTI-TURN VERIFICATION PASSED!")
