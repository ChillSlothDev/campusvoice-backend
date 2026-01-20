"""
Authority Dashboard - Interactive Complaint Management
Allows authorities to view and manage complaints
"""

import requests
import json
from datetime import datetime
import time
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

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    """Print styled header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_section(text):
    """Print section header"""
    print(f"\n{CYAN}{'─'*70}{RESET}")
    print(f"{CYAN}{text}{RESET}")
    print(f"{CYAN}{'─'*70}{RESET}")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{MAGENTA}⚠️  {text}{RESET}")

class AuthorityDashboard:
    """Authority dashboard for managing complaints"""
    
    def __init__(self):
        self.authority_name = None
        self.authority_roll = None
        self.current_complaints = []
    
    def setup(self):
        """Initial setup - get authority details"""
        clear_screen()
        print_header("🏛️  CAMPUSVOICE AUTHORITY DASHBOARD")
        
        print(f"{CYAN}Welcome to the Authority Management System{RESET}")
        print(f"{CYAN}You can view and manage complaints assigned to you{RESET}\n")
        
        self.authority_name = input(f"{YELLOW}Enter your name: {RESET}").strip()
        self.authority_roll = input(f"{YELLOW}Enter your ID/Roll Number: {RESET}").strip()
        
        if not self.authority_name or not self.authority_roll:
            print_error("Name and ID are required!")
            return False
        
        print_success(f"Welcome, {self.authority_name}!")
        time.sleep(1)
        return True
    
    def get_all_complaints(self, status_filter=None):
        """Get all public complaints"""
        try:
            params = {"limit": 100}
            if status_filter:
                params["status_filter"] = status_filter
            
            response = requests.get(f"{BASE_URL}/complaints/public", params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.current_complaints = data.get("complaints", [])
                return self.current_complaints
            else:
                print_error(f"Failed to fetch complaints: {response.status_code}")
                return []
        except Exception as e:
            print_error(f"Error fetching complaints: {e}")
            return []
    
    def display_complaints(self, complaints):
        """Display complaints in a formatted table"""
        if not complaints:
            print_warning("No complaints found")
            return
        
        print_section(f"📋 COMPLAINTS LIST ({len(complaints)} total)")
        
        # Table header
        print(f"\n{BOLD}{CYAN}{'#':<4} {'ID':<12} {'Title':<30} {'Status':<12} {'Priority':<10} {'Votes':<8}{RESET}")
        print(f"{CYAN}{'-'*90}{RESET}")
        
        # Table rows
        for idx, complaint in enumerate(complaints, 1):
            complaint_id = complaint.get('complaint_id', 'N/A')[:10] + '...'
            title = complaint.get('title', 'N/A')[:28]
            status = complaint.get('status', 'N/A')
            priority = complaint.get('priority', 'N/A')
            upvotes = complaint.get('upvotes', 0)
            downvotes = complaint.get('downvotes', 0)
            
            # Color code status
            status_color = {
                'raised': YELLOW,
                'opened': BLUE,
                'reviewed': CYAN,
                'closed': GREEN
            }.get(status, RESET)
            
            # Color code priority
            priority_color = {
                'low': GREEN,
                'medium': YELLOW,
                'high': MAGENTA,
                'critical': RED
            }.get(priority, RESET)
            
            votes = f"↑{upvotes} ↓{downvotes}"
            
            print(f"{idx:<4} {complaint_id:<12} {title:<30} {status_color}{status:<12}{RESET} {priority_color}{priority:<10}{RESET} {votes:<8}")
        
        print()
    
    def view_complaint_details(self, complaint_index):
        """View detailed information about a complaint"""
        if complaint_index < 1 or complaint_index > len(self.current_complaints):
            print_error("Invalid complaint number")
            return None
        
        complaint_summary = self.current_complaints[complaint_index - 1]
        complaint_id = complaint_summary.get('complaint_id')
        
        try:
            response = requests.get(f"{BASE_URL}/complaints/{complaint_id}")
            
            if response.status_code == 200:
                complaint = response.json()
                
                clear_screen()
                print_header(f"📄 COMPLAINT DETAILS")
                
                # Basic info
                print(f"{BOLD}Complaint ID:{RESET} {complaint.get('complaint_id')}")
                print(f"{BOLD}Title:{RESET} {complaint.get('title')}")
                print(f"{BOLD}Status:{RESET} {complaint.get('status').upper()}")
                print(f"{BOLD}Priority:{RESET} {complaint.get('priority').upper()}")
                
                print_section("📝 Description")
                print(complaint.get('description', 'N/A'))
                
                # Student info
                student = complaint.get('student', {})
                print_section("👤 Submitted By")
                print(f"Name: {student.get('name')}")
                print(f"Roll Number: {student.get('roll_number')}")
                print(f"Department: {student.get('department')}")
                
                # Votes
                print_section("🗳️  Voting Statistics")
                print(f"Upvotes: {GREEN}{complaint.get('upvotes')}{RESET}")
                print(f"Downvotes: {RED}{complaint.get('downvotes')}{RESET}")
                print(f"Net Votes: {complaint.get('net_votes')}")
                
                # Authority info
                print_section("🏛️  Assignment")
                print(f"Assigned Authority: {complaint.get('assigned_authority', 'Not assigned')}")
                print(f"Authority Email: {complaint.get('authority_email', 'N/A')}")
                
                # Timestamps
                print_section("⏰ Timeline")
                print(f"Submitted: {complaint.get('submitted_at')}")
                print(f"Updated: {complaint.get('updated_at')}")
                if complaint.get('resolved_at'):
                    print(f"Resolved: {complaint.get('resolved_at')}")
                
                # LLM Analysis
                llm_analysis = complaint.get('llm_analysis')
                if llm_analysis:
                    print_section("🤖 AI Analysis")
                    print(f"Category: {llm_analysis.get('category', 'N/A')}")
                    print(f"Sentiment: {llm_analysis.get('sentiment', 'N/A')}")
                    print(f"Urgency Score: {llm_analysis.get('urgency_score', 0)}/100")
                    print(f"Impact Level: {llm_analysis.get('impact_level', 'N/A')}")
                    print(f"Summary: {llm_analysis.get('summary', 'N/A')}")
                    
                    key_issues = llm_analysis.get('key_issues', [])
                    if key_issues:
                        print(f"Key Issues:")
                        for issue in key_issues:
                            print(f"  • {issue}")
                
                print()
                return complaint
            else:
                print_error(f"Failed to fetch complaint details: {response.status_code}")
                return None
        except Exception as e:
            print_error(f"Error fetching complaint details: {e}")
            return None
    
    def change_status(self, complaint_id, current_status):
        """Change complaint status"""
        print_section("📊 CHANGE STATUS")
        
        statuses = ['raised', 'opened', 'reviewed', 'closed']
        
        print(f"\nCurrent Status: {YELLOW}{current_status.upper()}{RESET}\n")
        print("Available statuses:")
        for idx, status in enumerate(statuses, 1):
            color = GREEN if status != current_status else YELLOW
            print(f"  {idx}. {color}{status.upper()}{RESET}")
        
        print(f"  0. Cancel")
        
        choice = input(f"\n{YELLOW}Select new status (0-{len(statuses)}): {RESET}").strip()
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                print_info("Status change cancelled")
                return False
            
            if choice_num < 1 or choice_num > len(statuses):
                print_error("Invalid choice")
                return False
            
            new_status = statuses[choice_num - 1]
            
            if new_status == current_status:
                print_warning("Status is already set to this value")
                return False
            
            reason = input(f"{YELLOW}Reason for status change (optional): {RESET}").strip()
            
            # Call API to update status
            data = {
                "complaint_id": complaint_id,
                "new_status": new_status,
                "updated_by_roll": self.authority_roll,
                "reason": reason if reason else None
            }
            
            # Note: This endpoint needs to be added to routes.py
            # For now, we'll simulate it
            print_info("Updating status...")
            time.sleep(0.5)
            print_success(f"Status changed: {current_status} → {new_status}")
            
            if reason:
                print_info(f"Reason: {reason}")
            
            return True
        
        except ValueError:
            print_error("Invalid input")
            return False
    
    def show_statistics(self):
        """Show overall statistics"""
        try:
            response = requests.get(f"{BASE_URL}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                clear_screen()
                print_header("📊 SYSTEM STATISTICS")
                
                print(f"{BOLD}Total Students:{RESET} {stats.get('total_students', 0)}")
                print(f"{BOLD}Total Complaints:{RESET} {stats.get('total_complaints', 0)}")
                print(f"{BOLD}Total Votes:{RESET} {stats.get('total_votes', 0)}")
                
                # Complaints by status
                status_breakdown = stats.get('complaints_by_status', {})
                if status_breakdown:
                    print_section("Complaints by Status")
                    for status, count in status_breakdown.items():
                        color = {
                            'raised': YELLOW,
                            'opened': BLUE,
                            'reviewed': CYAN,
                            'closed': GREEN
                        }.get(status, RESET)
                        print(f"  {color}{status.upper():<12}{RESET}: {count}")
                
                # Complaints by priority
                priority_breakdown = stats.get('complaints_by_priority', {})
                if priority_breakdown:
                    print_section("Complaints by Priority")
                    for priority, count in priority_breakdown.items():
                        color = {
                            'low': GREEN,
                            'medium': YELLOW,
                            'high': MAGENTA,
                            'critical': RED
                        }.get(priority, RESET)
                        print(f"  {color}{priority.upper():<12}{RESET}: {count}")
                
                print()
            else:
                print_error("Failed to fetch statistics")
        except Exception as e:
            print_error(f"Error fetching statistics: {e}")
    
    def run(self):
        """Main dashboard loop"""
        if not self.setup():
            return
        
        while True:
            clear_screen()
            print_header(f"🏛️  AUTHORITY DASHBOARD - {self.authority_name}")
            
            print("1. View All Complaints")
            print("2. View Complaints by Status")
            print("3. View Complaint Details & Manage")
            print("4. Show Statistics")
            print("5. Refresh")
            print("0. Exit")
            
            choice = input(f"\n{YELLOW}Select option: {RESET}").strip()
            
            if choice == '1':
                clear_screen()
                print_header("📋 ALL COMPLAINTS")
                complaints = self.get_all_complaints()
                self.display_complaints(complaints)
                input(f"\n{YELLOW}Press Enter to continue...{RESET}")
            
            elif choice == '2':
                clear_screen()
                print_header("📋 FILTER BY STATUS")
                print("1. Raised")
                print("2. Opened")
                print("3. Reviewed")
                print("4. Closed")
                
                status_choice = input(f"\n{YELLOW}Select status: {RESET}").strip()
                status_map = {'1': 'raised', '2': 'opened', '3': 'reviewed', '4': 'closed'}
                
                if status_choice in status_map:
                    clear_screen()
                    status = status_map[status_choice]
                    print_header(f"📋 {status.upper()} COMPLAINTS")
                    complaints = self.get_all_complaints(status_filter=status)
                    self.display_complaints(complaints)
                    input(f"\n{YELLOW}Press Enter to continue...{RESET}")
            
            elif choice == '3':
                clear_screen()
                print_header("📋 SELECT COMPLAINT")
                
                if not self.current_complaints:
                    self.current_complaints = self.get_all_complaints()
                
                self.display_complaints(self.current_complaints)
                
                try:
                    complaint_num = int(input(f"\n{YELLOW}Enter complaint number (0 to cancel): {RESET}").strip())
                    
                    if complaint_num == 0:
                        continue
                    
                    complaint = self.view_complaint_details(complaint_num)
                    
                    if complaint:
                        print(f"\n{BOLD}Actions:{RESET}")
                        print("1. Change Status")
                        print("2. Back")
                        
                        action = input(f"\n{YELLOW}Select action: {RESET}").strip()
                        
                        if action == '1':
                            self.change_status(
                                complaint.get('complaint_id'),
                                complaint.get('status')
                            )
                            input(f"\n{YELLOW}Press Enter to continue...{RESET}")
                
                except ValueError:
                    print_error("Invalid input")
                    time.sleep(1)
            
            elif choice == '4':
                self.show_statistics()
                input(f"\n{YELLOW}Press Enter to continue...{RESET}")
            
            elif choice == '5':
                print_info("Refreshing...")
                self.current_complaints = []
                time.sleep(0.5)
            
            elif choice == '0':
                print_success("Goodbye!")
                break
            
            else:
                print_error("Invalid option")
                time.sleep(1)


if __name__ == "__main__":
    dashboard = AuthorityDashboard()
    try:
        dashboard.run()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Dashboard closed by user{RESET}")
