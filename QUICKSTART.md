# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure API Key

```powershell
# Copy environment file
Copy-Item .env.example .env

# Open and edit .env file
notepad .env
```

Add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_actual_api_key_here
```

Get an API key from: https://openrouter.ai/

### Step 3: Start Docker Desktop

Make sure Docker Desktop is running before starting the application.

### Step 4: Run the Application

```powershell
python main.py
```

Visit: http://localhost:8000/docs

## 📝 Example Usage

### Testing Aptitude Mode

1. **Generate a Question**
   - Go to http://localhost:8000/docs
   - Find `POST /api/v1/aptitude/generate-question`
   - Click "Try it out"
   - Use this JSON:
   ```json
   {
     "mode": "apti",
     "difficulty": "medium",
     "topic": "logical reasoning",
     "user_id": "test_user_123"
   }
   ```
   - Copy the `question_id` from the response

2. **Submit an Answer**
   - Find `POST /api/v1/aptitude/submit-answer`
   - Use the `question_id` you just got:
   ```json
   {
     "user_id": "test_user_123",
     "question_id": "paste_question_id_here",
     "user_answer": "A"
   }
   ```

3. **View Your Mistakes**
   - Find `GET /api/v1/aptitude/user-summary/{user_id}`
   - Enter: `test_user_123`
   - See all wrong answers with explanations

### Testing Code Mode

1. **Generate a Coding Challenge**
   - Find `POST /api/v1/code/generate-question`
   - Use:
   ```json
   {
     "mode": "code",
     "difficulty": "easy",
     "topic": "arrays",
     "user_id": "test_user_123"
   }
   ```

2. **Submit Code**
   - Find `POST /api/v1/code/submit-code`
   - Use:
   ```json
   {
     "user_id": "test_user_123",
     "question_id": "paste_question_id_here",
     "code": "def solution(arr):\n    return sorted(arr)",
     "language": "python"
   }
   ```

3. **Quick Code Test**
   - Find `POST /api/v1/code/run-code`
   - Test any code without a question:
   ```json
   {
     "user_id": "test_user_123",
     "question_id": "test",
     "code": "print('Hello from Docker!')\nprint(2 + 2)",
     "language": "python"
   }
   ```

## 🔧 Using with Python Requests

Save this as `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "test_user_123"

# Test Aptitude Mode
print("=== Testing Aptitude Mode ===")

# Generate question
response = requests.post(f"{BASE_URL}/aptitude/generate-question", json={
    "mode": "apti",
    "difficulty": "medium",
    "user_id": USER_ID
})
question = response.json()
print(f"Question: {question['question_text']}")
print(f"Options: {question['options']}")
question_id = question['question_id']

# Submit answer
response = requests.post(f"{BASE_URL}/aptitude/submit-answer", json={
    "user_id": USER_ID,
    "question_id": question_id,
    "user_answer": "A"
})
result = response.json()
print(f"Correct: {result['is_correct']}")
print(f"Feedback: {result['feedback']}")

# Test Code Mode
print("\n=== Testing Code Mode ===")

# Generate coding question
response = requests.post(f"{BASE_URL}/code/generate-question", json={
    "mode": "code",
    "difficulty": "easy",
    "user_id": USER_ID
})
challenge = response.json()
print(f"Challenge: {challenge['title']}")
question_id = challenge['question_id']

# Submit code
code = """
def solution(arr):
    return sorted(arr)
"""

response = requests.post(f"{BASE_URL}/code/submit-code", json={
    "user_id": USER_ID,
    "question_id": question_id,
    "code": code,
    "language": "python"
})
result = response.json()
print(f"Tests Passed: {result['execution_result']['passed_tests']}/{result['execution_result']['total_tests']}")
print(f"Feedback: {result['feedback']}")
```

Run it:
```powershell
python test_api.py
```

## 🐳 Using Docker Compose

For a complete production setup:

```powershell
# Build and start
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop everything
docker-compose down
```

## 🎯 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Check Health**: Visit http://localhost:8000/health
3. **View MongoDB**: Use MongoDB Compass or VS Code extension
4. **Customize**: Edit `config.py` to change settings
5. **Add Features**: Extend the routes and services

## 🆘 Common Issues

### "Docker not found"
→ Install Docker Desktop and make sure it's running

### "OpenRouter API key not set"
→ Check your `.env` file has `OPENROUTER_API_KEY=your_key`

### "MongoDB connection failed"
→ Check your internet connection and MongoDB URL

### "Port 8000 already in use"
→ Change port in `main.py` or stop other services using port 8000

## 📚 Learn More

- FastAPI docs: https://fastapi.tiangolo.com/
- OpenRouter docs: https://openrouter.ai/docs
- Docker docs: https://docs.docker.com/
- MongoDB docs: https://docs.mongodb.com/
