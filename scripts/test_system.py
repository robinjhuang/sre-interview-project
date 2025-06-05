#!/usr/bin/env python3

import requests
import time
import json
import sys
from concurrent.futures import ThreadPoolExecutor
import random

PRODUCER_URL = "http://localhost:5000"

def test_health_check():
    print("Testing health check...")
    try:
        response = requests.get(f"{PRODUCER_URL}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def send_single_message(msg_id):
    payload = {
        "id": f"test_msg_{msg_id}",
        "payload": f"Test message {msg_id} - {random.choice(['urgent', 'normal', 'low'])} priority",
        "processing_time": random.uniform(0.5, 3.0)
    }
    
    try:
        response = requests.post(f"{PRODUCER_URL}/produce", json=payload)
        if response.status_code == 201:
            return True, f"Message {msg_id} sent successfully"
        else:
            return False, f"Message {msg_id} failed with status {response.status_code}"
    except Exception as e:
        return False, f"Message {msg_id} failed: {e}"

def test_single_messages(count=10):
    print(f"\nTesting {count} single messages...")
    success_count = 0
    
    for i in range(count):
        success, message = send_single_message(i)
        if success:
            success_count += 1
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
        time.sleep(0.1)
    
    print(f"Single message test: {success_count}/{count} successful")
    return success_count == count

def test_batch_messages():
    print("\nTesting batch messages...")
    batch_payload = {
        "messages": [
            {"id": f"batch_msg_{i}", "payload": f"Batch message {i}", "processing_time": 1.0}
            for i in range(5)
        ]
    }
    
    try:
        response = requests.post(f"{PRODUCER_URL}/batch-produce", json=batch_payload)
        if response.status_code == 201:
            print("✓ Batch messages sent successfully")
            return True
        else:
            print(f"✗ Batch messages failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Batch messages failed: {e}")
        return False

def test_concurrent_load(threads=5, messages_per_thread=10):
    print(f"\nTesting concurrent load: {threads} threads, {messages_per_thread} messages each...")
    
    def send_messages(thread_id):
        success_count = 0
        for i in range(messages_per_thread):
            success, _ = send_single_message(f"{thread_id}_{i}")
            if success:
                success_count += 1
            time.sleep(0.05)
        return success_count
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        results = list(executor.map(send_messages, range(threads)))
    
    end_time = time.time()
    total_messages = sum(results)
    total_expected = threads * messages_per_thread
    duration = end_time - start_time
    
    print(f"✓ Concurrent test: {total_messages}/{total_expected} messages sent in {duration:.2f}s")
    print(f"  Rate: {total_messages/duration:.2f} messages/second")
    
    return total_messages == total_expected

def check_metrics():
    print("\nChecking metrics...")
    try:
        response = requests.get(f"{PRODUCER_URL}/metrics")
        if response.status_code == 200:
            print("✓ Metrics endpoint accessible")
            return True
        else:
            print(f"✗ Metrics failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Metrics check failed: {e}")
        return False

def main():
    print("SRE System Test Suite")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health_check),
        ("Single Messages", lambda: test_single_messages(10)),
        ("Batch Messages", test_batch_messages),
        ("Concurrent Load", lambda: test_concurrent_load(3, 5)),
        ("Metrics Check", check_metrics)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print(f"\n{'='*40}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()