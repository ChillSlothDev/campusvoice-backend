"""
LLM Service for Complaint Analysis
Groq API integration for intelligent complaint processing
"""

from groq import Groq
import json
import os
from typing import Dict, Optional
import logging
from dotenv import load_dotenv
import asyncio
from functools import wraps

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# ASYNC WRAPPER FOR GROQ (Sync to Async)
# ============================================

def async_wrap(func):
    """
    Decorator to run sync functions in async context
    Groq SDK is synchronous, so we wrap it for async usage
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper

# ============================================
# LLM SERVICE CLASS
# ============================================

class LLMService:
    """
    Service for LLM-based complaint analysis using Groq
    
    Features:
    - Automatic priority detection
    - Category classification (with improved rules)
    - Sentiment analysis
    - Resolution suggestions
    - Authority routing
    - Dynamic priority scoring
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,  # Lower for consistent categorization
        max_tokens: int = 500
    ):
        """
        Initialize LLM service
        
        Args:
            api_key: Groq API key (defaults to env variable)
            model: Model name (defaults to mixtral-8x7b-32768)
            temperature: Model temperature (0.0-1.0, lower = more consistent)
            max_tokens: Max tokens in response
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            logger.warning("⚠️  GROQ_API_KEY not found. LLM features will be disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"✅ Groq LLM initialized with model: {self.model}")
    
    def _is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None
    
    # ============================================
    # IMPROVED COMPLAINT ANALYSIS
    # ============================================
    
    @async_wrap
    def _sync_analyze_complaint(self, title: str, description: str) -> Dict:
        """
        Synchronous complaint analysis (wrapped for async)
        
        Internal method - use analyze_complaint() instead
        """
        prompt = f"""Analyze this campus complaint and provide a structured response.

Complaint Title: {title}
Complaint Description: {description}

You are analyzing a complaint from an engineering college campus. Carefully categorize based on these rules:

CATEGORY RULES (VERY IMPORTANT):
- "food": Mess, canteen, food quality, hygiene, menu, food timing, dining hall issues
- "infrastructure": Buildings, classrooms, labs, maintenance, AC, fans, lights, electricity, water supply, furniture, equipment, wifi (except hostel wifi), library infrastructure (AC, furniture, space)
- "academic": Classes, exams, faculty, curriculum, library BOOKS/RESOURCES, timetable, course content
- "hostel": Hostel rooms, hostel facilities, hostel mess, hostel rules, roommates, hostel wifi, hostel maintenance
- "transport": College bus, transport timing, vehicle issues, parking, shuttle service
- "other": Everything else not clearly fitting above

PRIORITY RULES:
- "critical": Safety hazards, health emergencies, major infrastructure failure affecting many students, fire/electrical hazards
- "high": Significant disruption to academics or daily life, urgent repairs needed, affecting multiple people or important facilities
- "medium": Moderate issues that need attention but not urgent, affecting individuals or small groups, quality issues
- "low": Minor inconveniences, suggestions, cosmetic issues, low-impact problems

IMPORTANT EXAMPLES:
- "Library AC not working" = INFRASTRUCTURE (not academic)
- "Library books missing" = ACADEMIC (not infrastructure)
- "Mess food quality" = FOOD
- "Hostel wifi slow" = HOSTEL (not infrastructure)
- "Classroom projector broken" = INFRASTRUCTURE
- "Professor teaching method" = ACADEMIC

Provide analysis in the following JSON format ONLY (no other text):
{{
    "priority": "low" | "medium" | "high" | "critical",
    "category": "food" | "infrastructure" | "academic" | "hostel" | "transport" | "other",
    "sentiment": "negative" | "neutral" | "positive",
    "urgency_score": 0-100,
    "impact_level": "individual" | "group" | "campus-wide",
    "summary": "Brief 1-sentence summary of the core issue",
    "key_issues": ["issue1", "issue2", "issue3"],
    "suggested_authority": "Name of the department/authority that should handle this"
}}

