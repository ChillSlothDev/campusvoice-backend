"""
Load Testing Script
Create multiple complaints and votes to test performance
"""

import requests
import concurrent.futures
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def create_complaint(student_num):
    """Create a test complaint"""
    data = {
        "name": f"Student {student_num}",
        "register_number": f"22CS{student_num:03d}",
        "department": "CSE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": f"Test Complaint #{student_num}",
        "description": f"This is test complaint number {student_num} for load testing",
        "image_url": None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/complaints", json=data)
        if response.status_code == 201:
            return response.json().get("complaint_id")
        return None
    except Exception as e:
        print(f"Error creating complaint: {e}")
        return None

def vote_on_complaint(complaint_id, voter_num, vote_type="upvote"):
    """Vote on a complaint"""
    data = {
        "complaint_id": complaint_id,
        "roll_number": f"22CS{voter_num:03d}",
        "vote_type": vote_type
    }
    
    try:
        response = requests.post(f"{BASE_URL}/vote", json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error voting: {e}")
        return False

def load_test(num_complaints=10, num_votes_per_complaint=5):
    """Run load test"""
    print(f"\n{'='*60}")
    print(f"🔥 LOAD TEST")
    print(f"{'='*60}")
    print(f"Creating {num_complaints} complaints...")
    print(f"Adding {num_votes_per_complaint} votes per complaint...")
    print(f"Total operations: {num_complaints + (num_complaints * num_votes_per_complaint)}")
    
    start_time = time.time()
    
    # Create complaints in parallel
    complaint_ids = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_complaint, i) for i in range(1, num_complaints + 1)]
        for future in concurrent.futures.as_completed(futures):
            complaint_id = future.result()
            if complaint_id:
                complaint_ids.append(complaint_id)
    
    print(f"✅ Created {len(complaint_ids)} complaints")
    
    # Vote on complaints in parallel
    vote_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for i, complaint_id in enumerate(complaint_ids):
            for voter in range(num_votes_per_complaint):
                voter_num = (i * num_votes_per_complaint) + voter + 1000
                futures.append(
                    executor.submit(vote_on_complaint, complaint_id, voter_num)
                )
        
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                vote_count += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Added {vote_count} votes")
    print(f"\n{'='*60}")
    print(f"⏱️  Duration: {duration:.2f} seconds")
    print(f"📊 Throughput: {(len(complaint_ids) + vote_count) / duration:.2f} ops/sec")
    print(f"{'='*60}")

if __name__ == "__main__":
    load_test(num_complaints=20, num_votes_per_complaint=10)
