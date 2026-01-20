"""
CAMPUSVOICE INTERACTIVE API TESTER
===================================
Manual testing interface for all endpoints

Features:
- Interactive menu-based navigation
- Manual input for all parameters
- Real-time API responses
- Save test data across sessions
- Color-coded output
"""

import requests
import json
from datetime import datetime
import os

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
    "last_complaint_id": None,
    "last_roll_number": None
}

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    """Print styled header"""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}{text:^80}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_menu(title, options):
    """Print menu with options"""
    print(f"\n{CYAN}{BOLD}{title}{RESET}")
    print(f"{CYAN}{'─'*80}{RESET}")
    for key, value in options.items():
        print(f"  {YELLOW}{key}{RESET}. {value}")
    print(f"{CYAN}{'─'*80}{RESET}")

def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{CYAN}{default}{RESET}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def print_response(response):
    """Print API response"""
    print(f"\n{BOLD}Response:{RESET}")
    print(f"Status Code: {response.status_code}")
    
    try:
        data = response.json()
        print(f"\n{json.dumps(data, indent=2)}")
        return data
    except:
        print(response.text)
        return None

def pause():
    """Pause and wait for user"""
    input(f"\n{YELLOW}Press Enter to continue...{RESET}")

# ============================================
# 1. SUBMIT COMPLAINT
# ============================================

