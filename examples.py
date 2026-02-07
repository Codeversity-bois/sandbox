"""
Example usage of the Sandbox API with different scenarios
"""

import asyncio
import httpx
from typing import Dict, Any


class SandboxClient:
    """Client for interacting with the Sandbox API"""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def close(self):
        await self.client.aclose()

    async def generate_aptitude_question(
        self, user_id: str, difficulty: str = "medium", topic: str = None
    ) -> Dict[str, Any]:
        """Generate an aptitude question"""
        response = await self.client.post(
            f"{self.base_url}/aptitude/generate-question",
            json={
                "mode": "apti",
                "difficulty": difficulty,
                "topic": topic,
                "user_id": user_id,
            },
        )
        response.raise_for_status()
        return response.json()

    async def submit_aptitude_answer(
        self, user_id: str, question_id: str, answer: str
    ) -> Dict[str, Any]:
        """Submit an aptitude answer"""
        response = await self.client.post(
            f"{self.base_url}/aptitude/submit-answer",
            json={
                "user_id": user_id,
                "question_id": question_id,
                "user_answer": answer,
            },
        )
        response.raise_for_status()
        return response.json()

    async def generate_code_question(
        self, user_id: str, difficulty: str = "medium", topic: str = None
    ) -> Dict[str, Any]:
        """Generate a coding question"""
        response = await self.client.post(
            f"{self.base_url}/code/generate-question",
            json={
                "mode": "code",
                "difficulty": difficulty,
                "topic": topic,
                "user_id": user_id,
            },
        )
        response.raise_for_status()
        return response.json()

    async def submit_code(
        self, user_id: str, question_id: str, code: str, language: str = "python"
    ) -> Dict[str, Any]:
        """Submit code solution"""
        response = await self.client.post(
            f"{self.base_url}/code/submit-code",
            json={
                "user_id": user_id,
                "question_id": question_id,
                "code": code,
                "language": language,
            },
        )
        response.raise_for_status()
        return response.json()

    async def run_code(self, code: str, user_id: str = "test") -> Dict[str, Any]:
        """Run code without evaluation"""
        response = await self.client.post(
            f"{self.base_url}/code/run-code",
            json={
                "user_id": user_id,
                "question_id": "test",
                "code": code,
                "language": "python",
            },
        )
        response.raise_for_status()
        return response.json()


async def example_aptitude_workflow():
    """Example: Complete aptitude question workflow"""
    client = SandboxClient()
    user_id = "demo_user_1"

    try:
        # Generate a question
        print("Generating aptitude question...")
        question = await client.generate_aptitude_question(
            user_id=user_id, difficulty="medium", topic="mathematics"
        )

        print(f"\nQuestion: {question['question_text']}")
        print("\nOptions:")
        for option in question["options"]:
            print(f"  {option}")

        # Simulate user answering
        user_answer = "A"  # User's choice

        # Submit answer
        print(f"\nSubmitting answer: {user_answer}")
        result = await client.submit_aptitude_answer(
            user_id=user_id, question_id=question["question_id"], answer=user_answer
        )

        print(f"\nResult:")
        print(f"  Correct: {result['is_correct']}")
        print(f"  Score: {result['score']}/100")
        print(f"  Feedback: {result['feedback']}")

        if not result["is_correct"]:
            print(f"\n  Why wrong: {result['why_wrong']}")
            print("\n  Learning points:")
            for point in result.get("learning_points", []):
                print(f"    - {point}")

    finally:
        await client.close()


async def example_code_workflow():
    """Example: Complete coding question workflow"""
    client = SandboxClient()
    user_id = "demo_user_2"

    try:
        # Generate a coding challenge
        print("Generating coding challenge...")
        challenge = await client.generate_code_question(
            user_id=user_id, difficulty="easy", topic="strings"
        )

        print(f"\nChallenge: {challenge['title']}")
        print(f"\nDescription:\n{challenge['description']}")
        print(f"\nStarter code:\n{challenge['starter_code']}")

        # User writes solution
        solution = """
def solution(s):
    # Reverse the string
    return s[::-1]

# Handle test input
import sys
if hasattr(sys, 'stdin'):
    data = sys.stdin.read().strip()
    if data:
        print(solution(data))
"""

        # Submit solution
        print("\nSubmitting solution...")
        result = await client.submit_code(
            user_id=user_id, question_id=challenge["question_id"], code=solution
        )

        print(f"\nResult:")
        print(f"  Correct: {result['is_correct']}")
        print(f"  Score: {result['score']}/100")
        print(
            f"  Tests passed: {result['execution_result']['passed_tests']}/{result['execution_result']['total_tests']}"
        )
        print(f"  Feedback: {result['feedback']}")

        # Show test results
        print("\n  Test Results:")
        for test in result["execution_result"]["test_results"]:
            status = "✓" if test["passed"] else "✗"
            print(f"    {status} Test {test['test_case']}")

    finally:
        await client.close()


async def example_quick_code_test():
    """Example: Quick code testing without questions"""
    client = SandboxClient()

    try:
        # Test some Python code quickly
        code = """
# Calculate fibonacci numbers
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Print first 10 fibonacci numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
"""

        print("Running code in sandbox...")
        result = await client.run_code(code)

        print(f"\nSuccess: {result['success']}")
        print(f"\nOutput:\n{result['output']}")
        print(f"\nExecution time: {result['execution_time']:.3f}s")

    finally:
        await client.close()


async def main():
    """Run all examples"""
    print("=" * 70)
    print("EXAMPLE 1: Aptitude Question Workflow")
    print("=" * 70)
    await example_aptitude_workflow()

    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: Coding Challenge Workflow")
    print("=" * 70)
    await example_code_workflow()

    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: Quick Code Testing")
    print("=" * 70)
    await example_quick_code_test()

    print("\n\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
