"""
API Routes for CampusVoice Backend
REST endpoints + WebSocket for real-time updates
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import json
import logging

# Import dependencies
from database import get_db
from services.db_service import DatabaseService
from services.llm_service import LLMService
from websocket_handler import manager
from models_db import ComplaintDB
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["CampusVoice API"])

# Initialize LLM service
llm_service = LLMService()

# ============================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================

class ComplaintSubmission(BaseModel):
    """Complaint submission request (matches your JSON format)"""
    name: str = Field(..., min_length=2, max_length=100)
    register_number: str = Field(..., min_length=5, max_length=20)
    department: str = Field(..., min_length=2, max_length=50)
    stay_type: Optional[str] = Field(None, max_length=20)
    visibility: str = Field(..., pattern="^(Public|Private)$")
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Arun Kumar",
                "register_number": "22CS045",
                "department": "CSE",
                "stay_type": "Hostel",
                "visibility": "Public",
                "title": "Mess food quality issue",
                "description": "Rice is undercooked and curry is watery",
                "image_url": "uploads/complaints/123.jpg"
            }
        }

class VoteRequest(BaseModel):
    """Vote request"""
    complaint_id: str = Field(..., min_length=10)
    roll_number: str = Field(..., min_length=5, max_length=20)
    vote_type: str = Field(..., pattern="^(upvote|downvote)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "complaint_id": "abc-123-def-456",
                "roll_number": "22CS045",
                "vote_type": "upvote"
            }
        }

class StatusUpdateRequest(BaseModel):
    """Status update request"""
    complaint_id: str
    new_status: str = Field(..., pattern="^(raised|opened|reviewed|closed)$")
    updated_by_roll: str
    reason: Optional[str] = None

class ComplaintResponse(BaseModel):
    """Complaint response schema"""
    complaint_id: str
    title: str
    description: str
    visibility: str
    status: str
    priority: str
    upvotes: int
    downvotes: int
    student_name: str
    student_roll: str
    department: str
    submitted_at: str
    image_url: Optional[str]
    llm_analysis: Optional[dict]
    assigned_authority: Optional[str]

# ============================================
# ENDPOINT 1: SUBMIT COMPLAINT
# ============================================

@router.post(
    "/complaints",
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new complaint",
    description="Submit a complaint with automatic LLM analysis and authority routing"
)
async def submit_complaint(
    complaint: ComplaintSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a new complaint
    
    **Process:**
    1. Create/update student record
    2. Analyze complaint with LLM
    3. Route to appropriate authority
    4. Create complaint in database
    5. Return complaint ID and analysis
    
    **Returns:**
    - complaint_id: Unique complaint identifier
    - priority: Detected priority (low, medium, high, critical)
    - category: Detected category (food, infrastructure, etc.)
    - assigned_to: Authority assigned to handle
    """
    try:
        db_service = DatabaseService(db)
        
        # Step 1: Get or create student
        student = await db_service.get_or_create_student(
            roll_number=complaint.register_number,
            name=complaint.name,
            email=f"{complaint.register_number}@srec.ac.in",
            department=complaint.department,
            stay_type=complaint.stay_type
        )
        
        logger.info(f"📝 Processing complaint from {complaint.register_number}")
        
        # Step 2: Analyze with LLM
        analysis = await llm_service.analyze_complaint(
            title=complaint.title,
            description=complaint.description
        )
        
        # Step 3: Get authority routing
        authority = llm_service.get_authority_from_category(
            analysis.get("category", "other")
        )
        
        # Step 4: Create complaint
        new_complaint = await db_service.create_complaint(
            student_id=student.id,
            title=complaint.title,
            description=complaint.description,
            visibility=complaint.visibility,
            image_url=complaint.image_url,
            priority=analysis.get("priority", "medium"),
            llm_analysis=json.dumps(analysis),
            llm_category=analysis.get("category"),
            assigned_authority=authority.get("authority"),
            authority_email=authority.get("email")
        )
        
        logger.info(f"✅ Complaint created: {new_complaint.id}")
        
        # Step 5: Return response (FIXED: use new_complaint.title)
        return {
            "success": True,
            "complaint_id": new_complaint.id,
            "message": "Complaint submitted successfully",
            "title": new_complaint.title,  # ✅ FIX: Use complaint object, not analysis
            "priority": analysis.get("priority"),
            "category": analysis.get("category"),
            "urgency_score": analysis.get("urgency_score"),
            "assigned_to": authority.get("authority"),
            "authority_email": authority.get("email"),
            "summary": analysis.get("summary"),
            "status": new_complaint.status
        }
    
    except Exception as e:
        logger.error(f"❌ Error submitting complaint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting complaint: {str(e)}"
        )

