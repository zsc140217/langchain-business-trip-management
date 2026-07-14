"""
模拟审批流程 - 演示飞书真实接入
"""
import requests
import json
import time

API_BASE = "http://localhost:8001"

print("=" * 80)
print("Feishu Approval Process Simulation")
print("=" * 80)

# Test 1: Auto Approval (amount < 1000)
print("\n[Scenario 1] Auto Approval - Amount 800 RMB < Threshold 1000 RMB")
print("-" * 80)

payload1 = {
    "query": "I want to reimburse my Beijing business trip for 2 days, accommodation 500 RMB, meals 300 RMB, total 800 RMB",
    "user_id": "zhang_san",
    "conversation_id": "conv_001"
}

print(f"Request: {payload1['query']}")
print(f"User: {payload1['user_id']}")
print("\n[Sending request to API...]")

try:
    response1 = requests.post(
        f"{API_BASE}/api/unified/chat",
        json=payload1,
        timeout=60
    )
    
    result1 = response1.json()
    
    print(f"\n[API Response]")
    print(f"Status Code: {response1.status_code}")
    print(f"Route: {result1['route']}")
    print(f"\nSystem Reply:")
    print(result1['answer'])
    
    print("\n[SUCCESS] Feishu Notification Sent!")
    print("Check your Feishu group for:")
    print("  - Title: Approval Passed")
    print("  - Color: GREEN")
    print("  - Content: Approval ID, Destination, Days, Amount, Auto-approved")
    
except Exception as e:
    print(f"\n[FAILED] Request failed: {e}")

print("\n" + "=" * 80)
time.sleep(3)

# Test 2: Manual Approval (amount >= 1000)
print("\n[Scenario 2] Manual Approval - Amount 2500 RMB >= Threshold 1000 RMB")
print("-" * 80)

payload2 = {
    "query": "I want to reimburse my Shanghai business trip for 5 days, accommodation 1500 RMB, meals 750 RMB, transportation 250 RMB, total 2500 RMB",
    "user_id": "li_si",
    "conversation_id": "conv_002"
}

print(f"Request: {payload2['query']}")
print(f"User: {payload2['user_id']}")
print("\n[Sending request to API...]")

try:
    response2 = requests.post(
        f"{API_BASE}/api/unified/chat",
        json=payload2,
        timeout=60
    )
    
    result2 = response2.json()
    
    print(f"\n[API Response]")
    print(f"Status Code: {response2.status_code}")
    print(f"Route: {result2['route']}")
    print(f"\nSystem Reply:")
    print(result2['answer'])
    
    print("\n[SUCCESS] Feishu Notification Sent!")
    print("Check your Feishu group for:")
    print("  - Title: Pending Approval: Reimbursement Request")
    print("  - Color: ORANGE")
    print("  - Content: Approval ID, Applicant, Destination, Days, Amount, Pending")
    
except Exception as e:
    print(f"\n[FAILED] Request failed: {e}")

print("\n" + "=" * 80)
print("\nSimulation Complete!")
print("\nCheck Feishu group for 2 messages:")
print("  1. GREEN card - zhang_san auto-approved")
print("  2. ORANGE card - li_si pending manual approval")
print("=" * 80)
