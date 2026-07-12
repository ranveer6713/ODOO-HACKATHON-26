"""
backend/test_api.py
End-to-end smoke test for the AssetFlow backend API.
Usage:  python backend/test_api.py
Requires the Uvicorn server to be running on http://127.0.0.1:8000
"""

import sys
import requests
from datetime import datetime, timezone, timedelta

BASE = "http://127.0.0.1:8000/api/v1"


def ok(label, condition, detail=""):
    icon = "[PASS]" if condition else "[FAIL]"
    print(f"  {icon}  {label}" + (f"  ->  {detail}" if detail else ""))
    if not condition:
        sys.exit(1)


def run():
    print("\n==========================================")
    print("  AssetFlow API -- End-to-End Smoke Test  ")
    print("==========================================\n")

    # 1. Login
    print("1. Authentication")
    r = requests.post(f"{BASE}/auth/login", json={"email": "manager@assetflow.com", "password": "manager123"})
    ok("Login returns 200", r.status_code == 200, str(r.status_code))
    token = r.json().get("access_token")
    ok("JWT token received", bool(token))
    H = {"Authorization": f"Bearer {token}"}

    # 2. Asset directory
    print("\n2. Asset Directory")
    r = requests.get(f"{BASE}/assets/", headers=H)
    ok("GET /assets/ returns 200", r.status_code == 200)
    assets = r.json()
    ok(f"Seeded assets found (got {len(assets)})", len(assets) >= 3)
    for a in assets:
        print(f"     [{a['asset_tag']}] {a['name']}  --  {a['status']}")

    asset1 = next(a for a in assets if a["asset_tag"] == "AST-0001")
    asset_id = asset1["id"]

    # 3. Checkout
    print("\n3. Checkout (Allocate)")
    due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    r = requests.post(
        f"{BASE}/allocations/",
        json={"asset_id": asset_id, "employee_id": 4, "expected_return_date": due, "condition_out": "Pristine"},
        headers=H,
    )
    ok("POST /allocations/ returns 201", r.status_code == 201, str(r.status_code))
    alloc_id = r.json()["id"]
    ok("Allocation ID assigned", alloc_id > 0, str(alloc_id))

    # 4. Conflict detection
    print("\n4. Conflict Detection")
    r = requests.post(
        f"{BASE}/allocations/",
        json={"asset_id": asset_id, "employee_id": 3},
        headers=H,
    )
    ok("Re-allocation blocked (409)", r.status_code == 409, str(r.status_code))
    print(f"     Detail: {r.json().get('detail')}")

    # 5. Transfer request
    print("\n5. Transfer Request")
    r = requests.post(
        f"{BASE}/transfers/",
        json={"asset_id": asset_id, "to_employee_id": 3, "requester_notes": "Needed for client visit"},
        headers=H,
    )
    ok("POST /transfers/ returns 201", r.status_code == 201, str(r.status_code))
    transfer_id = r.json()["id"]
    ok("Transfer ID assigned", transfer_id > 0, str(transfer_id))

    # 6. Transfer approval
    print("\n6. Transfer Approval")
    r = requests.post(
        f"{BASE}/transfers/{transfer_id}/action",
        json={"action": "approved", "approver_notes": "Approved by IT Manager"},
        headers=H,
    )
    ok("POST /transfers/{id}/action returns 200", r.status_code == 200, str(r.status_code))
    ok("Transfer status is approved", r.json()["status"] == "approved")

    # 7. Verify new holder
    print("\n7. Verify new holder")
    r = requests.get(f"{BASE}/allocations/?asset_id={asset_id}&status=active", headers=H)
    ok("Active allocation found", r.status_code == 200 and len(r.json()) == 1)
    new_alloc = r.json()[0]
    ok("New holder is employee 3", new_alloc["employee_id"] == 3, str(new_alloc["employee_id"]))
    new_alloc_id = new_alloc["id"]

    # 8. Return
    print("\n8. Asset Return")
    r = requests.post(
        f"{BASE}/allocations/{new_alloc_id}/return",
        json={"condition_in": "Good -- minor surface scratches"},
        headers=H,
    )
    ok("POST /allocations/{id}/return returns 200", r.status_code == 200, str(r.status_code))

    # 9. Asset back to Available
    print("\n9. Asset Status After Return")
    r = requests.get(f"{BASE}/assets/{asset_id}", headers=H)
    ok("Asset status is Available", r.json()["status"] == "Available", r.json()["status"])

    # 10. Audit history
    print("\n10. Audit History")
    r = requests.get(f"{BASE}/assets/{asset_id}/history", headers=H)
    ok("History records exist", r.status_code == 200 and len(r.json()) > 0, str(len(r.json())))
    for h in r.json():
        print(f"     [{h['performed_at'][:19]}]  {h['action']}")

    print("\n==========================================")
    print("  All tests passed!")
    print("==========================================\n")


if __name__ == "__main__":
    run()
