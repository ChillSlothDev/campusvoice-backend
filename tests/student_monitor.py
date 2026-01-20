"""
Student Complaint Monitor
Continuously monitors complaint status and displays updates
"""

import requests
import json
import time
from datetime import datetime
import os
import sys

BASE_URL = "http://localhost:8000/api"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
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

class StudentMonitor:
    """Monitor student complaints in real-time"""
    
    def __init__(self):
        self.roll_number = None
        self.student_name = None
        self.last_status = {}
        self.refresh_interval = 5  # seconds
    
    def setup(self):
        """Setup student details"""
        clear_screen()
        print_header("📱 CAMPUSVOICE STUDENT MONITOR")
        
        print(f"{CYAN}Real-time monitoring of your complaints{RESET}\n")
        
        self.student_name = input(f"{YELLOW}Enter your name: {RESET}").strip()
        self.roll_number = input(f"{YELLOW}Enter your roll number: {RESET}").strip()
        
        if not self.student_name or not self.roll_number:
            print(f"{RED}❌ Name and roll number are required!{RESET}")
            return False
        
        try:
            interval = input(f"{YELLOW}Refresh interval in seconds (default: 5): {RESET}").strip()
            if interval:
                self.refresh_interval = int(interval)
        except:
            self.refresh_interval = 5
        
        print(f"{GREEN}✅ Monitoring started for {self.student_name} ({self.roll_number}){RESET}")
        time.sleep(1)
        return True
    
    def get_my_complaints(self):
        """Fetch student's complaints"""
        try:
            response = requests.get(
                f"{BASE_URL}/complaints/my",
                params={"roll_number": self.roll_number}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('complaints', [])
            else:
                return []
        except Exception as e:
            print(f"{RED}❌ Error fetching complaints: {e}{RESET}")
            return []
    
    def detect_changes(self, complaints):
        """Detect status changes in complaints"""
        changes = []
        
        for complaint in complaints:
            complaint_id = complaint.get('complaint_id')
            current_status = complaint.get('status')
            current_upvotes = complaint.get('upvotes', 0)
            current_downvotes = complaint.get('downvotes', 0)
            
            if complaint_id in self.last_status:
                old_data = self.last_status[complaint_id]
                
                # Check status change
                if old_data['status'] != current_status:
                    changes.append({
                        'type': 'status',
                        'complaint_id': complaint_id,
                        'title': complaint.get('title'),
                        'old_status': old_data['status'],
                        'new_status': current_status
                    })
                
                # Check vote changes
                if (old_data['upvotes'] != current_upvotes or 
                    old_data['downvotes'] != current_downvotes):
                    changes.append({
                        'type': 'votes',
                        'complaint_id': complaint_id,
                        'title': complaint.get('title'),
                        'old_upvotes': old_data['upvotes'],
                        'new_upvotes': current_upvotes,
                        'old_downvotes': old_data['downvotes'],
                        'new_downvotes': current_downvotes
                    })
            
            # Update last status
            self.last_status[complaint_id] = {
                'status': current_status,
                'upvotes': current_upvotes,
                'downvotes': current_downvotes
            }
        
        return changes
    
    def display_complaints(self, complaints):
        """Display complaints table"""
        if not complaints:
            print(f"{YELLOW}⚠️  No complaints found for {self.roll_number}{RESET}")
            return
        
        print(f"{BOLD}{CYAN}{'Title':<35} {'Status':<12} {'Priority':<10} {'Votes':<12}{RESET}")
        print(f"{CYAN}{'-'*75}{RESET}")
        
        for complaint in complaints:
            title = complaint.get('title', 'N/A')[:33]
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
                'high': CYAN,
                'critical': RED
            }.get(priority, RESET)
            
            votes = f"↑{upvotes} ↓{downvotes}"
            
            print(f"{title:<35} {status_color}{status:<12}{RESET} {priority_color}{priority:<10}{RESET} {GREEN}{votes:<12}{RESET}")
    
    def show_notification(self, changes):
        """Show notification for changes"""
        if not changes:
            return
        
        print(f"\n{BOLD}{CYAN}{'🔔 UPDATES DETECTED!'}{RESET}")
        print(f"{CYAN}{'─'*70}{RESET}")
        
        for change in changes:
            if change['type'] == 'status':
                print(f"{YELLOW}📊 Status Changed:{RESET}")
                print(f"   Complaint: {change['title'][:50]}")
                print(f"   {change['old_status'].upper()} → {GREEN}{change['new_status'].upper()}{RESET}")
            
            elif change['type'] == 'votes':
                print(f"{GREEN}🗳️  Vote Update:{RESET}")
                print(f"   Complaint: {change['title'][:50]}")
                upvote_change = change['new_upvotes'] - change['old_upvotes']
                downvote_change = change['new_downvotes'] - change['old_downvotes']
                
                if upvote_change > 0:
                    print(f"   {GREEN}+{upvote_change} upvote(s){RESET}")
                if downvote_change > 0:
                    print(f"   {RED}+{downvote_change} downvote(s){RESET}")
                print(f"   Total: ↑{change['new_upvotes']} ↓{change['new_downvotes']}")
        
        print(f"{CYAN}{'─'*70}{RESET}")
    
    def run(self):
        """Main monitoring loop"""
        if not self.setup():
            return
        
        iteration = 0
        
        try:
            while True:
                clear_screen()
                
                # Header
                print_header(f"📱 STUDENT MONITOR - {self.student_name}")
                print(f"{CYAN}Roll Number: {self.roll_number}{RESET}")
                print(f"{CYAN}Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
                print(f"{CYAN}Auto-refresh: Every {self.refresh_interval}s{RESET}")
                print(f"{CYAN}Press Ctrl+C to stop{RESET}\n")
                
                # Fetch complaints
                complaints = self.get_my_complaints()
                
                # Detect changes
                changes = self.detect_changes(complaints)
                
                # Show notifications
                if iteration > 0 and changes:  # Skip first iteration
                    self.show_notification(changes)
                
                # Display current complaints
                print(f"\n{BOLD}📋 YOUR COMPLAINTS ({len(complaints)} total){RESET}\n")
                self.display_complaints(complaints)
                
                # Progress indicator
                print(f"\n{YELLOW}Next refresh in: {RESET}", end='', flush=True)
                for i in range(self.refresh_interval, 0, -1):
                    print(f"{i}s ", end='', flush=True)
                    time.sleep(1)
                
                iteration += 1
        
        except KeyboardInterrupt:
            print(f"\n\n{GREEN}✅ Monitoring stopped{RESET}")


if __name__ == "__main__":
    monitor = StudentMonitor()
    monitor.run()
