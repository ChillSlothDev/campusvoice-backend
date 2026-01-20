"""
AI CLASSIFICATION TEST SUITE
============================
Tests AI's ability to correctly classify complaints into:
- infrastructure
- food
- hostel
- academic
- transport
- disciplinary

Each complaint is designed to clearly fit one category.
"""

import requests
import json
import time
from datetime import datetime

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
    print(f"\n{BLUE}{'='*100}{RESET}")
    print(f"{BLUE}{BOLD}{text:^100}{RESET}")
    print(f"{BLUE}{'='*100}{RESET}\n")

def print_test(number, total, category):
    print(f"\n{MAGENTA}{BOLD}[TEST {number}/{total}] CATEGORY: {category.upper()}{RESET}")

def print_result(expected, actual, correct):
    if correct:
        print(f"   ✅ Expected: {expected:<20} | Actual: {GREEN}{actual:<20}{RESET} | {GREEN}CORRECT{RESET}")
    else:
        print(f"   ❌ Expected: {expected:<20} | Actual: {RED}{actual:<20}{RESET} | {RED}WRONG{RESET}")

# ============================================
# TEST COMPLAINTS BY CATEGORY
# ============================================

test_complaints = [
    # ========================================
    # INFRASTRUCTURE COMPLAINTS (5)
    # ========================================
    {
        "category": "infrastructure",
        "name": "Rajesh Kumar",
        "register_number": "22CS101",
        "department": "CSE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Classroom projector not working in CSE Block",
        "description": "The projector in classroom 301 CSE block has been broken for one week. Faculty cannot conduct presentations and students are missing important lecture content. This is affecting daily classes for 60+ students.",
        "expected_authority": "Maintenance Officer",
        "expected_priority": "high"
    },
    {
        "category": "infrastructure",
        "name": "Priya Menon",
        "register_number": "22EC102",
        "department": "ECE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Water cooler not functioning in ECE department",
        "description": "The water cooler on the second floor ECE block stopped working three days ago. Students have no access to drinking water during class hours in hot weather. Urgent repair needed.",
        "expected_authority": "Maintenance Officer",
        "expected_priority": "medium"
    },
    {
        "category": "infrastructure",
        "name": "Amit Patel",
        "register_number": "22ME103",
        "department": "MECH",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Broken ceiling fan in workshop causing safety hazard",
        "description": "One of the ceiling fans in the mechanical workshop is wobbling dangerously and making loud noise. This poses a safety risk to students working below. Immediate attention required before an accident occurs.",
        "expected_authority": "Maintenance Officer",
        "expected_priority": "critical"
    },
    {
        "category": "infrastructure",
        "name": "Sneha Reddy",
        "register_number": "22IT104",
        "department": "IT",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Air conditioning not working in computer lab",
        "description": "The central AC in computer lab 1 has been malfunctioning for five days. The room temperature reaches 35°C, making it unbearable for students during practical sessions. Multiple computers are overheating.",
        "expected_authority": "Maintenance Officer",
        "expected_priority": "high"
    },
    {
        "category": "infrastructure",
        "name": "Karthik Sharma",
        "register_number": "22EE105",
        "department": "EEE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Toilet plumbing issues in main building",
        "description": "Two toilets on the ground floor main building have been clogged for three days. Only one functional toilet for 200+ students. Causing hygiene issues and long queues during breaks.",
        "expected_authority": "Maintenance Officer",
        "expected_priority": "high"
    },
    
    # ========================================
    # FOOD/MESS COMPLAINTS (5)
    # ========================================
    {
        "category": "food",
        "name": "Deepak Verma",
        "register_number": "22CS201",
        "department": "CSE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Undercooked rice served in mess daily",
        "description": "The rice served in mess for the past week has been consistently undercooked and hard. Many students are getting stomach aches. The quality of staple food is unacceptable and affecting student health.",
        "expected_authority": "Mess Committee Head",
        "expected_priority": "medium"
    },
    {
        "category": "food",
        "name": "Ananya Singh",
        "register_number": "22EC202",
        "department": "ECE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Unhygienic conditions in mess kitchen",
        "description": "Students noticed cockroaches and flies in the mess kitchen area. Food handlers are not wearing gloves or hairnets. This is a serious health and safety violation that needs immediate intervention.",
        "expected_authority": "Mess Committee Head",
        "expected_priority": "critical"
    },
    {
        "category": "food",
        "name": "Rahul Nair",
        "register_number": "22ME203",
        "department": "MECH",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Stale vegetables in mess curry",
        "description": "Yesterday's dinner had rotten vegetables in the curry. Multiple students complained of foul smell and taste. Some students have reported food poisoning symptoms. Urgent quality check needed.",
        "expected_authority": "Mess Committee Head",
        "expected_priority": "critical"
    },
    {
        "category": "food",
        "name": "Divya Krishnan",
        "register_number": "22IT204",
        "department": "IT",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Mess food quantity insufficient for students",
        "description": "The portion sizes served in mess have reduced significantly. Many students are still hungry after meals. We pay full mess fees but receive inadequate food. This needs to be addressed.",
        "expected_authority": "Mess Committee Head",
        "expected_priority": "medium"
    },
    {
        "category": "food",
        "name": "Arjun Das",
        "register_number": "22EE205",
        "department": "EEE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "No hot water for tea in morning mess",
        "description": "For the past 10 days, the mess has not been providing hot water for tea/coffee in the morning. Students have to attend early morning classes without any warm beverage in winter.",
        "expected_authority": "Mess Committee Head",
        "expected_priority": "low"
    },
    
    # ========================================
    # HOSTEL COMPLAINTS (5)
    # ========================================
    {
        "category": "hostel",
        "name": "Vikram Joshi",
        "register_number": "22CS301",
        "department": "CSE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Hostel room locks broken in Block B",
        "description": "The door locks in hostel rooms 201-210 Block B are not working properly. Students cannot secure their belongings. Risk of theft and no room security. Immediate lock replacement required.",
        "expected_authority": "Hostel Warden",
        "expected_priority": "high"
    },
    {
        "category": "hostel",
        "name": "Meera Iyer",
        "register_number": "22EC302",
        "department": "ECE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Hostel wifi not working for 15 days",
        "description": "The wifi in girls hostel Block A has been completely down for two weeks. Students cannot attend online classes, download study materials, or submit assignments. This is seriously affecting academics.",
        "expected_authority": "Hostel Warden",
        "expected_priority": "high"
    },
    {
        "category": "hostel",
        "name": "Suresh Pillai",
        "register_number": "22ME303",
        "department": "MECH",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Water leakage in hostel bathrooms Block C",
        "description": "Severe water leakage from bathroom pipes in rooms 301-305 Block C. Water seeping into rooms, damaging books and electronics. Mosquito breeding due to stagnant water. Health hazard.",
        "expected_authority": "Hostel Warden",
        "expected_priority": "critical"
    },
    {
        "category": "hostel",
        "name": "Pooja Gupta",
        "register_number": "22IT304",
        "department": "IT",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Hostel room cleaning not done regularly",
        "description": "Housekeeping staff have not cleaned hostel rooms for the past month. Dust accumulation, dirty floors, and unhygienic conditions in rooms. We pay hostel fees but cleaning service is not provided.",
        "expected_authority": "Hostel Warden",
        "expected_priority": "medium"
    },
    {
        "category": "hostel",
        "name": "Aditya Rao",
        "register_number": "22EE305",
        "department": "EEE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Unreasonable hostel night curfew timing",
        "description": "The 10 PM curfew timing is too early for engineering students who need to work on projects and assignments late night. Request to extend curfew to 11 PM on weekdays and 12 AM on weekends.",
        "expected_authority": "Hostel Warden",
        "expected_priority": "low"
    },
    
    # ========================================
    # ACADEMIC COMPLAINTS (5)
    # ========================================
    {
        "category": "academic",
        "name": "Rohit Verma",
        "register_number": "22CS401",
        "department": "CSE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Important textbooks missing from library",
        "description": "Key reference books for Data Structures and Algorithms course are not available in library. Only 2 copies for 80 students. Exam preparation is severely affected. Please procure more copies urgently.",
        "expected_authority": "Academic Dean",
        "expected_priority": "medium"
    },
    {
        "category": "academic",
        "name": "Lakshmi Menon",
        "register_number": "22EC402",
        "department": "ECE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Faculty teaching quality poor in Digital Electronics",
        "description": "The professor for Digital Electronics course is not explaining concepts clearly. Students are unable to understand the subject. Class attendance is dropping. Need better teaching methods or additional tutorial classes.",
        "expected_authority": "Academic Dean",
        "expected_priority": "medium"
    },
    {
        "category": "academic",
        "name": "Naveen Kumar",
        "register_number": "22ME403",
        "department": "MECH",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Lab equipment shortage for Thermodynamics practical",
        "description": "Not enough equipment in thermodynamics lab. 4 students have to share one setup. Practical exam is next week but students haven't got proper hands-on experience. Need more equipment sets.",
        "expected_authority": "Academic Dean",
        "expected_priority": "high"
    },
    {
        "category": "academic",
        "name": "Priyanka Sharma",
        "register_number": "22IT404",
        "department": "IT",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Outdated syllabus for Database Management course",
        "description": "The DBMS syllabus is 5 years old and doesn't include modern technologies like NoSQL, MongoDB, or cloud databases. Students are not industry-ready. Curriculum update urgently needed.",
        "expected_authority": "Academic Dean",
        "expected_priority": "medium"
    },
    {
        "category": "academic",
        "name": "Vishal Reddy",
        "register_number": "22EE405",
        "department": "EEE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Timetable clash between two core subjects",
        "description": "Power Systems and Control Systems are scheduled at the same time slot on Monday and Wednesday. Students cannot attend both classes. This is a major timetabling error affecting entire semester.",
        "expected_authority": "Academic Dean",
        "expected_priority": "critical"
    },
    
    # ========================================
    # TRANSPORT COMPLAINTS (5)
    # ========================================
    {
        "category": "transport",
        "name": "Manoj Pillai",
        "register_number": "22CS501",
        "department": "CSE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "College bus always late by 20-30 minutes",
        "description": "Route 5 college bus is consistently late every day. Students miss first period classes. Bus supposed to arrive at 8:00 AM but comes at 8:30 AM. Discipline action and timing adjustment needed.",
        "expected_authority": "Transport Coordinator",
        "expected_priority": "medium"
    },
    {
        "category": "transport",
        "name": "Kavya Nair",
        "register_number": "22EC502",
        "department": "ECE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Bus driver drives recklessly at high speed",
        "description": "The driver of Route 3 bus drives dangerously fast, overtakes vehicles rashly, and doesn't stop at zebra crossings. Students feel unsafe. Multiple complaints have been raised. Safety concern.",
        "expected_authority": "Transport Coordinator",
        "expected_priority": "critical"
    },
    {
        "category": "transport",
        "name": "Harish Kumar",
        "register_number": "22ME503",
        "department": "MECH",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Insufficient seating capacity in Route 7 bus",
        "description": "Route 7 bus has only 40 seats but picks up 65 students daily. Students have to stand for 1 hour journey. Very uncomfortable and unsafe. Need bigger bus or additional bus for this route.",
        "expected_authority": "Transport Coordinator",
        "expected_priority": "high"
    },
    {
        "category": "transport",
        "name": "Nisha Gupta",
        "register_number": "22IT504",
        "department": "IT",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "No bus service for weekend classes",
        "description": "College has introduced Saturday classes but no bus service on weekends. Day scholars from distant areas cannot attend. Either cancel weekend classes or provide transport facility.",
        "expected_authority": "Transport Coordinator",
        "expected_priority": "medium"
    },
    {
        "category": "transport",
        "name": "Ravi Shankar",
        "register_number": "22EE505",
        "department": "EEE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Bus AC not working in summer heat",
        "description": "The air conditioning in Route 2 bus has not been working for two weeks. In 38°C heat, students are traveling in unbearable conditions. Immediate AC repair required for student comfort.",
        "expected_authority": "Transport Coordinator",
        "expected_priority": "medium"
    },
    
    # ========================================
    # DISCIPLINARY COMPLAINTS (3)
    # ========================================
    {
        "category": "other",  # Disciplinary goes to "other" as per your current setup
        "name": "Sanjay Patel",
        "register_number": "22CS601",
        "department": "CSE",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Students smoking in college premises near canteen",
        "description": "A group of students regularly smoke cigarettes near the canteen area despite no-smoking rules. This is against college regulations and affecting other students. Disciplinary action needed.",
        "expected_authority": "Student Affairs Officer",
        "expected_priority": "medium"
    },
    {
        "category": "other",
        "name": "Anjali Iyer",
        "register_number": "22EC602",
        "department": "ECE",
        "stay_type": "Hostel",
        "visibility": "Public",
        "title": "Ragging incident in hostel fresher block",
        "description": "First year students in hostel are being subjected to ragging by senior students. Verbal abuse and forced to do errands. This is illegal and traumatic. Immediate investigation and strict action required.",
        "expected_authority": "Student Affairs Officer",
        "expected_priority": "critical"
    },
    {
        "category": "other",
        "name": "Kartik Menon",
        "register_number": "22ME603",
        "department": "MECH",
        "stay_type": "Day Scholar",
        "visibility": "Public",
        "title": "Vandalism of library property by students",
        "description": "Library books are being torn and damaged by some students. Obscene content written on desks. CCTV footage should be checked and culprits should be penalized for damaging college property.",
        "expected_authority": "Student Affairs Officer",
        "expected_priority": "medium"
    }
]