Be very careful with categorization. Think step by step about which category fits best."""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a campus complaint analysis system for an engineering college. Provide structured, accurate JSON responses ONLY. Pay close attention to proper categorization based on the rules provided."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=self.temperature,  # Low temperature for consistency
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            response_text = chat_completion.choices[0].message.content
            analysis = json.loads(response_text)
            
            logger.info(f"✅ LLM Analysis complete: Priority={analysis.get('priority')}, Category={analysis.get('category')}")
            
            return analysis
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            return self._get_fallback_analysis()
        
        except Exception as e:
            logger.error(f"❌ LLM API error: {e}")
            return self._get_fallback_analysis()
    
    async def analyze_complaint(self, title: str, description: str) -> Dict:
        """
        Analyze complaint and return structured insights
        
        Args:
            title: Complaint title
            description: Complaint description
        
        Returns:
            dict: {
                "priority": str,
                "category": str,
                "sentiment": str,
                "urgency_score": int,
                "impact_level": str,
                "summary": str,
                "key_issues": list,
                "suggested_authority": str
            }
        """
        if not self._is_available():
            logger.warning("⚠️  LLM service unavailable, using fallback analysis")
            return self._get_fallback_analysis()
        
        try:
            return await self._sync_analyze_complaint(title, description)
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            return self._get_fallback_analysis()
    
    # ============================================
    # PRIORITY CALCULATION (AI + VOTING)
    # ============================================
    
    async def calculate_priority_score(self, analysis: Dict, upvotes: int = 0, downvotes: int = 0) -> int:
        """
        Calculate numeric priority score based on LLM analysis and votes
        
        Combines:
        - AI-detected base priority
        - Urgency score from AI
        - Impact level from AI
        - Community voting (upvotes boost, downvotes reduce)
        
        Args:
            analysis: LLM analysis result
            upvotes: Number of upvotes
            downvotes: Number of downvotes
        
        Returns:
            int: Priority score (0-2000)
        """
        score = 0
        
        # Base priority score from AI
        priority_scores = {
            "low": 100,
            "medium": 300,
            "high": 700,
            "critical": 1500
        }
        score += priority_scores.get(analysis.get("priority", "medium"), 300)
        
        # Urgency score from AI
        score += analysis.get("urgency_score", 50)
        
        # Impact level from AI
        impact_scores = {
            "individual": 50,
            "group": 150,
            "campus-wide": 300
        }
        score += impact_scores.get(analysis.get("impact_level", "individual"), 50)
        
        # Vote influence (upvotes boost, downvotes reduce)
        net_votes = upvotes - (downvotes * 0.5)  # Downvotes have half weight
        score += max(0, net_votes * 5)  # Each net upvote adds 5 points
        
        # Cap at 2000
        return min(int(score), 2000)
    
    def get_priority_label(self, priority_score: int) -> str:
        """
        Convert priority score to label
        
        Args:
            priority_score: Numeric priority score
        
        Returns:
            str: Priority label (low, medium, high, critical)
        """
        if priority_score >= 1500:
            return "critical"
        elif priority_score >= 700:
            return "high"
        elif priority_score >= 300:
            return "medium"
        else:
            return "low"
    
    # ============================================
    # AUTHORITY ROUTING (IMPROVED)
    # ============================================
    
    def get_authority_from_category(self, category: str) -> Dict[str, str]:
        """
        Get authority contact based on complaint category
        
        Args:
            category: Complaint category
        
        Returns:
            dict: {"authority": str, "email": str, "department": str}
        """
        authority_map = {
            "food": {
                "authority": "Mess Committee Head",
                "email": "mess@srec.ac.in",
                "department": "Mess & Catering Services"
            },
            "infrastructure": {
                "authority": "Maintenance Officer",
                "email": "maintenance@srec.ac.in",
                "department": "Infrastructure & Maintenance"
            },
            "academic": {
                "authority": "Academic Dean",
                "email": "academics@srec.ac.in",
                "department": "Academic Affairs"
            },
            "hostel": {
                "authority": "Hostel Warden",
                "email": "hostel@srec.ac.in",
                "department": "Hostel Administration"
            },
            "transport": {
                "authority": "Transport Coordinator",
                "email": "transport@srec.ac.in",
                "department": "Transport Services"
            },
            "other": {
                "authority": "Student Affairs Officer",
                "email": "studentaffairs@srec.ac.in",
                "department": "Student Affairs"
            }
        }
        
        result = authority_map.get(category.lower(), authority_map["other"])
        logger.info(f"🏛️  Routed to: {result['authority']} (Category: {category})")
        return result
    
    # ============================================
    # RESOLUTION SUGGESTIONS
    # ============================================
    
    @async_wrap
    def _sync_suggest_resolution(self, title: str, description: str, category: str) -> str:
        """
        Synchronous resolution suggestion (wrapped for async)
        """
        prompt = f"""Suggest actionable resolution steps for this campus complaint.

