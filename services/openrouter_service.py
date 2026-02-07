import httpx
import json
from typing import Dict, Any, Optional
from config import settings


class OpenRouterService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_MODEL

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate completion using OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Sandbox Environment",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

    async def generate_aptitude_question(
        self, difficulty: str, topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate an aptitude question"""
        topic_text = f" on the topic of {topic}" if topic else ""
        system_prompt = "You are an expert at creating aptitude test questions. Generate questions that test logical reasoning, quantitative ability, and problem-solving skills."

        prompt = f"""Generate a {difficulty} difficulty aptitude question{topic_text}.
        
Return the response as a JSON object with the following structure:
{{
    "question_text": "The question text",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "The correct option letter (A, B, C, or D)",
    "explanation": "Detailed explanation of why this is the correct answer",
    "topic": "The topic of the question"
}}

Make the question challenging and relevant."""

        response = await self.generate_completion(prompt, system_prompt)
        # Extract JSON from response (handle potential markdown formatting)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

    async def generate_code_question(
        self, difficulty: str, topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a coding question"""
        topic_text = f" related to {topic}" if topic else ""
        system_prompt = "You are an expert at creating coding challenges. Generate practical programming problems that test algorithmic thinking and coding skills."

        prompt = f"""Generate a {difficulty} difficulty coding problem{topic_text}.

Return the response as a JSON object with the following structure:
{{
    "title": "Problem title",
    "description": "Detailed problem description with constraints",
    "topic": "The topic/category",
    "test_cases": [
        {{"input": "test input", "expected_output": "expected output", "description": "what this tests"}},
        // at least 3 test cases
    ],
    "starter_code": "def solution():\\n    # Write your code here\\n    pass",
    "solution_explanation": "How to approach this problem"
}}

Make it challenging but solvable."""

        response = await self.generate_completion(prompt, system_prompt)
        # Extract JSON from response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

    async def evaluate_aptitude_answer(
        self, question: str, correct_answer: str, user_answer: str, explanation: str
    ) -> Dict[str, Any]:
        """Evaluate an aptitude answer and provide feedback"""
        system_prompt = "You are an expert tutor evaluating student answers. Provide constructive feedback."

        prompt = f"""Question: {question}

Correct Answer: {correct_answer}
Explanation: {explanation}

Student's Answer: {user_answer}

Evaluate if the student's answer is correct. If wrong, explain why and provide learning points.

Return JSON:
{{
    "is_correct": true/false,
    "score": 0-100,
    "feedback": "Brief feedback",
    "why_wrong": "Detailed explanation if wrong, null if correct",
    "learning_points": ["key point 1", "key point 2"]
}}"""

        response = await self.generate_completion(
            prompt, system_prompt, temperature=0.3
        )
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())

    async def evaluate_code_output(
        self,
        question: str,
        test_cases: list,
        code: str,
        execution_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate code execution results"""
        system_prompt = (
            "You are an expert code reviewer. Evaluate code quality and correctness."
        )

        prompt = f"""Problem: {question}

Test Cases: {json.dumps(test_cases, indent=2)}

Student's Code:
```python
{code}
```

Execution Results: {json.dumps(execution_results, indent=2)}

Evaluate the code and provide feedback.

Return JSON:
{{
    "is_correct": true/false,
    "score": 0-100,
    "feedback": "Overall feedback",
    "why_wrong": "What went wrong if incorrect, null if correct",
    "learning_points": ["improvement 1", "improvement 2"]
}}"""

        response = await self.generate_completion(
            prompt, system_prompt, temperature=0.3
        )
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        return json.loads(response.strip())


# Singleton instance
openrouter_service = OpenRouterService()
