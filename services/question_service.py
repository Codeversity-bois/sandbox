"""Service for fetching questions from qa_gen_spice database."""
from typing import Optional, List, Dict, Any
from models.database import get_database
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from bson import ObjectId
import random


class QuestionService:
    """Service to fetch pre-generated questions from database."""
    
    def __init__(self):
        """Initialize separate connection to qa_gen_db for reading questions."""
        self._qa_client = None
        self._qa_db = None
    
    def _get_qa_database(self):
        """Get qa_gen_db database instance for reading questions."""
        if self._qa_client is None:
            self._qa_client = AsyncIOMotorClient(settings.MONGODB_URL)
            self._qa_db = self._qa_client["qa_gen_db"]  # Always use qa_gen_db for questions
        return self._qa_db
    
    async def fetch_question(
        self,
        question_type: str,
        difficulty: Optional[str] = None,
        topic: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch a random question from database based on criteria.
        
        Args:
            question_type: "code" or "apti"
            difficulty: Optional difficulty filter (easy, medium, hard)
            topic: Optional topic filter
            job_id: Optional job ID filter
            
        Returns:
            Question dict or None if not found
        """
        qa_db = self._get_qa_database()  # Use qa_gen_db for questions
        qa_db = self._get_qa_database()  # Use qa_gen_db for questions
        
        # Build query
        query = {"question_type": question_type}
        
        if difficulty:
            query["difficulty"] = difficulty
            
        if topic:
            query["topics"] = topic
        
        if job_id:
            query["job_id"] = job_id
        
        # Debug logging
        print(f"\n[QuestionService] Fetching question with query: {query}")
        print(f"[QuestionService] Using database: qa_gen_db")
        
        # Get all matching questions
        questions = await qa_db.dsa_questions.find(query).to_list(length=None)
        
        print(f"[QuestionService] Found {len(questions)} matching questions")
        
        if not questions:
            # Debug: Check what's actually in the database
            total_count = await qa_db.dsa_questions.count_documents({"question_type": question_type})
            print(f"[QuestionService] Total {question_type} questions in DB: {total_count}")
            
            # Check if any questions have the job_id field
            if job_id:
                with_job_id = await qa_db.dsa_questions.count_documents({"question_type": question_type, "job_id": {"$exists": True}})
                print(f"[QuestionService] Questions with job_id field: {with_job_id}")
                
                # Show sample job_id values
                sample = await qa_db.dsa_questions.find({"question_type": question_type, "job_id": {"$exists": True}}).limit(5).to_list(length=5)
                if sample:
                    job_ids = [q.get("job_id") for q in sample]
                    print(f"[QuestionService] Sample job_id values in DB: {job_ids}")
            
            return None
        
        # Pick a random question
        question = random.choice(questions)
        
        # Convert ObjectId to string
        if "_id" in question:
            question["_id"] = str(question["_id"])
        
        print(f"[QuestionService] Returning question: {question.get('title', 'N/A')} (job_id: {question.get('job_id', 'None')})")
        
        return question
    
    async def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific question by ID.
        
        Args:
            question_id: MongoDB ObjectId as string
            
        Returns:
            Question dict or None
        """
        qa_db = self._get_qa_database()  # Use qa_gen_db for questions
        
        try:
            question = await qa_db.dsa_questions.find_one({"_id": ObjectId(question_id)})
            
            if question:
                question["_id"] = str(question["_id"])
            
            return question
        except Exception:
            return None
    
    async def list_questions(
        self,
        question_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        topic: Optional[str] = None,
        job_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List questions with optional filters.
        
        Args:
            question_type: Optional filter by "code" or "apti"
            difficulty: Optional difficulty filter
            topic: Optional topic filter
            job_id: Optional job ID filter
            limit: Maximum number of questions to return
            
        Returns:
            List of question dicts
        """
        qa_db = self._get_qa_database()  # Use qa_gen_db for questions
        
        # Build query
        query = {}
        
        if question_type:
            query["question_type"] = question_type
            
        if difficulty:
            query["difficulty"] = difficulty
            
        if topic:
            query["topics"] = topic
        
        if job_id:
            query["job_id"] = job_id
        
        # Fetch questions
        questions = await qa_db.dsa_questions.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        # Convert ObjectIds to strings
        for q in questions:
            if "_id" in q:
                q["_id"] = str(q["_id"])
        
        return questions
    
    async def get_question_count(
        self,
        question_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> int:
        """Get count of questions matching criteria.
        
        Args:
            question_type: Optional filter by "code" or "apti"
            difficulty: Optional difficulty filter
            job_id: Optional job ID filter
            
        Returns:
            Count of matching questions
        """
        qa_db = self._get_qa_database()  # Use qa_gen_db for questions
        
        query = {}
        
        if question_type:
            query["question_type"] = question_type
            
        if difficulty:
            query["difficulty"] = difficulty
        
        if job_id:
            query["job_id"] = job_id
        
        count = await qa_db.dsa_questions.count_documents(query)
        return count
    
    async def get_available_job_ids(self) -> List[str]:
        """Get list of all unique job IDs that have questions.
        
        Returns:
            List of job ID strings
        """
        qa_db = self._get_qa_database()  # Use qa_gen_db for questions
        
        # Get distinct job_id values from the collection
        job_ids = await qa_db.dsa_questions.distinct("job_id")
        
        # Filter out None values
        job_ids = [job_id for job_id in job_ids if job_id is not None and job_id != ""]
        
        return sorted(job_ids)


question_service = QuestionService()
