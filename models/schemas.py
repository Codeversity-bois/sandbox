from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ModeEnum(str, Enum):
    CODE = "code"
    APTI = "apti"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionRequest(BaseModel):
    mode: ModeEnum
    difficulty: Optional[QuestionDifficulty] = QuestionDifficulty.MEDIUM
    topic: Optional[str] = None
    job_id: Optional[str] = None  # Filter questions by job ID
    user_id: Optional[str] = None  # Optional user ID for tracking


class AptitudeQuestion(BaseModel):
    question_id: str
    question_text: str
    options: Optional[List[str]] = None
    difficulty: QuestionDifficulty
    topic: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class CodeQuestion(BaseModel):
    question_id: str
    title: str
    description: str
    difficulty: QuestionDifficulty
    topic: str
    test_cases: List[Dict[str, Any]]
    starter_code: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class AptitudeSubmission(BaseModel):
    user_id: str
    question_id: str
    user_answer: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class CodeSubmission(BaseModel):
    user_id: str
    question_id: str
    code: str
    language: str = "python"
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationResult(BaseModel):
    submission_id: str
    is_correct: bool
    score: float
    feedback: str
    detailed_explanation: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class UserAttemptSummary(BaseModel):
    user_id: str
    mode: ModeEnum
    question_id: str
    question_text: str
    user_answer: str
    correct_answer: Optional[str] = None
    is_correct: bool
    why_wrong: Optional[str] = None
    learning_points: Optional[List[str]] = None
    attempted_at: datetime = Field(default_factory=datetime.utcnow)


class CodeExecutionResult(BaseModel):
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    test_results: Optional[List[Dict[str, Any]]] = None