def submit_complaint():
    """Submit a new complaint"""
    print_header("📝 SUBMIT COMPLAINT")
    
    print(f"{BOLD}Enter complaint details:{RESET}")
    
    # Get details
    name = get_input("Student Name", "Test Student")
    roll = get_input("Roll Number", "22CS999")
    dept = get_input("Department", "CSE")
    stay = get_input("Stay Type (Hostel/Day Scholar)", "Day Scholar")
    visibility = get_input("Visibility (Public/Private)", "Public")
    
    print(f"\n{BOLD}Complaint Details:{RESET}")
    title = get_input("Title", "Test Complaint - " + datetime.now().strftime("%H:%M:%S"))
    description = get_input("Description", "This is a test complaint for manual testing")
    image = get_input("Image URL (optional)", "")
    
    # Create payload
    payload = {
        "name": name,
        "register_number": roll,
        "department": dept,
        "stay_type": stay,
        "visibility": visibility,
        "title": title,
        "description": description,
        "image_url": image if image else None
    }
    
    print(f"\n{YELLOW}Submitting complaint...{RESET}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/complaints",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        data = print_response(response)
        
        if response.status_code == 201 and data:
            # Save for later use
            test_data["last_complaint_id"] = data.get("complaint_id")
            test_data["last_roll_number"] = roll
            test_data["complaints"].append({
                "id": data.get("complaint_id"),
                "title": title,
                "roll": roll
            })
            
            print(f"\n{GREEN}✅ Complaint submitted successfully!{RESET}")
            print(f"   Complaint ID: {CYAN}{data.get('complaint_id')}{RESET}")
            print(f"   Category: {data.get('category')}")
            print(f"   Priority: {data.get('priority')}")
            print(f"   Assigned to: {data.get('assigned_to')}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 2. VIEW MY COMPLAINTS
# ============================================

def view_my_complaints():
    """View complaints for a specific student"""
    print_header("📋 VIEW MY COMPLAINTS")
    
    roll = get_input("Roll Number", test_data.get("last_roll_number", "22CS999"))
    limit = get_input("Limit (max complaints)", "10")
    
    print(f"\n{YELLOW}Fetching complaints...{RESET}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/complaints/my",
            params={"roll_number": roll, "limit": int(limit)}
        )
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            complaints = data.get("complaints", [])
            print(f"\n{GREEN}Found {len(complaints)} complaint(s){RESET}")
            
            for i, c in enumerate(complaints, 1):
                print(f"\n{BOLD}[{i}] {c['title']}{RESET}")
                print(f"    Status: {c['status'].upper()}")
                print(f"    Priority: {c['priority']}")
                print(f"    Category: {c.get('category', 'N/A')}")
                print(f"    Votes: ↑{c['upvotes']} ↓{c['downvotes']}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 3. VIEW PUBLIC FEED
# ============================================

def view_public_feed():
    """View public complaints feed"""
    print_header("📰 PUBLIC COMPLAINTS FEED")
    
    limit = get_input("Limit (max complaints)", "20")
    status_filter = get_input("Status Filter (raised/opened/reviewed/closed or leave blank)", "")
    priority_filter = get_input("Priority Filter (low/medium/high/critical or leave blank)", "")
    
    params = {"limit": int(limit)}
    if status_filter:
        params["status_filter"] = status_filter
    if priority_filter:
        params["priority_filter"] = priority_filter
    
    print(f"\n{YELLOW}Fetching public feed...{RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/complaints/public", params=params)
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            complaints = data.get("complaints", [])
            print(f"\n{GREEN}Found {len(complaints)} public complaint(s){RESET}")
            
            print(f"\n{BOLD}{'#':<4} {'Title':<40} {'Status':<10} {'Priority':<10} {'Votes':<10}{RESET}")
            print(f"{CYAN}{'-'*80}{RESET}")
            
            for i, c in enumerate(complaints, 1):
                title = c['title'][:38]
                status = c['status'][:8]
                priority = c['priority'][:8]
                votes = f"↑{c['upvotes']} ↓{c['downvotes']}"
                
                print(f"{i:<4} {title:<40} {status:<10} {priority:<10} {votes:<10}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 4. VIEW COMPLAINT DETAILS
# ============================================

def view_complaint_details():
    """View full details of a complaint"""
    print_header("🔍 COMPLAINT DETAILS")
    
    # Show recent complaints
    if test_data["complaints"]:
        print(f"{BOLD}Recent complaints:{RESET}")
        for i, c in enumerate(test_data["complaints"][-5:], 1):
            print(f"  {i}. {c['title'][:50]} (ID: {c['id'][:8]}...)")
    
    complaint_id = get_input("\nComplaint ID", test_data.get("last_complaint_id", ""))
    
    if not complaint_id:
        print(f"{RED}No complaint ID provided{RESET}")
        pause()
        return
    
    print(f"\n{YELLOW}Fetching complaint details...{RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/complaints/{complaint_id}")
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            print(f"\n{BOLD}COMPLAINT DETAILS:{RESET}")
            print(f"  Title: {data['title']}")
            print(f"  Description: {data['description'][:100]}...")
            print(f"  Status: {data['status'].upper()}")
            print(f"  Priority: {data['priority'].upper()}")
            print(f"  Category: {data.get('category', 'N/A')}")
            print(f"  Student: {data['student']['name']} ({data['student']['roll_number']})")
            print(f"  Department: {data['student']['department']}")
            print(f"  Votes: ↑{data['upvotes']} ↓{data['downvotes']} (Net: {data['net_votes']})")
            print(f"  Assigned to: {data.get('assigned_authority', 'N/A')}")
            
            if data.get('llm_analysis'):
                llm = data['llm_analysis']
                print(f"\n{BOLD}AI ANALYSIS:{RESET}")
                print(f"  Summary: {llm.get('summary', 'N/A')}")
                print(f"  Urgency Score: {llm.get('urgency_score', 'N/A')}/100")
                print(f"  Impact Level: {llm.get('impact_level', 'N/A')}")
                print(f"  Sentiment: {llm.get('sentiment', 'N/A')}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 5. VOTE ON COMPLAINT
# ============================================

def vote_on_complaint():
    """Vote on a complaint"""
    print_header("🗳️  VOTE ON COMPLAINT")
    
    complaint_id = get_input("Complaint ID", test_data.get("last_complaint_id", ""))
    roll = get_input("Your Roll Number", "22CS888")
    
    print(f"\n{BOLD}Vote Type:{RESET}")
    print("  1. Upvote")
    print("  2. Downvote")
    vote_choice = get_input("Choose", "1")
    
    vote_type = "upvote" if vote_choice == "1" else "downvote"
    
    payload = {
        "complaint_id": complaint_id,
        "roll_number": roll,
        "vote_type": vote_type
    }
    
    print(f"\n{YELLOW}Submitting vote...{RESET}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/vote",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            print(f"\n{GREEN}✅ Vote recorded!{RESET}")
            print(f"   Action: {data.get('action')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Current Votes: ↑{data.get('upvotes')} ↓{data.get('downvotes')}")
            print(f"   Net Votes: {data.get('net_votes')}")
            
            if data.get('priority_updated'):
                print(f"\n{MAGENTA}📊 Priority auto-updated:{RESET}")
                print(f"   {data.get('old_priority')} → {data.get('new_priority')}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 6. GET VOTE STATISTICS
# ============================================

def get_vote_stats():
    """Get vote statistics for a complaint"""
    print_header("📊 VOTE STATISTICS")
    
    complaint_id = get_input("Complaint ID", test_data.get("last_complaint_id", ""))
    
    print(f"\n{YELLOW}Fetching vote statistics...{RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/votes/{complaint_id}")
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            print(f"\n{BOLD}VOTE STATISTICS:{RESET}")
            print(f"  Upvotes: {GREEN}{data.get('upvotes')}{RESET}")
            print(f"  Downvotes: {RED}{data.get('downvotes')}{RESET}")
            print(f"  Total Votes: {data.get('total')}")
            print(f"  Net Votes: {data.get('net_votes')}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 7. UPDATE COMPLAINT STATUS
# ============================================

def update_status():
    """Update complaint status"""
    print_header("⚙️  UPDATE COMPLAINT STATUS")
    
    complaint_id = get_input("Complaint ID", test_data.get("last_complaint_id", ""))
    
    print(f"\n{BOLD}New Status:{RESET}")
    print("  1. raised")
    print("  2. opened")
    print("  3. reviewed")
    print("  4. closed")
    status_choice = get_input("Choose", "2")
    
    status_map = {"1": "raised", "2": "opened", "3": "reviewed", "4": "closed"}
    new_status = status_map.get(status_choice, "opened")
    
    authority_roll = get_input("Authority Roll/ID", "ADMIN001")
    reason = get_input("Reason (optional)", "Status updated by authority")
    
    payload = {
        "complaint_id": complaint_id,
        "new_status": new_status,
        "updated_by_roll": authority_roll,
        "reason": reason
    }
    
    print(f"\n{YELLOW}Updating status...{RESET}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/status/update",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            print(f"\n{GREEN}✅ Status updated!{RESET}")
            print(f"   Old Status: {data.get('old_status')}")
            print(f"   New Status: {data.get('new_status')}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 8. VIEW OVERALL STATISTICS
# ============================================

def view_overall_stats():
    """View system-wide statistics"""
    print_header("📈 OVERALL SYSTEM STATISTICS")
    
    print(f"{YELLOW}Fetching statistics...{RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/stats")
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            print(f"\n{BOLD}SYSTEM OVERVIEW:{RESET}")
            print(f"  Total Students: {data.get('total_students', 0)}")
            print(f"  Total Complaints: {data.get('total_complaints', 0)}")
            print(f"  Total Votes: {data.get('total_votes', 0)}")
            
            status_breakdown = data.get('complaints_by_status', {})
            if status_breakdown:
                print(f"\n{BOLD}Complaints by Status:{RESET}")
                for status, count in status_breakdown.items():
                    print(f"  {status.upper()}: {count}")
            
            priority_breakdown = data.get('complaints_by_priority', {})
            if priority_breakdown:
                print(f"\n{BOLD}Complaints by Priority:{RESET}")
                for priority, count in priority_breakdown.items():
                    color = {
                        'low': GREEN,
                        'medium': YELLOW,
                        'high': MAGENTA,
                        'critical': RED
                    }.get(priority, RESET)
                    print(f"  {color}{priority.upper()}: {count}{RESET}")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# 9. HEALTH CHECK
# ============================================

def health_check():
    """Check API health"""
    print_header("💚 HEALTH CHECK")
    
    print(f"{YELLOW}Checking API health...{RESET}")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            print(f"\n{GREEN}✅ API is healthy!{RESET}")
            print(f"  Service: {data.get('service')}")
            print(f"  Version: {data.get('version')}")
            print(f"  Status: {data.get('status')}")
    
    except Exception as e:
        print(f"{RED}❌ API is down: {e}{RESET}")
    
    pause()

# ============================================
# 10. SEARCH COMPLAINTS
# ============================================

def search_complaints():
    """Search complaints by keyword"""
    print_header("🔎 SEARCH COMPLAINTS")
    
    query = get_input("Search Query", "")
    limit = get_input("Limit", "10")
    
    if not query:
        print(f"{RED}No search query provided{RESET}")
        pause()
        return
    
    print(f"\n{YELLOW}Searching...{RESET}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/search",
            params={"query": query, "limit": int(limit)}
        )
        
        data = print_response(response)
        
        if response.status_code == 200 and data:
            complaints = data.get("complaints", [])
            print(f"\n{GREEN}Found {len(complaints)} result(s){RESET}")
            
            for i, c in enumerate(complaints, 1):
                print(f"\n{BOLD}[{i}] {c['title']}{RESET}")
                print(f"    {c['description'][:80]}...")
    
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
    
    pause()

# ============================================
# MAIN MENU
# ============================================

def main_menu():
    """Display main menu"""
    while True:
        clear_screen()
        print_header("🎓 CAMPUSVOICE INTERACTIVE API TESTER")
        
        print(f"{CYAN}Server: {BASE_URL}{RESET}")
        if test_data.get("last_complaint_id"):
            print(f"{CYAN}Last Complaint: {test_data['last_complaint_id'][:16]}...{RESET}")
        
        print_menu("MAIN MENU", {
            "1": "📝 Submit Complaint",
            "2": "📋 View My Complaints",
            "3": "📰 View Public Feed",
            "4": "🔍 View Complaint Details",
            "5": "🗳️  Vote on Complaint",
            "6": "📊 Get Vote Statistics",
            "7": "⚙️  Update Complaint Status",
            "8": "📈 View Overall Statistics",
            "9": "🔎 Search Complaints",
            "10": "💚 Health Check",
            "0": "❌ Exit"
        })
        
        choice = get_input("\nSelect option", "1")
        
        if choice == "1":
            submit_complaint()
        elif choice == "2":
            view_my_complaints()
        elif choice == "3":
            view_public_feed()
        elif choice == "4":
            view_complaint_details()
        elif choice == "5":
            vote_on_complaint()
        elif choice == "6":
            get_vote_stats()
        elif choice == "7":
            update_status()
        elif choice == "8":
            view_overall_stats()
        elif choice == "9":
            search_complaints()
        elif choice == "10":
            health_check()
        elif choice == "0":
            print(f"\n{GREEN}Goodbye!{RESET}\n")
            break
        else:
            print(f"{RED}Invalid option{RESET}")
            pause()

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Exited by user{RESET}\n")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}\n")
        import traceback
        traceback.print_exc()
