import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api/v1"


def run_tests():
    print("=== Testing AssetFlow API ===")
    
    # 1. Login
    print("\n1. Logging in as Asset Manager (manager@assetflow.com)...")
    login_data = {
        "username": "manager@assetflow.com",
        "password": "manager123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
        
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful! Token acquired.")

    # 2. Get Assets
    print("\n2. Fetching asset directory...")
    response = requests.get(f"{BASE_URL}/assets/", headers=headers)
    assets = response.json()
    print(f"Found {len(assets)} assets:")
    for a in assets:
        print(f" - [{a['asset_tag']}] {a['name']} (Status: {a['status']})")
        
    # Get ID of AST-0001
    ast1 = next(a for a in assets if a["asset_tag"] == "AST-0001")
    ast1_id = ast1["id"]

    # 3. Allocate Asset AST-0001 to Employee ID 4 (employee@assetflow.com)
    print(f"\n3. Allocating asset AST-0001 (ID: {ast1_id}) to Employee 4...")
    alloc_payload = {
        "asset_id": ast1_id,
        "allocated_to_type": "employee",
        "employee_id": 4,
        "expected_return_date": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
        "condition_on_allocation": "Excellent condition"
    }
    response = requests.post(f"{BASE_URL}/allocations/", json=alloc_payload, headers=headers)
    print(f"Allocation Response: {response.status_code}")
    if response.status_code == 201:
        alloc = response.json()
        print(f"Allocation created! ID: {alloc['id']}, Status: {alloc['status']}")
        alloc_id = alloc["id"]
    else:
        print(f"Failed to allocate: {response.text}")
        return

    # 4. Conflict Detection: Attempt to allocate again
    print("\n4. Testing conflict detection (allocating already allocated asset)...")
    response = requests.post(f"{BASE_URL}/allocations/", json=alloc_payload, headers=headers)
    print(f"Response code (expected 400): {response.status_code}")
    print(f"Response details: {response.json().get('detail')}")

    # 5. Request Transfer to Employee ID 3 (head@assetflow.com)
    print("\n5. Requesting asset transfer from Employee 4 to Employee 3...")
    transfer_payload = {
        "asset_id": ast1_id,
        "to_employee_id": 3,
        "notes": "Need MacBook for field work"
    }
    response = requests.post(f"{BASE_URL}/transfers/", json=transfer_payload, headers=headers)
    print(f"Transfer Request Response: {response.status_code}")
    if response.status_code == 201:
        transfer = response.json()
        print(f"Transfer requested! ID: {transfer['id']}, Status: {transfer['status']}")
        transfer_id = transfer["id"]
    else:
        print(f"Failed to request transfer: {response.text}")
        return

    # 6. Approve Transfer
    print(f"\n6. Approving transfer ID {transfer_id}...")
    action_payload = {
        "status": "approved",
        "notes": "Approved by IT Asset Manager"
    }
    response = requests.post(f"{BASE_URL}/transfers/{transfer_id}/action", json=action_payload, headers=headers)
    print(f"Transfer Approval Response: {response.status_code}")
    if response.status_code == 200:
        print("Transfer approved successfully!")
    else:
        print(f"Failed to approve transfer: {response.text}")
        return

    # 7. Check current asset holder and active allocations
    print("\n7. Verifying asset status and new holder after transfer...")
    response = requests.get(f"{BASE_URL}/assets/{ast1_id}", headers=headers)
    asset_updated = response.json()
    print(f"Asset Status: {asset_updated['status']}")
    
    response = requests.get(f"{BASE_URL}/allocations/asset/{ast1_id}", headers=headers)
    if response.status_code == 200:
        new_alloc = response.json()
        print(f"Current Active Allocation ID: {new_alloc['id']}")
        print(f"Allocated to Employee ID: {new_alloc['employee_id']} (Status: {new_alloc['status']})")
        new_alloc_id = new_alloc["id"]
    else:
        print(f"Failed to get active allocation: {response.text}")
        return

    # 8. Return Asset
    print(f"\n8. Returning asset AST-0001 (Closing allocation {new_alloc_id})...")
    return_payload = {
        "condition_on_return": "Good condition, slight keyboard wear"
    }
    response = requests.post(f"{BASE_URL}/allocations/{new_alloc_id}/return", json=return_payload, headers=headers)
    print(f"Return Response: {response.status_code}")
    if response.status_code == 200:
        print("Asset returned successfully!")
    else:
        print(f"Failed to return asset: {response.text}")
        return

    # 9. Verify Asset is Available again
    print("\n9. Verifying asset is back to Available...")
    response = requests.get(f"{BASE_URL}/assets/{ast1_id}", headers=headers)
    asset_final = response.json()
    print(f"Asset Name: {asset_final['name']}")
    print(f"Asset Status (expected Available): {asset_final['status']}")
    
    print("\n=== All Tests Completed Successfully! ===")


if __name__ == "__main__":
    run_tests()