# ============================================
# RUN CLASSIFICATION TESTS
# ============================================

def run_classification_tests():
    """Test AI classification accuracy"""
    print_header("🧪 AI CLASSIFICATION ACCURACY TEST")
    print(f"{CYAN}Testing {len(test_complaints)} complaints across different categories{RESET}\n")
    
    results = {
        "total": 0,
        "category_correct": 0,
        "authority_correct": 0,
        "priority_reasonable": 0,
        "by_category": {}
    }
    
    for idx, complaint in enumerate(test_complaints, 1):
        expected_category = complaint.pop("category")
        expected_authority = complaint.pop("expected_authority")
        expected_priority = complaint.pop("expected_priority")
        
        print_test(idx, len(test_complaints), expected_category)
        print(f"   Title: {complaint['title'][:70]}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/complaints",
                json=complaint,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                
                actual_category = data.get("category", "unknown")
                actual_authority = data.get("assigned_to", "unknown")
                actual_priority = data.get("priority", "unknown")
                
                # Check category
                category_correct = actual_category == expected_category
                print_result(expected_category, actual_category, category_correct)
                
                # Check authority
                authority_correct = expected_authority.lower() in actual_authority.lower()
                print_result(expected_authority, actual_authority, authority_correct)
                
                # Check priority (allow some flexibility)
                priority_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                expected_score = priority_map.get(expected_priority, 2)
                actual_score = priority_map.get(actual_priority, 2)
                priority_reasonable = abs(expected_score - actual_score) <= 1
                
                if priority_reasonable:
                    print(f"   ✅ Priority: {actual_priority.upper()} (Expected: {expected_priority.upper()}) - Acceptable")
                else:
                    print(f"   ⚠️  Priority: {actual_priority.upper()} (Expected: {expected_priority.upper()}) - Off target")
                
                # Show AI summary
                summary = data.get("summary", "N/A")
                print(f"   📝 AI Summary: {summary[:80]}...")
                
                # Track results
                results["total"] += 1
                if category_correct:
                    results["category_correct"] += 1
                if authority_correct:
                    results["authority_correct"] += 1
                if priority_reasonable:
                    results["priority_reasonable"] += 1
                
                # Track by category
                if expected_category not in results["by_category"]:
                    results["by_category"][expected_category] = {"total": 0, "correct": 0}
                
                results["by_category"][expected_category]["total"] += 1
                if category_correct:
                    results["by_category"][expected_category]["correct"] += 1
            
            else:
                print(f"   {RED}❌ Failed to submit: {response.status_code}{RESET}")
        
        except Exception as e:
            print(f"   {RED}❌ Error: {e}{RESET}")
        
        time.sleep(0.5)
    
    # Print summary
    print_header("📊 CLASSIFICATION ACCURACY REPORT")
    
    total = results["total"]
    cat_correct = results["category_correct"]
    auth_correct = results["authority_correct"]
    pri_reasonable = results["priority_reasonable"]
    
    cat_accuracy = (cat_correct / total * 100) if total > 0 else 0
    auth_accuracy = (auth_correct / total * 100) if total > 0 else 0
    pri_accuracy = (pri_reasonable / total * 100) if total > 0 else 0
    
    print(f"\n{BOLD}Overall Results:{RESET}")
    print(f"  Total Tests: {total}")
    print(f"  Category Accuracy: {cat_correct}/{total} ({cat_accuracy:.1f}%)")
    print(f"  Authority Accuracy: {auth_correct}/{total} ({auth_accuracy:.1f}%)")
    print(f"  Priority Accuracy: {pri_reasonable}/{total} ({pri_accuracy:.1f}%)")
    
    print(f"\n{BOLD}Accuracy by Category:{RESET}")
    for category, stats in results["by_category"].items():
        accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {category.upper():<15}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
    
    # Overall grade
    avg_accuracy = (cat_accuracy + auth_accuracy + pri_accuracy) / 3
    
    print(f"\n{BOLD}Overall AI Performance:{RESET}")
    if avg_accuracy >= 90:
        print(f"  {GREEN}🏆 EXCELLENT: {avg_accuracy:.1f}%{RESET}")
    elif avg_accuracy >= 75:
        print(f"  {YELLOW}✅ GOOD: {avg_accuracy:.1f}%{RESET}")
    elif avg_accuracy >= 60:
        print(f"  {YELLOW}⚠️  FAIR: {avg_accuracy:.1f}%{RESET}")
    else:
        print(f"  {RED}❌ NEEDS IMPROVEMENT: {avg_accuracy:.1f}%{RESET}")
    
    return avg_accuracy >= 75


if __name__ == "__main__":
    try:
        success = run_classification_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted{RESET}")
        exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        exit(1)