Title: {title}
Description: {description}
Category: {category}

Provide 3-5 specific, actionable steps that the assigned authority can take to resolve this issue.
Format as a numbered list. Be practical and campus-specific."""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a campus administration advisor. Provide practical, actionable resolution steps."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.4,
                max_tokens=400
            )
            
            resolution = chat_completion.choices[0].message.content
            logger.info("✅ Resolution suggestions generated")
            return resolution
        
        except Exception as e:
            logger.error(f"❌ Resolution suggestion error: {e}")
            return "Unable to generate resolution suggestions. Please review manually."
    
    async def suggest_resolution(self, title: str, description: str, category: str = "other") -> str:
        """
        Generate resolution suggestions for a complaint
        
        Args:
            title: Complaint title
            description: Complaint description
            category: Complaint category
        
        Returns:
            str: Resolution suggestions
        """
        if not self._is_available():
            return "LLM service unavailable. Manual review required."
        
        try:
            return await self._sync_suggest_resolution(title, description, category)
        except Exception as e:
            logger.error(f"❌ Suggestion error: {e}")
            return "Error generating suggestions. Manual review required."
    
    # ============================================
    # BATCH PROCESSING
    # ============================================
    
    async def analyze_multiple_complaints(self, complaints: list) -> list:
        """
        Analyze multiple complaints in batch
        
        Args:
            complaints: List of dicts with 'title' and 'description'
        
        Returns:
            list: List of analysis results
        """
        tasks = [
            self.analyze_complaint(c["title"], c["description"])
            for c in complaints
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [
            r if not isinstance(r, Exception) else self._get_fallback_analysis()
            for r in results
        ]
        
        return valid_results
    
    # ============================================
    # FALLBACK & UTILITIES
    # ============================================
    
    def _get_fallback_analysis(self) -> Dict:
        """
        Get fallback analysis when LLM is unavailable
        
        Returns:
            dict: Default analysis structure
        """
        return {
            "priority": "medium",
            "category": "other",
            "sentiment": "neutral",
            "urgency_score": 50,
            "impact_level": "individual",
            "summary": "Complaint requires manual review",
            "key_issues": ["Manual review required"],
            "suggested_authority": "Student Affairs Officer"
        }
    
    async def validate_analysis(self, analysis: Dict) -> bool:
        """
        Validate that analysis has required fields
        
        Args:
            analysis: Analysis dictionary
        
        Returns:
            bool: True if valid
        """
        required_fields = ["priority", "category", "summary"]
        return all(field in analysis for field in required_fields)
    
    # ============================================
    # TESTING & DEBUGGING
    # ============================================
    
    async def test_connection(self) -> bool:
        """
        Test LLM API connection
        
        Returns:
            bool: True if connection successful
        """
        if not self._is_available():
            logger.error("❌ LLM service not configured")
            return False
        
        try:
            test_result = await self.analyze_complaint(
                title="Test complaint",
                description="This is a test to verify API connection"
            )
            
            is_valid = await self.validate_analysis(test_result)
            
            if is_valid:
                logger.info("✅ LLM connection test passed")
                return True
            else:
                logger.error("❌ LLM connection test failed: Invalid response")
                return False
        
        except Exception as e:
            logger.error(f"❌ LLM connection test failed: {e}")
            return False

# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

async def quick_analyze(title: str, description: str) -> Dict:
    """
    Quick analysis function for standalone use
    
    Args:
        title: Complaint title
        description: Complaint description
    
    Returns:
        dict: Analysis result
    """
    service = LLMService()
    return await service.analyze_complaint(title, description)

# ============================================
# EXPORT
# ============================================

__all__ = [
    "LLMService",
    "quick_analyze"
]
