"""
Example usage of code-sandbox API with qa_gen_spice integration

This script demonstrates how to:
1. Check available questions
2. Fetch a code question
3. Submit code solution
4. Fetch an aptitude question
5. Submit aptitude answer
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_question_stats(job_id=None):
    """Check how many questions are available"""
    print("=== Checking Question Statistics ===")
    
    url = f"{BASE_URL}/questions/stats"
    params = {}
    if job_id:
        params["job_id"] = job_id
        print(f"Filtering by job ID: {job_id}")
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        stats = response.json()
        print(json.dumps(stats, indent=2))
        return True
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return False


def get_available_job_ids():
    """Get list of all available job IDs"""
    print("\n=== Available Job IDs ===")
    response = requests.get(f"{BASE_URL}/questions/job-ids")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal job IDs: {data['total_job_ids']}")
        for job_info in data['job_ids']:
            print(f"\n  {job_info['job_id']}:")
            print(f"    Total: {job_info['total_questions']}")
            print(f"    Code: {job_info['code_questions']}")
            print(f"    Aptitude: {job_info['aptitude_questions']}")
        return data['job_ids']
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return []


def get_code_question(user_id="test_user", difficulty="easy", topic=None, job_id=None):
    """Fetch a code question from database"""
    print("\n=== Fetching Code Question ===")
    
    payload = {
        "mode": "code",
        "user_id": user_id,
        "difficulty": difficulty
    }
    
    if topic:
        payload["topic"] = topic
    
    if job_id:
        payload["job_id"] = job_id
        print(f"Filtering by job ID: {job_id}")
    
    response = requests.post(f"{BASE_URL}/code/get-question", json=payload)
    
    if response.status_code == 200:
        question = response.json()
        print(f"\nQuestion ID: {question['question_id']}")
        print(f"Title: {question['title']}")
        print(f"Difficulty: {question['difficulty']}")
        print(f"Description: {question['description'][:100]}...")
        print(f"Test Cases: {question['test_cases_count']}")
        print(f"\nVisible Test Cases:")
        for tc in question.get('visible_test_cases', []):
            print(f"  Input: {tc['input']}")
            print(f"  Expected: {tc['expected_output']}")
        
        if question.get('hints'):
            print(f"\nHints: {question['hints']}")
        
        return question['question_id']
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None


def submit_code(question_id, code, user_id="test_user"):
    """Submit code solution"""
    print("\n=== Submitting Code Solution ===")
    
    payload = {
        "user_id": user_id,
        "question_id": question_id,
        "code": code,
        "language": "python"
    }
    
    response = requests.post(f"{BASE_URL}/code/submit-code", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nSubmission ID: {result['submission_id']}")
        print(f"Correct: {result['is_correct']}")
        print(f"Score: {result['score']}")
        print(f"Feedback: {result['feedback']}")
        
        exec_result = result['execution_result']
        print(f"\nExecution Result:")
        print(f"  Total Tests: {exec_result['total_tests']}")
        print(f"  Passed: {exec_result['passed_tests']}")
        
        if not result['is_correct']:
            print(f"\nWhy Wrong: {result.get('why_wrong')}")
            print(f"Learning Points: {result.get('learning_points')}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None


def get_aptitude_question(user_id="test_user", difficulty="easy", topic=None, job_id=None):
    """Fetch an aptitude question from database"""
    print("\n=== Fetching Aptitude Question ===")
    
    payload = {
        "mode": "apti",
        "user_id": user_id,
        "difficulty": difficulty
    }
    
    if topic:
        payload["topic"] = topic
    
    if job_id:
        payload["job_id"] = job_id
        print(f"Filtering by job ID: {job_id}")
    
    response = requests.post(f"{BASE_URL}/aptitude/get-question", json=payload)
    
    if response.status_code == 200:
        question = response.json()
        print(f"\nQuestion ID: {question['question_id']}")
        print(f"Difficulty: {question['difficulty']}")
        print(f"Topic: {question['topic']}")
        print(f"\nQuestion: {question['question_text']}")
        print(f"\nOptions:")
        for i, option in enumerate(question['options'], 1):
            print(f"  {i}. {option}")
        
        return question['question_id']
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None


def submit_aptitude_answer(question_id, answer, user_id="test_user"):
    """Submit aptitude answer"""
    print("\n=== Submitting Aptitude Answer ===")
    
    payload = {
        "user_id": user_id,
        "question_id": question_id,
        "user_answer": answer
    }
    
    response = requests.post(f"{BASE_URL}/aptitude/submit-answer", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nSubmission ID: {result['submission_id']}")
        print(f"Correct: {result['is_correct']}")
        print(f"Score: {result['score']}")
        print(f"Feedback: {result['feedback']}")
        
        if not result['is_correct']:
            print(f"\nCorrect Answer: {result.get('correct_answer')}")
            print(f"Why Wrong: {result.get('why_wrong')}")
            print(f"Learning Points: {result.get('learning_points')}")
        
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        return None


def main():
    """Run example workflow"""
    print("=" * 50)
    print("Code-Sandbox API Example")
    print("=" * 50)
    
    # Step 1: Check available questions
    if not check_question_stats():
        print("\n⚠️ No questions available!")
        print("Please run qa_gen_spice to generate questions first:")
        print("  cd qa_gen_spice")
        print("  python question_generator.py --count 50 --type code")
        print("  python question_generator.py --count 30 --type apti")
        return
    
    # Step 1b: Get available job IDs
    job_ids = get_available_job_ids()
    
    # Select first job ID if available
    selected_job_id = None
    if job_ids:
        selected_job_id = job_ids[0]['job_id']
        print(f"\n✓ Using job ID: {selected_job_id}")
        check_question_stats(job_id=selected_job_id)
    
    # Step 2: Try code question workflow
    print("\n" + "=" * 50)
    print("CODE QUESTION WORKFLOW")
    print("=" * 50)
    
    question_id = get_code_question(difficulty="easy", job_id=selected_job_id)
    
    if question_id:
        # Example solution (likely wrong for demonstration)
        example_code = """
def solution(nums, target):
    # Simple solution
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
        submit_code(question_id, example_code)
    
    # Step 3: Try aptitude question workflow
    print("\n" + "=" * 50)
    print("APTITUDE QUESTION WORKFLOW")
    print("=" * 50)
    
    question_id = get_aptitude_question(difficulty="easy", job_id=selected_job_id)
    
    if question_id:
        # Example: Submit first option (might be wrong)
        submit_aptitude_answer(question_id, "A")
    
    print("\n" + "=" * 50)
    print("Example completed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API")
        print("Make sure the code-sandbox server is running:")
        print("  cd code-sandbox")
        print("  python main.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
