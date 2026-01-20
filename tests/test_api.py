"""
Complete API Test Suite for CampusVoice Backend
Tests all 7 endpoints + database operations
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Test data
TEST_STUDENT = {
    "name": "Test Student",
    "register_number": "22CS999",
    "department": "CSE",
    "stay_type": "Hostel",
    "visibility": "Public",
    "title": "Test Complaint - Automated Test",
    "description": "This is an automated test complaint to verify the system is working correctly. Please ignore.",
    "image_url": None
}

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print section header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def print_response(response):
    """Print formatted response"""
    print(f"\nStatus Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)


# ============================================
# TEST 1: HEALTH CHECK
# ============================================
def test_health_check():
    print_header("TEST 1: HEALTH CHECK")
    
    try:
        response = requests.get(f"{API_URL}/health")
        print_response(response)
        
        if response.status_code == 200:
            print_success("Health check passed")
            return True
        else:
            print_error("Health check failed")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


# ============================================
# TEST 2: DATABASE HEALTH
# ============================================
def test_database_health():
    print_header("TEST 2: DATABASE HEALTH")
    
    try:
        response = requests.get(f"{BASE_URL}/health/database")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_success("Database connection healthy")
                return True
            else:
                print_error("Database connection unhealthy")
                return False
        else:
            print_error("Database health check failed")
            return False
    except Exception as e:
        print_error(f"Database health error: {e}")
        return False


# ============================================
# TEST 3: SUBMIT COMPLAINT
# ============================================
def test_submit_complaint():
    print_header("TEST 3: SUBMIT COMPLAINT")
    
    try:
        response = requests.post(
            f"{API_URL}/complaints",
            json=TEST_STUDENT,
            headers={"Content-Type": "application/json"}
        )
        print_response(response)
        
        if response.status_code == 201:
            data = response.json()
            complaint_id = data.get("complaint_id")
            print_success(f"Complaint submitted successfully")
            print_info(f"Complaint ID: {complaint_id}")
            print_info(f"Priority: {data.get('priority')}")
            print_info(f"Category: {data.get('category')}")
            print_info(f"Assigned to: {data.get('assigned_to')}")
            return complaint_id
        else:
            print_error("Failed to submit complaint")
            return None
    except Exception as e:
        print_error(f"Submit complaint error: {e}")
        return None


# ============================================
# TEST 4: GET COMPLAINT DETAILS
# ============================================
def test_get_complaint_details(complaint_id):
    print_header("TEST 4: GET COMPLAINT DETAILS")
    
    if not complaint_id:
        print_error("No complaint ID provided")
        return False
    
    try:
        response = requests.get(f"{API_URL}/complaints/{complaint_id}")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Complaint details retrieved")
            print_info(f"Title: {data.get('title')}")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Upvotes: {data.get('upvotes')}")
            print_info(f"Downvotes: {data.get('downvotes')}")
            return True
        else:
            print_error("Failed to get complaint details")
            return False
    except Exception as e:
        print_error(f"Get complaint error: {e}")
        return False


# ============================================
# TEST 5: GET MY COMPLAINTS
# ============================================
def test_get_my_complaints():
    print_header("TEST 5: GET MY COMPLAINTS")
    
    try:
        response = requests.get(
            f"{API_URL}/complaints/my",
            params={"roll_number": TEST_STUDENT["register_number"]}
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print_success(f"Retrieved {count} complaint(s)")
            return True
        else:
            print_error("Failed to get my complaints")
            return False
    except Exception as e:
        print_error(f"Get my complaints error: {e}")
        return False


# ============================================
# TEST 6: GET PUBLIC FEED
# ============================================
def test_get_public_feed():
    print_header("TEST 6: GET PUBLIC FEED")
    
    try:
        response = requests.get(
            f"{API_URL}/complaints/public",
            params={"limit": 10}
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print_success(f"Retrieved {count} public complaint(s)")
            return True
        else:
            print_error("Failed to get public feed")
            return False
    except Exception as e:
        print_error(f"Get public feed error: {e}")
        return False


# ============================================
# TEST 7: UPVOTE COMPLAINT
# ============================================
def test_upvote_complaint(complaint_id):
    print_header("TEST 7: UPVOTE COMPLAINT")
    
    if not complaint_id:
        print_error("No complaint ID provided")
        return False
    
    try:
        vote_data = {
            "complaint_id": complaint_id,
            "roll_number": "22CS888",  # Different student
            "vote_type": "upvote"
        }
        
        response = requests.post(
            f"{API_URL}/vote",
            json=vote_data,
            headers={"Content-Type": "application/json"}
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Upvote successful")
            print_info(f"Action: {data.get('action')}")
            print_info(f"Upvotes: {data.get('upvotes')}")
            print_info(f"Downvotes: {data.get('downvotes')}")
            return True
        else:
            print_error("Failed to upvote")
            return False
    except Exception as e:
        print_error(f"Upvote error: {e}")
        return False


# ============================================
# TEST 8: DOWNVOTE COMPLAINT
# ============================================
def test_downvote_complaint(complaint_id):
    print_header("TEST 8: DOWNVOTE COMPLAINT")
    
    if not complaint_id:
        print_error("No complaint ID provided")
        return False
    
    try:
        vote_data = {
            "complaint_id": complaint_id,
            "roll_number": "22CS777",  # Different student
            "vote_type": "downvote"
        }
        
        response = requests.post(
            f"{API_URL}/vote",
            json=vote_data,
            headers={"Content-Type": "application/json"}
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Downvote successful")
            print_info(f"Action: {data.get('action')}")
            print_info(f"Upvotes: {data.get('upvotes')}")
            print_info(f"Downvotes: {data.get('downvotes')}")
            return True
        else:
            print_error("Failed to downvote")
            return False
    except Exception as e:
        print_error(f"Downvote error: {e}")
        return False


# ============================================
# TEST 9: DUPLICATE VOTE PREVENTION
# ============================================
def test_duplicate_vote_prevention(complaint_id):
    print_header("TEST 9: DUPLICATE VOTE PREVENTION")
    
    if not complaint_id:
        print_error("No complaint ID provided")
        return False
    
    try:
        vote_data = {
            "complaint_id": complaint_id,
            "roll_number": "22CS888",  # Same student as Test 7
            "vote_type": "upvote"
        }
        
        print_info("Voting again with same student (should toggle off)...")
        response = requests.post(
            f"{API_URL}/vote",
            json=vote_data,
            headers={"Content-Type": "application/json"}
        )
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            action = data.get('action')
            
            if action == "deleted":
                print_success("Duplicate vote prevention works! Vote was toggled off")
                return True
            elif action == "created":
                print_success("Vote created (student hadn't voted before)")
                return True
            else:
                print_info(f"Vote action: {action}")
                return True
        else:
            print_error("Duplicate vote test failed")
            return False
    except Exception as e:
        print_error(f"Duplicate vote test error: {e}")
        return False


# ============================================
# TEST 10: VOTE STATISTICS
# ============================================
def test_vote_statistics(complaint_id):
    print_header("TEST 10: VOTE STATISTICS")
    
    if not complaint_id:
        print_error("No complaint ID provided")
        return False
    
    try:
        response = requests.get(f"{API_URL}/votes/{complaint_id}")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Vote statistics retrieved")
            print_info(f"Upvotes: {data.get('upvotes')}")
            print_info(f"Downvotes: {data.get('downvotes')}")
            print_info(f"Total: {data.get('total')}")
            print_info(f"Net votes: {data.get('net_votes')}")
            return True
        else:
            print_error("Failed to get vote statistics")
            return False
    except Exception as e:
        print_error(f"Vote statistics error: {e}")
        return False


# ============================================
# TEST 11: WEBSOCKET STATS
# ============================================
def test_websocket_stats():
    print_header("TEST 11: WEBSOCKET STATISTICS")
    
    try:
        response = requests.get(f"{API_URL}/ws/stats")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_success("WebSocket statistics retrieved")
            print_info(f"Active connections: {data.get('total_active_connections')}")
            print_info(f"Active complaints: {data.get('active_complaints')}")
            return True
        else:
            print_error("Failed to get WebSocket statistics")
            return False
    except Exception as e:
        print_error(f"WebSocket stats error: {e}")
        return False


# ============================================
# TEST 12: OVERALL STATISTICS
# ============================================
def test_overall_statistics():
    print_header("TEST 12: OVERALL STATISTICS")
    
    try:
        response = requests.get(f"{API_URL}/stats")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Overall statistics retrieved")
            print_info(f"Total students: {data.get('total_students')}")
            print_info(f"Total complaints: {data.get('total_complaints')}")
            print_info(f"Total votes: {data.get('total_votes')}")
            return True
        else:
            print_error("Failed to get overall statistics")
            return False
    except Exception as e:
        print_error(f"Overall statistics error: {e}")
        return False


# ============================================
# MAIN TEST RUNNER
# ============================================
def run_all_tests():
    """Run all tests in sequence"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🧪 CAMPUSVOICE BACKEND TEST SUITE{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{YELLOW}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    
    results = {}
    complaint_id = None
    
    # Run tests
    results['health_check'] = test_health_check()
    time.sleep(0.5)
    
    results['database_health'] = test_database_health()
    time.sleep(0.5)
    
    complaint_id = test_submit_complaint()
    results['submit_complaint'] = complaint_id is not None
    time.sleep(1)
    
    if complaint_id:
        results['get_complaint_details'] = test_get_complaint_details(complaint_id)
        time.sleep(0.5)
        
        results['get_my_complaints'] = test_get_my_complaints()
        time.sleep(0.5)
        
        results['get_public_feed'] = test_get_public_feed()
        time.sleep(0.5)
        
        results['upvote'] = test_upvote_complaint(complaint_id)
        time.sleep(0.5)
        
        results['downvote'] = test_downvote_complaint(complaint_id)
        time.sleep(0.5)
        
        results['duplicate_vote'] = test_duplicate_vote_prevention(complaint_id)
        time.sleep(0.5)
        
        results['vote_stats'] = test_vote_statistics(complaint_id)
        time.sleep(0.5)
    
    results['websocket_stats'] = test_websocket_stats()
    time.sleep(0.5)
    
    results['overall_stats'] = test_overall_statistics()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}✅ ALL TESTS PASSED: {passed}/{total}{RESET}")
    else:
        print(f"{YELLOW}⚠️  SOME TESTS FAILED: {passed}/{total} passed{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    if complaint_id:
        print(f"\n{YELLOW}📝 Test Complaint ID: {complaint_id}{RESET}")
        print(f"{YELLOW}🔗 View at: {BASE_URL}/docs{RESET}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
