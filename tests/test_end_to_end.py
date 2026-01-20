"""
End-to-End Test Script
1. Student submits complaint
2. Gets complaint ID
3. Authority views complaint
4. Authority changes status
5. Student checks if status reflected
"""

import requests
import json
import time
from datetime import datetime
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

def print_header(text):
    """Print styled header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{text:^70}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_section(text):
    """Print section header"""
    print(f"\n{CYAN}{'─'*70}{RESET}")
    print(f"{CYAN}{BOLD}{text}{RESET}")
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

def print_step(number, text):
    """Print step number"""
    print(f"\n{MAGENTA}{BOLD}STEP {number}: {text}{RESET}")

def pause(message="Press Enter to continue..."):
    """Pause execution"""
    input(f"\n{YELLOW}{message}{RESET}")


class EndToEndTest:
    """Complete end-to-end workflow test"""
    
    def __init__(self):
        self.student_name = None
        self.student_roll = None
        self.authority_name = None
        self.authority_roll = None
        self.complaint_id = None
        self.complaint_data = None
    
    def setup_student(self):
        """Setup student details"""
        print_header("👨‍🎓 STUDENT SETUP")
        
        self.student_name = input(f"{YELLOW}Enter student name: {RESET}").strip() or "Arun Kumar"
        self.student_roll = input(f"{YELLOW}Enter student roll number: {RESET}").strip() or "22CS045"
        
        print_success(f"Student: {self.student_name} ({self.student_roll})")
    
    def setup_authority(self):
        """Setup authority details"""
        print_header("🏛️  AUTHORITY SETUP")
        
        self.authority_name = input(f"{YELLOW}Enter authority name: {RESET}").strip() or "Dr. Rajesh"
        self.authority_roll = input(f"{YELLOW}Enter authority ID: {RESET}").strip() or "ADMIN001"
        
        print_success(f"Authority: {self.authority_name} ({self.authority_roll})")
    
    def student_submit_complaint(self):
        """Student submits a complaint"""
        print_step(1, "STUDENT SUBMITS COMPLAINT")
        
        # Get complaint details
        print(f"\n{CYAN}Enter complaint details:{RESET}")
        
        title = input(f"{YELLOW}Title (or Enter for default): {RESET}").strip()
        if not title:
            title = f"Test Complaint - {datetime.now().strftime('%H:%M:%S')}"
        
        description = input(f"{YELLOW}Description (or Enter for default): {RESET}").strip()
        if not description:
            description = f"This is an automated end-to-end test complaint submitted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Testing the complete workflow from submission to status update."
        
        department = input(f"{YELLOW}Department (default: CSE): {RESET}").strip() or "CSE"
        
        # Prepare complaint data
        complaint_data = {
            "name": self.student_name,
            "register_number": self.student_roll,
            "department": department,
            "stay_type": "Hostel",
            "visibility": "Public",
            "title": title,
            "description": description,
            "image_url": None
        }
        
        print_info("Submitting complaint...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/complaints",
                json=complaint_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.complaint_id = data.get("complaint_id")
                
                print_success("Complaint submitted successfully!")
                print(f"\n{BOLD}Complaint Details:{RESET}")
                print(f"  ID: {CYAN}{self.complaint_id}{RESET}")
                print(f"  Title: {data.get('title')}")
                print(f"  Priority: {data.get('priority').upper()}")
                print(f"  Category: {data.get('category')}")
                print(f"  Status: {YELLOW}{data.get('status', 'raised').upper()}{RESET}")
                print(f"  Assigned to: {data.get('assigned_to')}")
                print(f"  Authority Email: {data.get('authority_email')}")
                
                # Store initial data
                self.complaint_data = {
                    'title': title,
                    'initial_status': data.get('status', 'raised'),
                    'priority': data.get('priority'),
                    'category': data.get('category')
                }
                
                return True
            else:
                print_error(f"Failed to submit complaint: {response.status_code}")
                print(response.text)
                return False
        
        except Exception as e:
            print_error(f"Error submitting complaint: {e}")
            return False
    
    def student_check_complaint(self, show_full_details=False):
        """Student checks their complaint"""
        if not self.complaint_id:
            print_error("No complaint ID available")
            return None
        
        try:
            response = requests.get(f"{BASE_URL}/complaints/{self.complaint_id}")
            
            if response.status_code == 200:
                complaint = response.json()
                
                if show_full_details:
                    print(f"\n{BOLD}Full Complaint Details:{RESET}")
                    print(json.dumps(complaint, indent=2))
                else:
                    print(f"\n{BOLD}Complaint Status:{RESET}")
                    print(f"  ID: {complaint.get('complaint_id')}")
                    print(f"  Title: {complaint.get('title')}")
                    print(f"  Status: {self._colorize_status(complaint.get('status'))}")
                    print(f"  Priority: {complaint.get('priority').upper()}")
                    print(f"  Upvotes: {GREEN}{complaint.get('upvotes')}{RESET}")
                    print(f"  Downvotes: {RED}{complaint.get('downvotes')}{RESET}")
                
                return complaint
            else:
                print_error(f"Failed to fetch complaint: {response.status_code}")
                return None
        
        except Exception as e:
            print_error(f"Error fetching complaint: {e}")
            return None
    
    def authority_view_complaint(self):
        """Authority views the complaint"""
        print_step(2, "AUTHORITY VIEWS COMPLAINT")
        
        print_info(f"Authority ({self.authority_name}) is viewing complaint...")
        
        complaint = self.student_check_complaint(show_full_details=False)
        
        if complaint:
            print_success("Authority can see the complaint")
            
            # Show LLM analysis if available
            llm_analysis = complaint.get('llm_analysis')
            if llm_analysis:
                print(f"\n{BOLD}🤖 AI Analysis:{RESET}")
                print(f"  Summary: {llm_analysis.get('summary', 'N/A')}")
                print(f"  Urgency: {llm_analysis.get('urgency_score', 0)}/100")
                print(f"  Impact: {llm_analysis.get('impact_level', 'N/A')}")
                
                key_issues = llm_analysis.get('key_issues', [])
                if key_issues:
                    print(f"  Key Issues:")
                    for issue in key_issues:
                        print(f"    • {issue}")
            
            return True
        else:
            return False
    
    def authority_change_status(self):
        """Authority changes complaint status"""
        print_step(3, "AUTHORITY CHANGES STATUS")
        
        if not self.complaint_id:
            print_error("No complaint ID available")
            return False
        
        # Get current status
        complaint = self.student_check_complaint(show_full_details=False)
        if not complaint:
            return False
        
        current_status = complaint.get('status')
        
        print(f"\n{BOLD}Current Status:{RESET} {self._colorize_status(current_status)}")
        
        # Show available status options
        statuses = ['raised', 'opened', 'reviewed', 'closed']
        print(f"\n{BOLD}Available Statuses:{RESET}")
        for idx, status in enumerate(statuses, 1):
            color = GREEN if status != current_status else YELLOW
            marker = "✓" if status == current_status else " "
            print(f"  {idx}. [{marker}] {color}{status.upper()}{RESET}")
        
        # Get new status
        choice = input(f"\n{YELLOW}Select new status (1-{len(statuses)}): {RESET}").strip()
        
        try:
            choice_num = int(choice)
            if choice_num < 1 or choice_num > len(statuses):
                print_error("Invalid choice")
                return False
            
            new_status = statuses[choice_num - 1]
            
            if new_status == current_status:
                print_info("Status is already set to this value. Continuing anyway for demo...")
            
            reason = input(f"{YELLOW}Reason for status change (optional): {RESET}").strip()
            if not reason:
                reason = f"Status updated by {self.authority_name} during workflow test"
            
            print_info("Updating status...")
            
            # Since we don't have the status update endpoint yet, 
            # we'll use a workaround by directly updating via db_service
            # For now, let's simulate and show what would happen
            
            print(f"\n{BOLD}Update Request:{RESET}")
            print(f"  Complaint ID: {self.complaint_id}")
            print(f"  Old Status: {self._colorize_status(current_status)}")
            print(f"  New Status: {self._colorize_status(new_status)}")
            print(f"  Updated By: {self.authority_name} ({self.authority_roll})")
            print(f"  Reason: {reason}")
            
            # Store for verification
            self.complaint_data['old_status'] = current_status
            self.complaint_data['new_status'] = new_status
            self.complaint_data['update_reason'] = reason
            
            # Simulate API call (you'll need to implement this endpoint)
            update_data = {
                "complaint_id": self.complaint_id,
                "new_status": new_status,
                "updated_by_roll": self.authority_roll,
                "reason": reason
            }
            
            # Try to call the endpoint (may not exist yet)
            try:
                response = requests.post(
                    f"{BASE_URL}/status/update",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    print_success("Status updated via API!")
                    return True
                else:
                    print_info(f"API endpoint returned: {response.status_code}")
                    print_info("Simulating manual update...")
            except:
                print_info("Status update endpoint not available yet")
                print_info("You'll need to manually update in database or Swagger UI")
            
            # Instruction for manual update
            print(f"\n{YELLOW}{'─'*70}{RESET}")
            print(f"{YELLOW}MANUAL UPDATE REQUIRED:{RESET}")
            print(f"{YELLOW}Since the status update endpoint is not available,{RESET}")
            print(f"{YELLOW}please manually update the status using one of these methods:{RESET}")
            print(f"\n{CYAN}Option 1: Using pgAdmin/SQL:{RESET}")
            print(f"{GREEN}UPDATE complaints SET status = '{new_status}' WHERE id = '{self.complaint_id}';{RESET}")
            print(f"\n{CYAN}Option 2: Continue test to verify current behavior{RESET}")
            print(f"{YELLOW}{'─'*70}{RESET}")
            
            return True
        
        except ValueError:
            print_error("Invalid input")
            return False
    
    def student_verify_status_change(self):
        """Student verifies if status was changed"""
        print_step(4, "STUDENT VERIFIES STATUS CHANGE")
        
        print_info(f"Student ({self.student_name}) is checking complaint status...")
        
        # Wait a moment
        print_info("Waiting for changes to propagate...")
        time.sleep(2)
        
        # Fetch current complaint
        complaint = self.student_check_complaint(show_full_details=False)
        
        if not complaint:
            return False
        
        current_status = complaint.get('status')
        expected_status = self.complaint_data.get('new_status')
        old_status = self.complaint_data.get('old_status')
        
        print(f"\n{BOLD}Verification Results:{RESET}")
        print(f"  Original Status: {self._colorize_status(old_status)}")
        print(f"  Expected Status: {self._colorize_status(expected_status)}")
        print(f"  Current Status: {self._colorize_status(current_status)}")
        
        if current_status == expected_status:
            print_success("✅ STATUS CHANGE REFLECTED SUCCESSFULLY!")
            print(f"{GREEN}The complaint status has been updated as expected.{RESET}")
            return True
        else:
            print_error("❌ STATUS CHANGE NOT REFLECTED")
            print(f"{RED}The status was not updated. This might be because:{RESET}")
            print(f"{RED}1. The status update endpoint is not implemented{RESET}")
            print(f"{RED}2. The database was not manually updated{RESET}")
            print(f"{RED}3. There was an error in the update process{RESET}")
            return False
    
    def _colorize_status(self, status):
        """Return colorized status string"""
        color_map = {
            'raised': YELLOW,
            'opened': BLUE,
            'reviewed': CYAN,
            'closed': GREEN
        }
        color = color_map.get(status, RESET)
        return f"{color}{status.upper()}{RESET}"
    
    def run_test(self):
        """Run complete end-to-end test"""
        print_header("🧪 END-TO-END WORKFLOW TEST")
        print(f"{CYAN}This test will:{RESET}")
        print(f"  1. Student submits a complaint")
        print(f"  2. Authority views the complaint")
        print(f"  3. Authority changes status")
        print(f"  4. Student verifies status change")
        print()
        
        # Setup
        self.setup_student()
        self.setup_authority()
        
        pause()
        
        # Step 1: Student submits complaint
        if not self.student_submit_complaint():
            print_error("Test failed at Step 1")
            return False
        
        pause()
        
        # Step 2: Authority views complaint
        if not self.authority_view_complaint():
            print_error("Test failed at Step 2")
            return False
        
        pause()
        
        # Step 3: Authority changes status
        if not self.authority_change_status():
            print_error("Test failed at Step 3")
            return False
        
        pause()
        
        # Step 4: Student verifies status change
        result = self.student_verify_status_change()
        
        # Final summary
        print_header("📊 TEST SUMMARY")
        
        print(f"{BOLD}Student:{RESET} {self.student_name} ({self.student_roll})")
        print(f"{BOLD}Authority:{RESET} {self.authority_name} ({self.authority_roll})")
        print(f"{BOLD}Complaint ID:{RESET} {self.complaint_id}")
        print(f"{BOLD}Title:{RESET} {self.complaint_data.get('title')}")
        
        if result:
            print(f"\n{GREEN}{BOLD}{'='*70}{RESET}")
            print(f"{GREEN}{BOLD}✅ TEST PASSED: Status change workflow working correctly!{RESET}")
            print(f"{GREEN}{BOLD}{'='*70}{RESET}")
        else:
            print(f"\n{YELLOW}{BOLD}{'='*70}{RESET}")
            print(f"{YELLOW}{BOLD}⚠️  TEST INCOMPLETE: Status update needs to be implemented{RESET}")
            print(f"{YELLOW}{BOLD}{'='*70}{RESET}")
            
            print(f"\n{CYAN}To complete this test:{RESET}")
            print(f"1. Implement the status update endpoint in routes.py")
            print(f"2. OR manually update the database")
            print(f"3. Re-run the verification step")
        
        return result


def main():
    """Main entry point"""
    test = EndToEndTest()
    
    try:
        test.run_test()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
