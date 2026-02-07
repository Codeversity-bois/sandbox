from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import uuid
from datetime import datetime

from models.schemas import QuestionRequest, CodeQuestion, CodeSubmission, ModeEnum
from services.openrouter_service import openrouter_service
from services.docker_sandbox import docker_sandbox
from services.question_service import question_service
from models.database import get_database

router = APIRouter(prefix="/code", tags=["Code Mode"])


@router.post("/get-question", response_model=Dict[str, Any])
async def get_code_question(request: QuestionRequest):
    """Fetch a pre-generated coding question from database"""
    if request.mode != ModeEnum.CODE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for code mode only",
        )

    try:
        # Fetch question from database using question_service
        question = await question_service.fetch_question(
            question_type="code",
            difficulty=request.difficulty.value if request.difficulty else None,
            topic=request.topic,
            job_id=request.job_id
        )

        if not question:
            criteria_msg = f"criteria (difficulty={request.difficulty.value if request.difficulty else 'any'}, topic={request.topic or 'any'}, job_id={request.job_id or 'any'})"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No code questions available matching the {criteria_msg}. Please generate questions using qa_gen_spice service first."
            )

        question_id = question["_id"]
        test_cases = question.get("test_cases", [])
        
        # Show only non-hidden test cases
        visible_test_cases = [
            tc for tc in test_cases if not tc.get("is_hidden", False)
        ]

        # Return question (hide solution and hidden test cases)
        return {
            "question_id": question_id,
            "title": question.get("title"),
            "description": question.get("description"),
            "difficulty": question.get("difficulty"),
            "topic": question.get("topics", ["general"])[0] if question.get("topics") else "general",
            "starter_code": "# Write your code here\n",
            "test_cases_count": len(test_cases),
            "visible_test_cases": visible_test_cases,
            "constraints": question.get("constraints", []),
            "hints": question.get("hints", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch question: {str(e)}",
        )


@router.post("/submit-code", response_model=Dict[str, Any])
async def submit_code(submission: CodeSubmission):
    """Submit and evaluate code in Docker sandbox"""
    try:
        # Get the question from dsa_questions collection
        question = await question_service.get_question_by_id(submission.question_id)

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
            )
        
        db = get_database()

        # Get test cases from question
        test_cases = question.get("test_cases", [])
        
        # Execute code in Docker sandbox
        execution_result = await docker_sandbox.execute_code_with_tests(
            code=submission.code, test_cases=test_cases
        )

        # Evaluate using LLM
        evaluation = await openrouter_service.evaluate_code_output(
            question=question.get("description", ""),
            test_cases=test_cases,
            code=submission.code,
            execution_results=execution_result,
        )

        # Create submission record
        submission_id = str(uuid.uuid4())
        submission_record = {
            "submission_id": submission_id,
            "user_id": submission.user_id,
            "question_id": submission.question_id,
            "code": submission.code,
            "language": submission.language,
            "execution_result": execution_result,
            "is_correct": evaluation["is_correct"],
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "submitted_at": datetime.utcnow(),
        }

        await db.code_submissions.insert_one(submission_record)

        # Store summary if wrong
        if not evaluation["is_correct"]:
            summary = {
                "user_id": submission.user_id,
                "mode": "code",
                "question_id": submission.question_id,
                "question_text": question.get("title", ""),
                "user_answer": submission.code,
                "correct_answer": None,  # Don't store solution
                "is_correct": False,
                "why_wrong": evaluation.get("why_wrong"),
                "learning_points": evaluation.get("learning_points", []),
                "test_results": execution_result.get("test_results", []),
                "attempted_at": datetime.utcnow(),
            }
            await db.user_attempt_summaries.insert_one(summary)

        return {
            "submission_id": submission_id,
            "is_correct": evaluation["is_correct"],
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "execution_result": {
                "success": execution_result["success"],
                "total_tests": execution_result["total_tests"],
                "passed_tests": execution_result["passed_tests"],
                "test_results": execution_result["test_results"],
            },
            "why_wrong": evaluation.get("why_wrong"),
            "learning_points": evaluation.get("learning_points", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate code: {str(e)}",
        )


@router.post("/run-code", response_model=Dict[str, Any])
async def run_code(submission: CodeSubmission):
    """Run code without evaluation (for testing)"""
    try:
        # Execute code in Docker sandbox
        result = await docker_sandbox.execute_python_code(code=submission.code)

        return {
            "success": result["success"],
            "output": result.get("output"),
            "error": result.get("error"),
            "execution_time": result["execution_time"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run code: {str(e)}",
        )


@router.get("/user-summary/{user_id}", response_model=Dict[str, Any])
async def get_user_code_summary(user_id: str):
    """Get summary of user's code attempts (wrong answers)"""
    try:
        db = get_database()

        summaries = (
            await db.user_attempt_summaries.find({"user_id": user_id, "mode": "code"})
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
