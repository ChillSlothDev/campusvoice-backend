"""
Database Models for CampusVoice Backend
PostgreSQL tables with SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# ============================================
# TABLE 1: STUDENTS (No dependencies)
# ============================================
class StudentDB(Base):
    """
    Student information table
    Uses roll_number as unique identifier
    """
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    roll_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    stay_type = Column(String(20), nullable=True)  # Hostel, Day Scholar
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    complaints = relationship("ComplaintDB", back_populates="student", cascade="all, delete-orphan")
    votes = relationship("VoteDB", back_populates="student", cascade="all, delete-orphan")
    status_updates = relationship("StatusUpdateDB", back_populates="user")
    
    def __repr__(self):
        return f"<Student {self.roll_number} - {self.name}>"


# ============================================
# TABLE 2: COMPLAINTS (Depends on Students)
# ============================================
class ComplaintDB(Base):
    """
    Complaint submissions table
    Stores all complaint information with LLM analysis
    """
    __tablename__ = "complaints"
    
    id = Column(String(50), primary_key=True)  # UUID
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    
    # Complaint content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    visibility = Column(String(20), default="Public", nullable=False)  # Public, Private
    image_url = Column(String(500), nullable=True)
    
    # Vote counts
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    
    # Status tracking
    status = Column(String(20), default="raised", nullable=False)  # raised, opened, reviewed, closed
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    
    # LLM analysis
    llm_analysis = Column(Text, nullable=True)
    llm_category = Column(String(50), nullable=True)
    llm_priority_score = Column(Integer, default=0)
    
    # Authority routing
    assigned_authority = Column(String(100), nullable=True)
    authority_email = Column(String(100), nullable=True)
    
    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    student = relationship("StudentDB", back_populates="complaints")
    votes = relationship("VoteDB", back_populates="complaint", cascade="all, delete-orphan")
    status_updates = relationship("StatusUpdateDB", back_populates="complaint", cascade="all, delete-orphan")
    meta = relationship("MetaDB", back_populates="complaint", cascade="all, delete-orphan")
    
    # Indexes for performance (UNIQUE NAMES!)
    __table_args__ = (
        Index('idx_complaint_student_id', 'student_id'),
        Index('idx_complaint_status', 'status'),
        Index('idx_complaint_priority', 'priority'),
        Index('idx_complaint_submitted_at', 'submitted_at'),
        Index('idx_complaint_visibility', 'visibility'),
    )
    
    def __repr__(self):
        return f"<Complaint {self.id} - {self.title[:30]}>"


# ============================================
# TABLE 3: VOTES (Depends on Complaints & Students)
# ============================================
class VoteDB(Base):
    """
    Votes table with UNIQUE constraint
    Prevents duplicate votes from same student on same complaint
    """
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(50), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    vote_type = Column(String(10), nullable=False)  # upvote, downvote
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    complaint = relationship("ComplaintDB", back_populates="votes")
    student = relationship("StudentDB", back_populates="votes")
    
    # UNIQUE CONSTRAINT - PREVENTS DUPLICATE VOTES
    # Same student can only vote ONCE per complaint
    __table_args__ = (
        UniqueConstraint('complaint_id', 'student_id', name='unique_vote_per_user'),
        Index('idx_vote_complaint_id', 'complaint_id'),
        Index('idx_vote_student_id', 'student_id'),
    )
    
    def __repr__(self):
        return f"<Vote {self.vote_type} by Student {self.student_id} on Complaint {self.complaint_id}>"


# ============================================
# TABLE 4: STATUS UPDATES (Depends on Complaints & Students)
# ============================================
class StatusUpdateDB(Base):
    """
    Status update audit trail
    Tracks all status changes with timestamp and user
    """
    __tablename__ = "status_updates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(50), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    updated_by = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    complaint = relationship("ComplaintDB", back_populates="status_updates")
    user = relationship("StudentDB", back_populates="status_updates")
    
    # Indexes
    __table_args__ = (
        Index('idx_status_complaint_id', 'complaint_id'),
        Index('idx_status_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<StatusUpdate {self.old_status} → {self.new_status}>"


# ============================================
# TABLE 5: META (Depends on Complaints)
# ============================================
class MetaDB(Base):
    """
    Metadata for complaint submissions
    Stores source and additional tracking info
    """
    __tablename__ = "meta"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(50), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True)
    source = Column(String(100), default="Campus Voice SREC", nullable=False)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    complaint = relationship("ComplaintDB", back_populates="meta")
    
    # Indexes
    __table_args__ = (
        Index('idx_meta_complaint_id', 'complaint_id'),
        Index('idx_meta_submitted_at', 'submitted_at'),
    )
    
    def __repr__(self):
        return f"<Meta for Complaint {self.complaint_id}>"


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_complaint_with_votes(complaint: ComplaintDB) -> dict:
    """
    Convert complaint to dict with vote information
    """
    return {
        "complaint_id": complaint.id,
        "title": complaint.title,
        "description": complaint.description,
        "visibility": complaint.visibility,
        "image_url": complaint.image_url,
        "upvotes": complaint.upvotes,
        "downvotes": complaint.downvotes,
        "status": complaint.status,
        "priority": complaint.priority,
        "student_name": complaint.student.name,
        "student_roll": complaint.student.roll_number,
        "department": complaint.student.department,
        "submitted_at": complaint.submitted_at.isoformat(),
        "llm_analysis": complaint.llm_analysis,
        "llm_category": complaint.llm_category,
    }


def get_student_summary(student: StudentDB) -> dict:
    """
    Convert student to dict summary
    """
    return {
        "id": student.id,
        "roll_number": student.roll_number,
        "name": student.name,
        "email": student.email,
        "department": student.department,
        "total_complaints": len(student.complaints),
        "total_votes": len(student.votes),
    }
