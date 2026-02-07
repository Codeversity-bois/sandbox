#!/usr/bin/env python3
"""
Example script to test the Sandbox API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "test_user_123"


def test_aptitude_mode():
    """Test aptitude question generation and evaluation"""
    print("\n" + "=" * 60)
    print("TESTING APTITUDE MODE")
    print("=" * 60)

    # Generate question
    print("\n1. Generating aptitude question...")
    response = requests.post(
        f"{BASE_URL}/aptitude/generate-question",
        json={
            "mode": "apti",
            "difficulty": "medium",
            "topic": "logical reasoning",
            "user_id": USER_ID,
        },
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    question = response.json()
    print(f"✅ Question generated: {question['question_id']}")
    print(f"\nQuestion: {question['question_text']}")
    print("\nOptions:")
    for option in question["options"]:
        print(f"  {option}")

    question_id = question["question_id"]

    # Submit answer
    print("\n2. Submitting answer (A)...")
    response = requests.post(
        f"{BASE_URL}/aptitude/submit-answer",
        json={"user_id": USER_ID, "question_id": question_id, "user_answer": "A"},
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    result = response.json()
    print(f"✅ Answer submitted")
    print(f"\nIs Correct: {result['is_correct']}")
    print(f"Score: {result['score']}/100")
    print(f"Feedback: {result['feedback']}")

    if not result["is_correct"]:
        print(f"\n📚 Learning Points:")
        for point in result.get("learning_points", []):
            print(f"  • {point}")

    # Get user summary
    print("\n3. Fetching user summary...")
    response = requests.get(f"{BASE_URL}/aptitude/user-summary/{USER_ID}")

    if response.status_code == 200:
        summary = response.json()
        print(f"✅ Summary retrieved")
        print(f"\nTotal wrong answers: {summary['total_wrong_answers']}")
        print(f"Topics with mistakes: {summary['topics_with_mistakes']}")


def test_code_mode():
    """Test code question generation and execution"""
    print("\n" + "=" * 60)
    print("TESTING CODE MODE")
    print("=" * 60)

    # Generate coding question
    print("\n1. Generating coding challenge...")
    response = requests.post(
        f"{BASE_URL}/code/generate-question",
        json={
            "mode": "code",
            "difficulty": "easy",
            "topic": "arrays",
            "user_id": USER_ID,
        },
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return

    challenge = response.json()
    print(f"✅ Challenge generated: {challenge['question_id']}")
    print(f"\nTitle: {challenge['title']}")
    print(f"\nDescription:\n{challenge['description']}")
    print(f"\nStarter Code:\n{challenge['starter_code']}")

    question_id = challenge["question_id"]

    # Test simple code execution
    print("\n2. Testing simple code execution...")
    test_code = """
print('Hello from Docker sandbox!')
print('2 + 2 =', 2 + 2)

# Test some Python features
numbers = [1, 2, 3, 4, 5]
print('Sum:', sum(numbers))
"""

    response = requests.post(
        f"{BASE_URL}/code/run-code",
        json={
            "user_id": USER_ID,
            "question_id": "test",
            "code": test_code,
            "language": "python",
        },
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Code executed successfully")
        print(f"\nOutput:\n{result['output']}")
        print(f"Execution time: {result['execution_time']:.3f}s")
    else:
        print(f"❌ Error: {response.text}")

    # Submit solution
    print("\n3. Submitting a solution...")
    solution_code = """
def solution(arr):
    # Sort the array
    return sorted(arr)

# If there's test input, use it
import sys
if hasattr(sys, 'stdin'):
    data = sys.stdin.read().strip()
    if data:
        arr = list(map(int, data.split()))
        print(solution(arr))
"""

    response = requests.post(
        f"{BASE_URL}/code/submit-code",
        json={
            "user_id": USER_ID,
            "question_id": question_id,
            "code": solution_code,
            "language": "python",
        },
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Solution submitted")
        print(f"\nCorrect: {result['is_correct']}")
        print(f"Score: {result['score']}/100")
        print(
            f"Passed Tests: {result['execution_result']['passed_tests']}/{result['execution_result']['total_tests']}"
        )
        print(f"Feedback: {result['feedback']}")

        if result["execution_result"]["test_results"]:
            print("\nTest Results:")
            for test in result["execution_result"]["test_results"]:
                status = "✓" if test["passed"] else "✗"
                print(f"  {status} Test {test['test_case']}")
    else:
        print(f"❌ Error: {response.text}")

    # Get user summary
    print("\n4. Fetching user summary...")
    response = requests.get(f"{BASE_URL}/code/user-summary/{USER_ID}")

    if response.status_code == 200:
        summary = response.json()
        print(f"✅ Summary retrieved")
        print(f"\nTotal wrong answers: {summary['total_wrong_answers']}")
        print(f"Topics with mistakes: {summary['topics_with_mistakes']}")


def test_health():
    """Test API health"""
    print("\n" + "=" * 60)
    print("TESTING API HEALTH")
    print("=" * 60)

    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print("✅ API is healthy")
        print(json.dumps(response.json(), indent=2))
    else:
        print("❌ API health check failed")


def main():
    """Run all tests"""
    print("\n🧪 Starting Sandbox API Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"User ID: {USER_ID}")

    try:
        # Check if API is running
        test_health()

        # Test aptitude mode
        test_aptitude_mode()

        # Wait a bit between tests
        time.sleep(1)

        # Test code mode
        test_code_mode()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API")
        print("Make sure the API is running: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