# ============================================
# ENDPOINT 2: GET YOUR COMPLAINTS
# ============================================

@router.get(
    "/complaints/my",
    summary="Get your complaints",
    description="Retrieve all complaints submitted by a specific student (identified by roll number)"
)
async def get_my_complaints(
    roll_number: str = Query(..., min_length=5, description="Your roll number"),
    limit: int = Query(50, ge=1, le=100, description="Max complaints to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all complaints by current student
    
    **Query Parameters:**
    - roll_number: Your student roll number (required)
    - limit: Max number of complaints (default: 50)
    - offset: Pagination offset (default: 0)
    
    **Returns:**
    List of your complaints with full details
    """
    try:
        db_service = DatabaseService(db)
        
        # Get student
        student = await db_service.get_student_by_roll_number(roll_number)
        if not student:
            return {
                "success": True,
                "roll_number": roll_number,
                "count": 0,
                "complaints": [],
                "message": "No student found with this roll number"
            }
        
        # Get student's complaints
        complaints = await db_service.get_student_complaints(
            student_id=student.id,
            limit=limit,
            offset=offset
        )
        
        # Format response
        complaint_list = []
        for c in complaints:
            complaint_list.append({
                "complaint_id": c.id,
                "title": c.title,
                "description": c.description,
                "status": c.status,
                "priority": c.priority,
                "visibility": c.visibility,
                "upvotes": c.upvotes,
                "downvotes": c.downvotes,
                "category": c.llm_category,
                "submitted_at": c.submitted_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
                "image_url": c.image_url,
                "assigned_authority": c.assigned_authority
            })
        
        logger.info(f"📋 Retrieved {len(complaints)} complaints for {roll_number}")
        
        return {
            "success": True,
            "roll_number": roll_number,
            "student_name": student.name,
            "count": len(complaints),
            "complaints": complaint_list
        }
    
    except Exception as e:
        logger.error(f"❌ Error retrieving complaints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving complaints: {str(e)}"
        )

# ============================================
# ENDPOINT 3: GET PUBLIC FEED
# ============================================

@router.get(
    "/complaints/public",
    summary="Get public complaints feed",
    description="Retrieve public complaints with optional filters"
)
async def get_public_complaints(
    limit: int = Query(50, ge=1, le=100, description="Max complaints"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status_filter: Optional[str] = Query(None, pattern="^(raised|opened|reviewed|closed)$"),
    priority_filter: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get public complaints feed
    
    **Query Parameters:**
    - limit: Max complaints (default: 50, max: 100)
    - offset: Pagination offset
    - status_filter: Filter by status (raised, opened, reviewed, closed)
    - priority_filter: Filter by priority (low, medium, high, critical)
    
    **Returns:**
    List of public complaints with student info
    """
    try:
        db_service = DatabaseService(db)
        
        # Get public complaints
        complaints = await db_service.get_public_complaints(
            limit=limit,
            offset=offset,
            status_filter=status_filter,
            priority_filter=priority_filter
        )
        
        # Format response
        complaint_list = []
        for c in complaints:
            complaint_list.append({
                "complaint_id": c.id,
                "title": c.title,
                "description": c.description[:200] + "..." if len(c.description) > 200 else c.description,
                "status": c.status,
                "priority": c.priority,
                "upvotes": c.upvotes,
                "downvotes": c.downvotes,
                "category": c.llm_category,
                "student_name": c.student.name,
                "department": c.student.department,
                "submitted_at": c.submitted_at.isoformat(),
                "image_url": c.image_url
            })
        
        logger.info(f"📰 Retrieved {len(complaints)} public complaints")
        
        return {
            "success": True,
            "count": len(complaints),
            "filters": {
                "status": status_filter,
                "priority": priority_filter
            },
            "complaints": complaint_list
        }
    
    except Exception as e:
        logger.error(f"❌ Error retrieving public feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving public feed: {str(e)}"
        )

# ============================================
# ENDPOINT 4: GET COMPLAINT DETAILS
# ============================================

@router.get(
    "/complaints/{complaint_id}",
    summary="Get complaint details",
    description="Get full details of a specific complaint"
)
async def get_complaint_detail(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full complaint details including LLM analysis
    
    **Path Parameters:**
    - complaint_id: Complaint UUID
    
    **Returns:**
    Complete complaint information with analysis
    """
    try:
        db_service = DatabaseService(db)
        
        # Get complaint
        complaint = await db_service.get_complaint(complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found"
            )
        
        # Parse LLM analysis
        llm_analysis = None
        if complaint.llm_analysis:
            try:
                llm_analysis = json.loads(complaint.llm_analysis)
            except:
                pass
        
        # Format response
        response = {
            "success": True,
            "complaint_id": complaint.id,
            "title": complaint.title,
            "description": complaint.description,
            "status": complaint.status,
            "priority": complaint.priority,
            "visibility": complaint.visibility,
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "net_votes": complaint.upvotes - complaint.downvotes,
            "category": complaint.llm_category,
            "student": {
                "name": complaint.student.name,
                "roll_number": complaint.student.roll_number,
                "department": complaint.student.department,
                "stay_type": complaint.student.stay_type
            },
            "assigned_authority": complaint.assigned_authority,
            "authority_email": complaint.authority_email,
            "submitted_at": complaint.submitted_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat(),
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
            "image_url": complaint.image_url,
            "llm_analysis": llm_analysis
        }
        
        logger.info(f"📄 Retrieved complaint details: {complaint_id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving complaint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving complaint: {str(e)}"
        )

# ============================================
# ENDPOINT 5: VOTE ON COMPLAINT
# ============================================

@router.post(
    "/vote",
    summary="Vote on a complaint",
    description="Upvote or downvote a complaint (with automatic duplicate prevention)"
)
async def vote_on_complaint(
    vote: VoteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Vote on a complaint
    
    **Features:**
    - UNIQUE constraint prevents duplicate votes
    - Vote again with same type = removes vote (toggle)
    - Vote with different type = changes vote
    - Real-time WebSocket broadcast to all connected clients
    - AUTO priority recalculation based on votes
    
    **Request Body:**
    - complaint_id: Complaint UUID
    - roll_number: Your roll number
    - vote_type: "upvote" or "downvote"
    
    **Returns:**
    Updated vote counts + action taken + priority changes
    """
    try:
        db_service = DatabaseService(db)
        
        # Get student
        student = await db_service.get_student_by_roll_number(vote.roll_number)
        if not student:
            # Create minimal student record for voting
            student = await db_service.get_or_create_student(
                roll_number=vote.roll_number,
                name="Student",
                email=f"{vote.roll_number}@srec.ac.in",
                department="Unknown"
            )
        
        # Vote on complaint (with auto priority update)
        result = await db_service.vote_on_complaint(
            complaint_id=vote.complaint_id,
            student_id=student.id,
            vote_type=vote.vote_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        # Broadcast real-time update via WebSocket
        await manager.broadcast_vote_update(
            complaint_id=vote.complaint_id,
            vote_data={
                "upvotes": result["upvotes"],
                "downvotes": result["downvotes"],
                "total_votes": result["upvotes"] + result["downvotes"],
                "action": result["action"],
                "vote_type": vote.vote_type,
                "priority_updated": result.get("priority_updated", False),
                "new_priority": result.get("new_priority")
            }
        )
        
        logger.info(f"🗳️ Vote {result['action']}: {vote.vote_type} on {vote.complaint_id}")
        
        response = {
            "success": True,
            "message": result["message"],
            "action": result["action"],
            "upvotes": result["upvotes"],
            "downvotes": result["downvotes"],
            "net_votes": result["upvotes"] - result["downvotes"]
        }
        
        # Add priority update info if changed
        if result.get("priority_updated"):
            response["priority_updated"] = True
            response["old_priority"] = result.get("old_priority")
            response["new_priority"] = result.get("new_priority")
            logger.info(f"📊 Priority auto-updated: {result.get('old_priority')} → {result.get('new_priority')}")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Vote error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vote error: {str(e)}"
        )

# ============================================
# ENDPOINT 6: GET VOTE STATISTICS
# ============================================

@router.get(
    "/votes/{complaint_id}",
    summary="Get vote statistics",
    description="Get current vote counts for a complaint"
)
async def get_vote_stats(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get vote statistics for a complaint
    
    **Path Parameters:**
    - complaint_id: Complaint UUID
    
    **Returns:**
    - upvotes: Number of upvotes
    - downvotes: Number of downvotes
    - total: Total votes
    - net_votes: Upvotes minus downvotes
    """
    try:
        db_service = DatabaseService(db)
        stats = await db_service.get_vote_stats(complaint_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found"
            )
        
        logger.info(f"📊 Retrieved vote stats for {complaint_id}")
        
        return {
            "success": True,
            "complaint_id": complaint_id,
            **stats
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving vote stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vote stats: {str(e)}"
        )

# ============================================
# ENDPOINT 7: WEBSOCKET (REAL-TIME UPDATES)
# ============================================

@router.websocket("/ws/votes/{complaint_id}")
async def websocket_vote_endpoint(
    websocket: WebSocket,
    complaint_id: str
):
    """
    WebSocket endpoint for real-time vote updates
    
    **Connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/ws/votes/{complaint_id}');
    ```
    
    **Receives:**
    ```json
    {
      "type": "vote_update",
      "complaint_id": "abc-123",
      "upvotes": 45,
      "downvotes": 3,
      "total_votes": 48,
      "action": "upvote_added",
      "timestamp": "2026-01-19T17:41:00"
    }
    ```
    
    **Features:**
    - Real-time updates (<100ms latency)
    - Auto-reconnect on disconnect
    - Broadcast to all connected clients
    """
    # Connect client
    await manager.connect(websocket, complaint_id)
    logger.info(f"🔌 WebSocket connected for complaint {complaint_id}")
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for keep-alive
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            
            # Optional: handle other client messages
            else:
                logger.debug(f"📨 Received from client: {data}")
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket, complaint_id)
        logger.info(f"🔌 WebSocket disconnected for complaint {complaint_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await manager.disconnect(websocket, complaint_id)

# ============================================
# ENDPOINT 8: UPDATE COMPLAINT STATUS (NEW!)
# ============================================

@router.post(
    "/status/update",
    summary="Update complaint status",
    description="Update complaint status (Authority use only)"
)
async def update_complaint_status(
    update: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update complaint status
    
    **Authority Use Only**
    
    **Request Body:**
    - complaint_id: Complaint UUID
    - new_status: New status (raised, opened, reviewed, closed)
    - updated_by_roll: Authority roll number/ID
    - reason: Optional reason for status change
    
    **Returns:**
    Updated status information
    """
    try:
        db_service = DatabaseService(db)
        
        # Get or create authority user
        authority = await db_service.get_student_by_roll_number(update.updated_by_roll)
        if not authority:
            authority = await db_service.get_or_create_student(
                roll_number=update.updated_by_roll,
                name="Authority User",
                email=f"{update.updated_by_roll}@srec.ac.in",
                department="Administration"
            )
        
        # Get complaint before update
        complaint = await db_service.get_complaint(update.complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {update.complaint_id} not found"
            )
        
        old_status = complaint.status
        
        # Update status
        await db_service.update_complaint_status(
            complaint_id=update.complaint_id,
            new_status=update.new_status,
            updated_by=authority.id,
            reason=update.reason
        )
        
        logger.info(f"✏️  Status updated: {update.complaint_id} → {update.new_status}")
        
        # Broadcast status change via WebSocket
        await manager.broadcast_status_update(
            complaint_id=update.complaint_id,
            status_data={
                "old_status": old_status,
                "new_status": update.new_status,
                "updated_by": authority.name,
                "updated_by_roll": authority.roll_number,
                "reason": update.reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": f"Status updated to {update.new_status}",
            "complaint_id": update.complaint_id,
            "old_status": old_status,
            "new_status": update.new_status,
            "updated_by": authority.name,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating status: {str(e)}"
        )

# ============================================
# ENDPOINT 9: AUTHORITY-SPECIFIC COMPLAINTS
# ============================================

@router.get(
    "/authority/{authority_type}/complaints",
    summary="Get complaints for specific authority",
    description="Get complaints assigned to a specific authority type"
)
async def get_authority_complaints(
    authority_type: str,
    status_filter: Optional[str] = Query(None, pattern="^(raised|opened|reviewed|closed)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complaints assigned to specific authority
    
    **Path Parameters:**
    - authority_type: Type of authority (food, infrastructure, academic, hostel, transport, other)
    
    **Query Parameters:**
    - status_filter: Filter by status
    - limit: Max complaints to return
    - offset: Pagination offset
    
    **Returns:**
    List of complaints assigned to this authority
    """
    try:
        db_service = DatabaseService(db)
        
        # Map authority type to authority name
        authority_map = {
            "food": "Mess Committee Head",
            "infrastructure": "Maintenance Officer",
            "academic": "Academic Dean",
            "hostel": "Hostel Warden",
            "transport": "Transport Coordinator",
            "other": "Student Affairs Officer"
        }
        
        authority_name = authority_map.get(authority_type.lower())
        
        if not authority_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid authority type: {authority_type}. Valid types: {', '.join(authority_map.keys())}"
            )
        
        # Get all complaints (we'll filter by authority)
        complaints = await db_service.get_public_complaints(
            limit=limit * 2,  # Get more to filter
            offset=offset,
            status_filter=status_filter
        )
        
        # Filter by assigned authority
        filtered_complaints = [
            c for c in complaints
            if c.assigned_authority == authority_name
        ][:limit]
        
        # Format response
        complaint_list = []
        for c in filtered_complaints:
            complaint_list.append({
                "complaint_id": c.id,
                "title": c.title,
                "description": c.description[:200] + "..." if len(c.description) > 200 else c.description,
                "status": c.status,
                "priority": c.priority,
                "upvotes": c.upvotes,
                "downvotes": c.downvotes,
                "net_votes": c.upvotes - c.downvotes,
                "category": c.llm_category,
                "student_name": c.student.name,
                "department": c.student.department,
                "submitted_at": c.submitted_at.isoformat(),
                "image_url": c.image_url
            })
        
        logger.info(f"📋 Retrieved {len(complaint_list)} complaints for {authority_name}")
        
        return {
            "success": True,
            "authority_type": authority_type,
            "authority_name": authority_name,
            "count": len(complaint_list),
            "complaints": complaint_list
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving authority complaints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving complaints: {str(e)}"
        )

# ============================================
# ENDPOINT 10: RECALCULATE PRIORITY
# ============================================

@router.post(
    "/complaints/{complaint_id}/recalculate-priority",
    summary="Recalculate complaint priority",
    description="Recalculate priority based on AI analysis and current votes"
)
async def recalculate_priority(
    complaint_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Recalculate complaint priority
    
    Combines:
    - AI-detected priority
    - Current vote count
    - Urgency score
    - Impact level
    
    **Returns:**
    New priority and score
    """
    try:
        db_service = DatabaseService(db)
        
        # Get complaint
        complaint = await db_service.get_complaint(complaint_id)
        if not complaint:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint {complaint_id} not found"
            )
        
        # Parse LLM analysis
        llm_analysis = None
        if complaint.llm_analysis:
            try:
                llm_analysis = json.loads(complaint.llm_analysis)
            except:
                pass
        
        # If no analysis, create one
        if not llm_analysis:
            llm_analysis = await llm_service.analyze_complaint(
                title=complaint.title,
                description=complaint.description
            )
        
        # Calculate new priority score
        priority_score = await llm_service.calculate_priority_score(
            analysis=llm_analysis,
            upvotes=complaint.upvotes
        )
        
        # Determine priority label
        new_priority = llm_service.get_priority_label(priority_score)
        
        old_priority = complaint.priority
        
        # Update in database
        await db_service.update_complaint_priority(
            complaint_id=complaint_id,
            priority=new_priority
        )
        
        # Update priority score
        stmt = update(ComplaintDB).where(
            ComplaintDB.id == complaint_id
        ).values(
            llm_priority_score=priority_score
        )
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"📊 Priority recalculated for {complaint_id}: {new_priority} ({priority_score})")
        
        return {
            "success": True,
            "complaint_id": complaint_id,
            "old_priority": old_priority,
            "new_priority": new_priority,
            "priority_score": priority_score,
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Priority recalculation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recalculating priority: {str(e)}"
        )

# ============================================
# BONUS ENDPOINTS
# ============================================

@router.get(
    "/stats",
    summary="Get overall statistics",
    description="Get system-wide statistics"
)
async def get_overall_stats(db: AsyncSession = Depends(get_db)):
    """Get overall system statistics"""
    try:
        db_service = DatabaseService(db)
        stats = await db_service.get_overall_stats()
        
        return {
            "success": True,
            **stats
        }
    
    except Exception as e:
        logger.error(f"❌ Error retrieving stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving stats: {str(e)}"
        )

@router.get(
    "/health",
    summary="Health check",
    description="Check API health status"
)
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "service": "CampusVoice Backend",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get(
    "/ws/stats",
    summary="WebSocket statistics",
    description="Get WebSocket connection statistics"
)
async def websocket_stats():
    """Get WebSocket connection statistics"""
    stats = manager.get_stats()
    return {
        "success": True,
        **stats
    }

# ============================================
# EXPORT
# ============================================

__all__ = ["router"]
