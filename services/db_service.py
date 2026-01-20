"""
Database Service Layer
All database CRUD operations for CampusVoice
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from models_db import StudentDB, ComplaintDB, VoteDB, StatusUpdateDB, MetaDB
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import uuid
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Database service for all CRUD operations
    
    Usage:
        db_service = DatabaseService(db_session)
        student = await db_service.get_or_create_student(...)
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize database service
        
        Args:
            db: Async database session
        """
        self.db = db
    
    # ============================================
    # STUDENT OPERATIONS
    # ============================================
    
    async def get_or_create_student(
        self,
        roll_number: str,
        name: str,
        email: str,
        department: str,
        stay_type: str = None
    ) -> StudentDB:
        """
        Get existing student or create new one
        
        Args:
            roll_number: Student roll number (unique identifier)
            name: Student name
            email: Student email
            department: Department (CSE, ECE, etc.)
            stay_type: Hostel or Day Scholar
        
        Returns:
            StudentDB: Student object
        """
        # Try to find existing student
        stmt = select(StudentDB).where(StudentDB.roll_number == roll_number)
        result = await self.db.execute(stmt)
        student = result.scalars().first()
        
        if student:
            # Update if information changed
            if student.name != name or student.email != email or student.department != department:
                student.name = name
                student.email = email
                student.department = department
                student.stay_type = stay_type
                student.updated_at = datetime.utcnow()
                await self.db.commit()
                await self.db.refresh(student)
                logger.info(f"✏️  Updated student: {roll_number}")
            
            return student
        
        # Create new student
        student = StudentDB(
            roll_number=roll_number,
            name=name,
            email=email,
            department=department,
            stay_type=stay_type
        )
        
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)
        
        logger.info(f"✅ Created new student: {roll_number}")
        return student
    
    async def get_student_by_roll_number(self, roll_number: str) -> Optional[StudentDB]:
        """
        Get student by roll number
        
        Args:
            roll_number: Student roll number
        
        Returns:
            StudentDB or None
        """
        stmt = select(StudentDB).where(StudentDB.roll_number == roll_number)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_student_by_id(self, student_id: int) -> Optional[StudentDB]:
        """
        Get student by database ID
        
        Args:
            student_id: Student database ID
        
        Returns:
            StudentDB or None
        """
        stmt = select(StudentDB).where(StudentDB.id == student_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    # ============================================
    # COMPLAINT OPERATIONS
    # ============================================
    
    async def create_complaint(
        self,
        student_id: int,
        title: str,
        description: str,
        visibility: str,
        image_url: Optional[str] = None,
        priority: str = "medium",
        llm_analysis: Optional[str] = None,
        llm_category: Optional[str] = None,
        assigned_authority: Optional[str] = None,
        authority_email: Optional[str] = None
    ) -> ComplaintDB:
        """
        Create new complaint
        
        Args:
            student_id: Student database ID
            title: Complaint title
            description: Complaint description
            visibility: Public or Private
            image_url: Optional image URL
            priority: low, medium, high, critical
            llm_analysis: LLM analysis result
            llm_category: LLM category (food, infrastructure, etc.)
            assigned_authority: Authority to handle complaint
            authority_email: Authority email
        
        Returns:
            ComplaintDB: Created complaint
        """
        complaint = ComplaintDB(
            id=str(uuid.uuid4()),
            student_id=student_id,
            title=title,
            description=description,
            visibility=visibility,
            image_url=image_url,
            priority=priority,
            llm_analysis=llm_analysis,
            llm_category=llm_category,
            assigned_authority=assigned_authority,
            authority_email=authority_email,
            upvotes=0,
            downvotes=0,
            status="raised"
        )
        
        self.db.add(complaint)
        await self.db.commit()
        await self.db.refresh(complaint)
        
        logger.info(f"✅ Created complaint: {complaint.id} - {title[:30]}")
        return complaint
    
    async def get_complaint(self, complaint_id: str) -> Optional[ComplaintDB]:
        """
        Get complaint by ID with student relationship loaded
        
        Args:
            complaint_id: Complaint UUID
        
        Returns:
            ComplaintDB or None
        """
        stmt = select(ComplaintDB).options(
            selectinload(ComplaintDB.student)
        ).where(ComplaintDB.id == complaint_id)
        
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_student_complaints(
        self,
        student_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ComplaintDB]:
        """
        Get all complaints by a specific student
        
        Args:
            student_id: Student database ID
            limit: Max number of complaints to return
            offset: Pagination offset
        
        Returns:
            List of ComplaintDB objects
        """
        stmt = select(ComplaintDB).where(
            ComplaintDB.student_id == student_id
        ).order_by(
            desc(ComplaintDB.submitted_at)
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_public_complaints(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None
    ) -> List[ComplaintDB]:
        """
        Get public complaints feed
        
        Args:
            limit: Max number of complaints
            offset: Pagination offset
            status_filter: Filter by status (raised, opened, reviewed, closed)
            priority_filter: Filter by priority (low, medium, high, critical)
        
        Returns:
            List of ComplaintDB objects with student data
        """
        # Base query
        stmt = select(ComplaintDB).options(
            selectinload(ComplaintDB.student)
        ).where(ComplaintDB.visibility == "Public")
        
        # Apply filters
        if status_filter:
            stmt = stmt.where(ComplaintDB.status == status_filter)
        
        if priority_filter:
            stmt = stmt.where(ComplaintDB.priority == priority_filter)
        
        # Order and paginate
        stmt = stmt.order_by(
            desc(ComplaintDB.submitted_at)
        ).limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_complaints_by_status(
        self,
        status: str,
        limit: int = 50
    ) -> List[ComplaintDB]:
        """
        Get complaints by status
        
        Args:
            status: Status to filter (raised, opened, reviewed, closed)
            limit: Max number of complaints
        
        Returns:
            List of ComplaintDB objects
        """
        stmt = select(ComplaintDB).options(
            selectinload(ComplaintDB.student)
        ).where(
            ComplaintDB.status == status
        ).order_by(
            desc(ComplaintDB.submitted_at)
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_complaint_status(
        self,
        complaint_id: str,
        new_status: str,
        updated_by: int,
        reason: Optional[str] = None
    ):
        """
        Update complaint status and record change in audit trail
        
        Args:
            complaint_id: Complaint UUID
            new_status: New status (raised, opened, reviewed, closed)
            updated_by: Student ID who updated
            reason: Optional reason for status change
        """
        # Get current complaint
        complaint = await self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found")
        
        old_status = complaint.status
        
        # Update complaint status
        complaint.status = new_status
        complaint.updated_at = datetime.utcnow()
        
        if new_status == "closed":
            complaint.resolved_at = datetime.utcnow()
        
        # Create status update record
        status_update = StatusUpdateDB(
            complaint_id=complaint_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=updated_by,
            reason=reason
        )
        
        self.db.add(complaint)
        self.db.add(status_update)
        await self.db.commit()
        
        logger.info(f"✏️  Updated complaint {complaint_id}: {old_status} → {new_status}")
    
    async def update_complaint_priority(
        self,
        complaint_id: str,
        priority: str
    ):
        """
        Update complaint priority
        
        Args:
            complaint_id: Complaint UUID
            priority: New priority (low, medium, high, critical)
        """
        stmt = update(ComplaintDB).where(
            ComplaintDB.id == complaint_id
        ).values(
            priority=priority,
            updated_at=datetime.utcnow()
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"✏️  Updated complaint {complaint_id} priority to {priority}")
    
    # ============================================
    # VOTE OPERATIONS (WITH AUTO PRIORITY UPDATE)
    # ============================================
    
    async def vote_on_complaint(
        self,
        complaint_id: str,
        student_id: int,
        vote_type: str
    ) -> Dict:
        """
        Vote on complaint with automatic duplicate prevention
        AND automatic priority recalculation
        
        UNIQUE constraint ensures same student can only vote once per complaint
        
        Args:
            complaint_id: Complaint UUID
            student_id: Student database ID
            vote_type: "upvote" or "downvote"
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "action": "created" | "updated" | "deleted",
                "upvotes": int,
                "downvotes": int,
                "priority_updated": bool,
                "old_priority": str,
                "new_priority": str
            }
        """
        try:
            # Check if vote already exists
            stmt = select(VoteDB).where(
                and_(
                    VoteDB.complaint_id == complaint_id,
                    VoteDB.student_id == student_id
                )
            )
            result = await self.db.execute(stmt)
            existing_vote = result.scalars().first()
            
            # Get complaint
            complaint = await self.get_complaint(complaint_id)
            if not complaint:
                return {
                    "success": False,
                    "message": "Complaint not found",
                    "action": None
                }
            
            old_priority = complaint.priority
            
            # CASE 1: No existing vote - CREATE NEW
            if not existing_vote:
                # Create new vote
                vote = VoteDB(
                    complaint_id=complaint_id,
                    student_id=student_id,
                    vote_type=vote_type
                )
                
                # Update complaint counts
                if vote_type == "upvote":
                    complaint.upvotes += 1
                else:
                    complaint.downvotes += 1
                
                self.db.add(vote)
                self.db.add(complaint)
                await self.db.commit()
                await self.db.refresh(complaint)
                
                action = "created"
                message = f"{vote_type.capitalize()} added"
            
            # CASE 2: Same vote type - REMOVE VOTE (toggle off)
            elif existing_vote.vote_type == vote_type:
                # Remove vote
                if vote_type == "upvote":
                    complaint.upvotes = max(0, complaint.upvotes - 1)
                else:
                    complaint.downvotes = max(0, complaint.downvotes - 1)
                
                await self.db.delete(existing_vote)
                self.db.add(complaint)
                await self.db.commit()
                await self.db.refresh(complaint)
                
                action = "deleted"
                message = f"{vote_type.capitalize()} removed"
            
            # CASE 3: Different vote type - CHANGE VOTE
            else:
                old_vote_type = existing_vote.vote_type
                
                # Update counts
                if old_vote_type == "upvote":
                    complaint.upvotes = max(0, complaint.upvotes - 1)
                    complaint.downvotes += 1
                else:
                    complaint.downvotes = max(0, complaint.downvotes - 1)
                    complaint.upvotes += 1
                
                # Update vote
                existing_vote.vote_type = vote_type
                
                self.db.add(existing_vote)
                self.db.add(complaint)
                await self.db.commit()
                await self.db.refresh(complaint)
                
                action = "updated"
                message = f"Vote changed to {vote_type}"
            
            # ============================================
            # AUTO-RECALCULATE PRIORITY BASED ON VOTES
            # ============================================
            
            priority_updated = False
            new_priority = complaint.priority
            
            # Only recalculate if we have LLM analysis
            if complaint.llm_analysis:
                try:
                    from services.llm_service import LLMService
                    llm_service = LLMService()
                    
                    llm_analysis = json.loads(complaint.llm_analysis)
                    
                    # Calculate new priority score
                    priority_score = await llm_service.calculate_priority_score(
                        analysis=llm_analysis,
                        upvotes=complaint.upvotes,
                        downvotes=complaint.downvotes
                    )
                    
                    # Get new priority label
                    new_priority = llm_service.get_priority_label(priority_score)
                    
                    # Update if changed
                    if new_priority != old_priority:
                        complaint.priority = new_priority
                        
                        # Update llm_priority_score if field exists
                        try:
                            complaint.llm_priority_score = priority_score
                        except AttributeError:
                            pass  # Field doesn't exist in model
                        
                        self.db.add(complaint)
                        await self.db.commit()
                        await self.db.refresh(complaint)
                        priority_updated = True
                        
                        logger.info(f"📊 Priority auto-updated: {old_priority} → {new_priority} (score: {priority_score})")
                
                except Exception as e:
                    logger.warning(f"Could not recalculate priority: {e}")
            
            logger.info(f"✅ Vote {action}: {vote_type} on complaint {complaint_id}")
            
            return {
                "success": True,
                "message": message,
                "action": action,
                "upvotes": complaint.upvotes,
                "downvotes": complaint.downvotes,
                "priority_updated": priority_updated,
                "old_priority": old_priority if priority_updated else None,
                "new_priority": new_priority if priority_updated else None
            }
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Vote error: {e}")
            return {
                "success": False,
                "message": f"Vote error: {str(e)}",
                "action": None
            }
    
    async def get_user_vote(
        self,
        complaint_id: str,
        student_id: int
    ) -> Optional[str]:
        """
        Get user's vote on a complaint
        
        Args:
            complaint_id: Complaint UUID
            student_id: Student database ID
        
        Returns:
            "upvote", "downvote", or None
        """
        stmt = select(VoteDB).where(
            and_(
                VoteDB.complaint_id == complaint_id,
                VoteDB.student_id == student_id
            )
        )
        
        result = await self.db.execute(stmt)
        vote = result.scalars().first()
        
        return vote.vote_type if vote else None
    
    async def get_vote_stats(self, complaint_id: str) -> Optional[Dict]:
        """
        Get vote statistics for a complaint
        
        Args:
            complaint_id: Complaint UUID
        
        Returns:
            dict: {
                "upvotes": int,
                "downvotes": int,
                "total": int,
                "net_votes": int
            }
        """
        complaint = await self.get_complaint(complaint_id)
        if not complaint:
            return None
        
        return {
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "total": complaint.upvotes + complaint.downvotes,
            "net_votes": complaint.upvotes - complaint.downvotes
        }
    
    async def get_complaint_voters(
        self,
        complaint_id: str
    ) -> Dict:
        """
        Get list of voters for a complaint
        
        Args:
            complaint_id: Complaint UUID
        
        Returns:
            dict: {
                "upvoters": List[dict],
                "downvoters": List[dict]
            }
        """
        stmt = select(VoteDB).options(
            selectinload(VoteDB.student)
        ).where(VoteDB.complaint_id == complaint_id)
        
        result = await self.db.execute(stmt)
        votes = result.scalars().all()
        
        upvoters = []
        downvoters = []
        
        for vote in votes:
            voter_info = {
                "roll_number": vote.student.roll_number,
                "name": vote.student.name,
                "voted_at": vote.created_at.isoformat()
            }
            
            if vote.vote_type == "upvote":
                upvoters.append(voter_info)
            else:
                downvoters.append(voter_info)
        
        return {
            "upvoters": upvoters,
            "downvoters": downvoters
        }
    
    # ============================================
    # STATISTICS & ANALYTICS
    # ============================================
    
    async def get_student_stats(self, student_id: int) -> Dict:
        """
        Get statistics for a student
        
        Args:
            student_id: Student database ID
        
        Returns:
            dict: Student statistics
        """
        # Count complaints
        complaint_count_stmt = select(func.count(ComplaintDB.id)).where(
            ComplaintDB.student_id == student_id
        )
        complaint_count_result = await self.db.execute(complaint_count_stmt)
        complaint_count = complaint_count_result.scalar()
        
        # Count votes
        vote_count_stmt = select(func.count(VoteDB.id)).where(
            VoteDB.student_id == student_id
        )
        vote_count_result = await self.db.execute(vote_count_stmt)
        vote_count = vote_count_result.scalar()
        
        # Get complaints by status
        status_stmt = select(
            ComplaintDB.status,
            func.count(ComplaintDB.id)
        ).where(
            ComplaintDB.student_id == student_id
        ).group_by(ComplaintDB.status)
        
        status_result = await self.db.execute(status_stmt)
        status_breakdown = {status: count for status, count in status_result}
        
        return {
            "total_complaints": complaint_count,
            "total_votes_cast": vote_count,
            "complaints_by_status": status_breakdown
        }
    
    async def get_overall_stats(self) -> Dict:
        """
        Get overall system statistics
        
        Returns:
            dict: Overall statistics
        """
        # Total students
        student_count_stmt = select(func.count(StudentDB.id))
        student_count_result = await self.db.execute(student_count_stmt)
        student_count = student_count_result.scalar()
        
        # Total complaints
        complaint_count_stmt = select(func.count(ComplaintDB.id))
        complaint_count_result = await self.db.execute(complaint_count_stmt)
        complaint_count = complaint_count_result.scalar()
        
        # Total votes
        vote_count_stmt = select(func.count(VoteDB.id))
        vote_count_result = await self.db.execute(vote_count_stmt)
        vote_count = vote_count_result.scalar()
        
        # Complaints by status
        status_stmt = select(
            ComplaintDB.status,
            func.count(ComplaintDB.id)
        ).group_by(ComplaintDB.status)
        
        status_result = await self.db.execute(status_stmt)
        status_breakdown = {status: count for status, count in status_result}
        
        # Complaints by priority
        priority_stmt = select(
            ComplaintDB.priority,
            func.count(ComplaintDB.id)
        ).group_by(ComplaintDB.priority)
        
        priority_result = await self.db.execute(priority_stmt)
        priority_breakdown = {priority: count for priority, count in priority_result}
        
        return {
            "total_students": student_count,
            "total_complaints": complaint_count,
            "total_votes": vote_count,
            "complaints_by_status": status_breakdown,
            "complaints_by_priority": priority_breakdown
        }
    
    # ============================================
    # SEARCH & FILTER
    # ============================================
    
    async def search_complaints(
        self,
        query: str,
        limit: int = 20
    ) -> List[ComplaintDB]:
        """
        Search complaints by title or description
        
        Args:
            query: Search query
            limit: Max results
        
        Returns:
            List of matching complaints
        """
        search_pattern = f"%{query}%"
        
        stmt = select(ComplaintDB).options(
            selectinload(ComplaintDB.student)
        ).where(
            or_(
                ComplaintDB.title.ilike(search_pattern),
                ComplaintDB.description.ilike(search_pattern)
            )
        ).order_by(
            desc(ComplaintDB.submitted_at)
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

# ============================================
# EXPORT
# ============================================

__all__ = ["DatabaseService"]
