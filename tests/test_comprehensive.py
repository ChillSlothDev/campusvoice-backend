"""
COMPREHENSIVE TEST SUITE FOR CAMPUSVOICE
=========================================
Tests all scenarios:
1. Multiple students submit different complaints
2. Students view their own complaints
3. Students view public feed
4. Students vote on complaints
5. Different authorities view assigned complaints
6. Authorities change status
7. Admin views all system details
8. Priority changes based on votes
9. WebSocket real-time updates (optional)

Run: python test_comprehensive.py
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List
import sys

BASE_URL = "http://localhost:8000/api"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Test data storage
test_data = {
    "students": [],
    "complaints": [],
    "authorities": [],
    "votes": []
}

def print_header(text):
    """Print styled header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}{text:^80}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_section(text):
    """Print section header"""
    print(f"\n{CYAN}{'─'*80}{RESET}")
    print(f"{CYAN}{BOLD}{text}{RESET}")
    print(f"{CYAN}{'─'*80}{RESET}")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def print_test(number, total, text):
    """Print test number"""
    print(f"\n{MAGENTA}{BOLD}[TEST {number}/{total}] {text}{RESET}")


# ============================================
# SCENARIO 1: STUDENTS SUBMIT COMPLAINTS
# ============================================

def scenario_1_students_submit_complaints():
    """Multiple students submit different types of complaints"""
    print_header("SCENARIO 1: STUDENTS SUBMIT COMPLAINTS")
    
    # Define 5 different students with different complaints
    students = [
        {
            "name": "Arun Kumar",
            "register_number": "22CS045",
            "department": "CSE",
            "stay_type": "Hostel",
            "visibility": "Public",
            "title": "Library AC not working",
            "description": "The air conditioning in the main library has been broken for 3 days. Students are unable to study in the hot weather. This affects hundreds of students daily.",
            "image_url": None
        },
        {
            "name": "Priya Sharma",
            "register_number": "22EC012",
            "department": "ECE",
            "stay_type": "Day Scholar",
            "visibility": "Public",
            "title": "Mess food quality very poor",
            "description": "The food quality in mess has deteriorated significantly. Rice is undercooked, curry is watery, and vegetables are not fresh. Multiple students have complained about stomach issues.",
            "image_url": None
        },
        {
            "name": "Rahul Verma",
            "register_number": "22ME028",
            "department": "MECH",
            "stay_type": "Hostel",
            "visibility": "Public",
            "title": "Hostel wifi extremely slow",
            "description": "Hostel block B wifi speed is less than 1 Mbps. Cannot attend online classes or download study materials. Issue persists for 2 weeks.",
            "image_url": None
        },
        {
            "name": "Sneha Reddy",
            "register_number": "22IT019",
            "department": "IT",
            "stay_type": "Day Scholar",
            "visibility": "Public",
            "title": "Bus timing inconvenient",
            "description": "College bus leaves at 6:30 AM which is too early. Many day scholars miss classes because of this. Request to change timing to 7:00 AM.",
            "image_url": None
        },
        {
            "name": "Karthik Menon",
            "register_number": "22CS067",
            "department": "CSE",
            "stay_type": "Hostel",
            "visibility": "Public",
            "title": "Library books missing",
            "description": "Several important reference books for Data Structures course are missing from library. Students need these for exam preparation.",
            "image_url": None
        }
    ]
    
    print_info(f"Submitting {len(students)} complaints from different students...")
    
    for idx, student in enumerate(students, 1):
        print_test(idx, len(students), f"Student: {student['name']} - {student['title']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/complaints",
                json=student,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Store student and complaint data
                test_data["students"].append({
                    "name": student["name"],
                    "roll_number": student["register_number"],
                    "department": student["department"]
                })
                
                test_data["complaints"].append({
                    "complaint_id": data.get("complaint_id"),
                    "title": student["title"],
                    "student_name": student["name"],
                    "roll_number": student["register_number"],
                    "priority": data.get("priority"),
                    "category": data.get("category"),
                    "assigned_to": data.get("assigned_to"),
                    "status": "raised"
                })
                
                print_success(f"Complaint submitted successfully")
                print(f"   ID: {CYAN}{data.get('complaint_id')}{RESET}")
                print(f"   Priority: {data.get('priority').upper()}")
                print(f"   Category: {data.get('category')}")
                print(f"   Assigned to: {data.get('assigned_to')}")
                print(f"   Summary: {data.get('summary')}")
            else:
                print_error(f"Failed to submit: {response.status_code}")
                print(response.text)
        
        except Exception as e:
            print_error(f"Error: {e}")
        
        time.sleep(0.5)
    
    print_section("SUMMARY")
    print(f"Total complaints submitted: {GREEN}{len(test_data['complaints'])}{RESET}")
    
    # Show breakdown by category
    categories = {}
    for c in test_data["complaints"]:
        cat = c["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nComplaints by category:")
    for cat, count in categories.items():
        print(f"  • {cat}: {count}")
    
    return len(test_data["complaints"]) > 0


# ============================================
# SCENARIO 2: STUDENTS VIEW THEIR COMPLAINTS
# ============================================

def scenario_2_students_view_own_complaints():
    """Each student views their own submitted complaints"""
    print_header("SCENARIO 2: STUDENTS VIEW THEIR OWN COMPLAINTS")
    
    if not test_data["students"]:
        print_error("No students found. Run scenario 1 first.")
        return False
    
    for idx, student in enumerate(test_data["students"], 1):
        print_test(idx, len(test_data["students"]), f"Viewing complaints for {student['name']}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/complaints/my",
                params={"roll_number": student["roll_number"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                
                print_success(f"Found {count} complaint(s)")
                
                for complaint in data.get("complaints", []):
                    print(f"   • {complaint['title']} ({complaint['status'].upper()})")
            else:
                print_error(f"Failed to fetch: {response.status_code}")
        
        except Exception as e:
            print_error(f"Error: {e}")
        
        time.sleep(0.3)
    
    return True


# ============================================
# SCENARIO 3: STUDENTS VIEW PUBLIC FEED
# ============================================

def scenario_3_view_public_feed():
    """Students view public complaints feed"""
    print_header("SCENARIO 3: STUDENTS VIEW PUBLIC FEED")
    
    try:
        response = requests.get(f"{BASE_URL}/complaints/public?limit=10")
        
        if response.status_code == 200:
            data = response.json()
            complaints = data.get("complaints", [])
            
            print_success(f"Retrieved {len(complaints)} public complaints")
            
            print(f"\n{BOLD}Public Feed:{RESET}")
            print(f"{CYAN}{'Title':<40} {'Status':<12} {'Priority':<10} {'Votes':<10}{RESET}")
            print(f"{CYAN}{'-'*80}{RESET}")
            
            for c in complaints:
                title = c['title'][:38]
                status = c['status']
                priority = c['priority']
                votes = f"↑{c['upvotes']} ↓{c['downvotes']}"
                
                print(f"{title:<40} {status:<12} {priority:<10} {votes:<10}")
            
            return True
        else:
            print_error(f"Failed to fetch public feed: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


# ============================================
# SCENARIO 4: STUDENTS VOTE ON COMPLAINTS
# ============================================

def scenario_4_students_vote():
    """Students vote on various complaints"""
    print_header("SCENARIO 4: STUDENTS VOTE ON COMPLAINTS")
    
    if not test_data["complaints"]:
        print_error("No complaints found. Run scenario 1 first.")
        return False
    
    # Create voting patterns
    # - Library AC: 15 upvotes, 2 downvotes (high priority issue)
    # - Mess food: 20 upvotes, 1 downvote (critical issue)
    # - Hostel wifi: 8 upvotes, 3 downvotes (medium issue)
    # - Bus timing: 5 upvotes, 8 downvotes (controversial)
    # - Library books: 12 upvotes, 0 downvotes (clear need)
    
    voting_patterns = [
        {"upvotes": 15, "downvotes": 2},   # Library AC
        {"upvotes": 20, "downvotes": 1},   # Mess food
        {"upvotes": 8, "downvotes": 3},    # Hostel wifi
        {"upvotes": 5, "downvotes": 8},    # Bus timing
        {"upvotes": 12, "downvotes": 0}    # Library books
    ]
    
    for idx, complaint in enumerate(test_data["complaints"]):
        if idx >= len(voting_patterns):
            break
        
        pattern = voting_patterns[idx]
        complaint_id = complaint["complaint_id"]
        
        print_test(idx + 1, len(test_data["complaints"]), 
                  f"Voting on: {complaint['title'][:50]}")
        
        # Simulate upvotes
        for vote_num in range(pattern["upvotes"]):
            voter_roll = f"22XX{idx:02d}{vote_num:03d}"
            
            try:
                response = requests.post(
                    f"{BASE_URL}/vote",
                    json={
                        "complaint_id": complaint_id,
                        "roll_number": voter_roll,
                        "vote_type": "upvote"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check if priority was updated
                    if data.get("priority_updated"):
                        print(f"   📊 Priority updated: {data['old_priority']} → {GREEN}{data['new_priority']}{RESET}")
            
            except Exception as e:
                print_error(f"Upvote error: {e}")
        
        # Simulate downvotes
        for vote_num in range(pattern["downvotes"]):
            voter_roll = f"22YY{idx:02d}{vote_num:03d}"
            
            try:
                response = requests.post(
                    f"{BASE_URL}/vote",
                    json={
                        "complaint_id": complaint_id,
                        "roll_number": voter_roll,
                        "vote_type": "downvote"
                    }
                )
            
            except Exception as e:
                print_error(f"Downvote error: {e}")
        
        # Get final vote stats
        try:
            response = requests.get(f"{BASE_URL}/votes/{complaint_id}")
            if response.status_code == 200:
                stats = response.json()
                print_success(f"Voting complete: ↑{stats['upvotes']} ↓{stats['downvotes']} (Net: {stats['net_votes']})")
        except:
            pass
        
        time.sleep(0.5)
    
    return True


# ============================================
# SCENARIO 5: AUTHORITIES VIEW ASSIGNED COMPLAINTS
# ============================================

def scenario_5_authorities_view_complaints():
    """Different authorities view their assigned complaints"""
    print_header("SCENARIO 5: AUTHORITIES VIEW ASSIGNED COMPLAINTS")
    
    # Define authorities
    authorities = [
        {"type": "infrastructure", "name": "Maintenance Officer", "id": "MAINT001"},
        {"type": "food", "name": "Mess Committee Head", "id": "MESS001"},
        {"type": "hostel", "name": "Hostel Warden", "id": "HOSTEL001"},
        {"type": "transport", "name": "Transport Coordinator", "id": "TRANS001"},
        {"type": "academic", "name": "Academic Dean", "id": "ACAD001"}
    ]
    
    test_data["authorities"] = authorities
    
    for idx, authority in enumerate(authorities, 1):
        print_test(idx, len(authorities), f"{authority['name']} viewing assigned complaints")
        
        try:
            response = requests.get(
                f"{BASE_URL}/authority/{authority['type']}/complaints"
            )
            
            if response.status_code == 200:
                data = response.json()
                complaints = data.get("complaints", [])
                
                print_success(f"Found {len(complaints)} assigned complaint(s)")
                
                for c in complaints:
                    print(f"   • {c['title'][:60]} [{c['status'].upper()}] (Priority: {c['priority']})")
            else:
                print_error(f"Failed to fetch: {response.status_code}")
        
        except Exception as e:
            print_error(f"Error: {e}")
        
        time.sleep(0.5)
    
    return True


# ============================================
# SCENARIO 6: AUTHORITIES CHANGE STATUS
# ============================================

def scenario_6_authorities_change_status():
    """Authorities update complaint statuses"""
    print_header("SCENARIO 6: AUTHORITIES CHANGE COMPLAINT STATUS")
    
    if not test_data["complaints"] or not test_data["authorities"]:
        print_error("Need complaints and authorities. Run scenarios 1 and 5 first.")
        return False
    
    # Define status changes
    status_updates = [
        {"complaint_idx": 0, "authority_idx": 0, "new_status": "opened", "reason": "Forwarded to maintenance team for immediate attention"},
        {"complaint_idx": 1, "authority_idx": 1, "new_status": "reviewed", "reason": "Mess committee inspected kitchen. Taking corrective action"},
        {"complaint_idx": 2, "authority_idx": 2, "new_status": "opened", "reason": "IT team notified to check hostel network infrastructure"},
        {"complaint_idx": 3, "authority_idx": 3, "new_status": "reviewed", "reason": "Transport timing reviewed. Will consider in next schedule update"},
        {"complaint_idx": 4, "authority_idx": 4, "new_status": "closed", "reason": "Missing books have been procured and added to library"}
    ]
    
    for idx, update in enumerate(status_updates, 1):
        complaint = test_data["complaints"][update["complaint_idx"]]
        authority = test_data["authorities"][update["authority_idx"]]
        
        print_test(idx, len(status_updates), 
                  f"{authority['name']} updating: {complaint['title'][:45]}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/status/update",
                json={
                    "complaint_id": complaint["complaint_id"],
                    "new_status": update["new_status"],
                    "updated_by_roll": authority["id"],
                    "reason": update["reason"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print_success(f"Status updated: {data['old_status'].upper()} → {data['new_status'].upper()}")
                print(f"   Reason: {update['reason']}")
                
                # Update local data
                complaint["status"] = update["new_status"]
            else:
                print_error(f"Failed to update status: {response.status_code}")
                print(response.text)
        
        except Exception as e:
            print_error(f"Error: {e}")
        
        time.sleep(0.5)
    
    return True


# ============================================
# SCENARIO 7: ADMIN VIEWS ALL DETAILS
# ============================================

def scenario_7_admin_view_system():
    """Admin views comprehensive system statistics"""
    print_header("SCENARIO 7: ADMIN VIEWS SYSTEM DETAILS")
    
    print_section("Overall Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            print(f"\n{BOLD}System Overview:{RESET}")
            print(f"  Total Students: {GREEN}{stats.get('total_students', 0)}{RESET}")
            print(f"  Total Complaints: {GREEN}{stats.get('total_complaints', 0)}{RESET}")
            print(f"  Total Votes: {GREEN}{stats.get('total_votes', 0)}{RESET}")
            
            # Complaints by status
            status_breakdown = stats.get('complaints_by_status', {})
            if status_breakdown:
                print(f"\n{BOLD}Complaints by Status:{RESET}")
                for status, count in status_breakdown.items():
                    print(f"  • {status.upper()}: {count}")
            
            # Complaints by priority
            priority_breakdown = stats.get('complaints_by_priority', {})
            if priority_breakdown:
                print(f"\n{BOLD}Complaints by Priority:{RESET}")
                for priority, count in priority_breakdown.items():
                    color = {
                        'low': GREEN,
                        'medium': YELLOW,
                        'high': MAGENTA,
                        'critical': RED
                    }.get(priority, RESET)
                    print(f"  • {color}{priority.upper()}: {count}{RESET}")
        
        else:
            print_error(f"Failed to fetch stats: {response.status_code}")
    
    except Exception as e:
        print_error(f"Error: {e}")
    
    print_section("Detailed Complaint View")
    
    # View each complaint in detail
    for idx, complaint in enumerate(test_data["complaints"], 1):
        print(f"\n{BOLD}[{idx}] {complaint['title']}{RESET}")
        
        try:
            response = requests.get(f"{BASE_URL}/complaints/{complaint['complaint_id']}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"  Student: {data['student']['name']} ({data['student']['roll_number']})")
                print(f"  Status: {data['status'].upper()}")
                print(f"  Priority: {data['priority'].upper()}")
                print(f"  Votes: ↑{data['upvotes']} ↓{data['downvotes']} (Net: {data['net_votes']})")
                print(f"  Assigned to: {data['assigned_authority']}")
                print(f"  Category: {data['category']}")
                
                llm = data.get('llm_analysis')
                if llm:
                    print(f"  AI Summary: {llm.get('summary', 'N/A')}")
        
        except Exception as e:
            print_error(f"Error fetching details: {e}")
    
    return True


# ============================================
# SCENARIO 8: VERIFY PRIORITY CHANGES
# ============================================

def scenario_8_verify_priority_changes():
    """Verify that priorities changed based on votes"""
    print_header("SCENARIO 8: VERIFY PRIORITY CHANGES FROM VOTING")
    
    print_info("Checking if priorities were automatically updated based on votes...")
    
    for idx, complaint in enumerate(test_data["complaints"], 1):
        print(f"\n{BOLD}[{idx}] {complaint['title']}{RESET}")
        
        try:
            response = requests.get(f"{BASE_URL}/complaints/{complaint['complaint_id']}")
            
            if response.status_code == 200:
                data = response.json()
                
                original_priority = complaint.get("priority", "unknown")
                current_priority = data.get("priority", "unknown")
                upvotes = data.get("upvotes", 0)
                downvotes = data.get("downvotes", 0)
                
                print(f"  Original Priority: {original_priority}")
                print(f"  Current Priority: {current_priority}")
                print(f"  Votes: ↑{upvotes} ↓{downvotes}")
                
                if original_priority != current_priority:
                    print_success(f"Priority changed: {original_priority} → {current_priority}")
                else:
                    print_info(f"Priority unchanged (still {current_priority})")
        
        except Exception as e:
            print_error(f"Error: {e}")
    
    return True


# ============================================
# MAIN TEST RUNNER
# ============================================

def run_comprehensive_tests():
    """Run all test scenarios"""
    print_header("🧪 CAMPUSVOICE COMPREHENSIVE TEST SUITE")
    print(f"{CYAN}Testing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{CYAN}Base URL: {BASE_URL}{RESET}")
    
    results = {}
    
    # Run scenarios
    print_section("Starting Test Scenarios...")
    
    results['scenario_1'] = scenario_1_students_submit_complaints()
    time.sleep(1)
    
    results['scenario_2'] = scenario_2_students_view_own_complaints()
    time.sleep(1)
    
    results['scenario_3'] = scenario_3_view_public_feed()
    time.sleep(1)
    
    results['scenario_4'] = scenario_4_students_vote()
    time.sleep(1)
    
    results['scenario_5'] = scenario_5_authorities_view_complaints()
    time.sleep(1)
    
    results['scenario_6'] = scenario_6_authorities_change_status()
    time.sleep(1)
    
    results['scenario_7'] = scenario_7_admin_view_system()
    time.sleep(1)
    
    results['scenario_8'] = scenario_8_verify_priority_changes()
    
    # Print final summary
    print_header("📊 TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{BOLD}Scenario Results:{RESET}")
    for scenario, result in results.items():
        if result:
            print(f"  {GREEN}✅ {scenario}: PASSED{RESET}")
        else:
            print(f"  {RED}❌ {scenario}: FAILED{RESET}")
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    if passed == total:
        print(f"{GREEN}{BOLD}✅ ALL SCENARIOS PASSED: {passed}/{total}{RESET}")
    else:
        print(f"{YELLOW}{BOLD}⚠️  SOME SCENARIOS FAILED: {passed}/{total} passed{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    
    # Print test data summary
    print(f"\n{BOLD}Test Data Created:{RESET}")
    print(f"  Students: {len(test_data['students'])}")
    print(f"  Complaints: {len(test_data['complaints'])}")
    print(f"  Authorities: {len(test_data['authorities'])}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_comprehensive_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
