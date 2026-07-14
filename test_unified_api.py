import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_health():
    print("\n" + "=" * 80)
    print("Test 1: Health Check")
    print("=" * 80)
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        result = response.json()
        print(f"Status: {result['status']}")
        print(f"Components:")
        for comp, status in result['components'].items():
            print(f"  - {comp}: {status}")
        print(f"Environment:")
        for var, status in result['environment'].items():
            print(f"  - {var}: {status}")
        return result['status'] == 'healthy'
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_qa_query():
    print("\n" + "=" * 80)
    print("Test 2: Q&A Domain - Policy Query")
    print("=" * 80)
    payload = {
        "query": "Beijing accommodation standard?",
        "user_id": "test_user_001"
    }
    try:
        print(f"Query: {payload['query']}")
        response = requests.post(f"{API_BASE}/api/unified/chat", json=payload, timeout=30)
        result = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Route: {result['route']}")
        print(f"Answer: {result['answer'][:150]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_auto_approval():
    print("\n" + "=" * 80)
    print("Test 3: Approval Domain - Auto Approval (< 1000 RMB)")
    print("=" * 80)
    payload = {
        "query": "I want to reimburse my Beijing business trip for 2 days, 800 RMB total",
        "user_id": "test_user_002"
    }
    try:
        print(f"Query: {payload['query']}")
        response = requests.post(f"{API_BASE}/api/unified/chat", json=payload, timeout=30)
        result = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Route: {result['route']}")
        print(f"Answer: {result['answer']}")
        if "approval" in result['route']:
            print("SUCCESS: Routed to approval domain!")
            print("Check Feishu for GREEN approval card")
            return True
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_feishu():
    print("\n" + "=" * 80)
    print("Test 4: Feishu Notification Test")
    print("=" * 80)
    try:
        response = requests.post(f"{API_BASE}/api/test/feishu", timeout=10)
        result = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Result: {result['message']}")
        if response.status_code == 200:
            print("SUCCESS: Feishu notification sent!")
            print("Check Feishu for BLUE test card")
            return True
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    print("\n" + "=" * 80)
    print("Unified RAG-Agent Architecture v2.0 - Feishu Integration Test")
    print("=" * 80)
    
    print("\nWaiting for service to start...")
    time.sleep(2)
    
    results = []
    results.append(("Health Check", test_health()))
    time.sleep(1)
    
    results.append(("Q&A Query", test_qa_query()))
    time.sleep(1)
    
    results.append(("Auto Approval", test_auto_approval()))
    time.sleep(2)
    
    results.append(("Feishu Notification", test_feishu()))
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nPass Rate: {passed}/{total} ({passed*100//total}%)")
    
    print("\n" + "=" * 80)
    print("Check Feishu Group for:")
    print("  1. System Startup Notification (GREEN)")
    print("  2. Approval Passed Card (GREEN) - Test 3")
    print("  3. Test Notification Card (BLUE) - Test 4")
    print("=" * 80)

if __name__ == "__main__":
    main()
