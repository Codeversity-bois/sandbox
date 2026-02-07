from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import uuid
from datetime import datetime

from models.schemas import (
    QuestionRequest,
    AptitudeQuestion,
    AptitudeSubmission,
    EvaluationResult,
    UserAttemptSummary,
    ModeEnum,
)
from services.openrouter_service import openrouter_service
from services.question_service import question_service
from models.database import get_database

router = APIRouter(prefix="/aptitude", tags=["Aptitude Mode"])


@router.post("/get-question", response_model=Dict[str, Any])
async def get_aptitude_question(request: QuestionRequest):
    """Fetch a pre-generated aptitude question from database"""
    if request.mode != ModeEnum.APTI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for aptitude mode only",
        )

    try:
        # Fetch question from database using question_service
        question = await question_service.fetch_question(
            question_type="apti",
            difficulty=request.difficulty.value if request.difficulty else None,
            topic=request.topic,
            job_id=request.job_id
        )

        if not question:
            criteria_msg = f"criteria (difficulty={request.difficulty.value if request.difficulty else 'any'}, topic={request.topic or 'any'}, job_id={request.job_id or 'any'})"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No aptitude questions available matching the {criteria_msg}. Please generate questions using qa_gen_spice service first."
            )

        question_id = question["_id"]

        # Return question without correct answer
        return {
            "question_id": question_id,
            "question_text": question.get("description", question.get("title", "")),
            "options": question.get("options", []),
            "difficulty": question.get("difficulty"),
            "topic": question.get("topics", ["general"])[0] if question.get("topics") else "general",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch question: {str(e)}",
        )


@router.post("/submit-answer", response_model=Dict[str, Any])
async def submit_aptitude_answer(submission: AptitudeSubmission):
    """Submit and evaluate an aptitude answer"""
    try:
        db = get_database()

        # Get the question from dsa_questions collection
        question = await question_service.get_question_by_id(submission.question_id)

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
            )
        
        question_text = question.get("description", question.get("title", ""))
        correct_answer = question.get("correct_answer", "")
        
        # Use LLM for detailed evaluation
        evaluation = await openrouter_service.evaluate_aptitude_answer(
            question=question_text,
            correct_answer=correct_answer,
            user_answer=submission.user_answer,
            explanation=question.get("explanation", "")
        )
        
        # Create submission record
        submission_id = str(uuid.uuid4())
        submission_record = {
            "submission_id": submission_id,
            "user_id": submission.user_id,
            "question_id": submission.question_id,
            "user_answer": submission.user_answer,
            "is_correct": evaluation["is_correct"],
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "submitted_at": datetime.utcnow(),
        }

        await db.aptitude_submissions.insert_one(submission_record)

        # Store summary if wrong
        if not evaluation["is_correct"]:
            summary = {
                "user_id": submission.user_id,
                "mode": "apti",
                "question_id": submission.question_id,
                "question_text": question_text,
                "user_answer": submission.user_answer,
                "correct_answer": correct_answer,
                "is_correct": False,
                "why_wrong": evaluation.get("why_wrong"),
                "learning_points": evaluation.get("learning_points", []),
                "attempted_at": datetime.utcnow(),
            }
            await db.user_attempt_summaries.insert_one(summary)

        return {
            "submission_id": submission_id,
            "is_correct": evaluation["is_correct"],
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "correct_answer": (
                correct_answer if not evaluation["is_correct"] else None
            ),
            "why_wrong": evaluation.get("why_wrong"),
            "learning_points": evaluation.get("learning_points", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate answer: {str(e)}",
        )


@router.get("/user-summary/{user_id}", response_model=Dict[str, Any])
async def get_user_aptitude_summary(user_id: str):
    """Get summary of user's aptitude attempts (wrong answers)"""
    try:
        db = get_database()

        summaries = (
            await db.user_attempt_summaries.find({"user_id": user_id, "mode": "apti"})
            .sort("attempted_at", -1)
            .to_list(length=100)
        )

        # Calculate statistics
        total_wrong = len(summaries)
        topics = {}

        for summary in summaries:
            topic = summary.get("topic", "general")
            topics[topic] = topics.get(topic, 0) + 1

        return {
            "user_id": user_id,
            "total_wrong_answers": total_wrong,
            "topics_with_mistakes": topics,
            "recent_mistakes": summaries[:10],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user summary: {str(e)}",
        )
