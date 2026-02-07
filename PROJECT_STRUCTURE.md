# Project Structure

```
code-sandbox/
│
├── main.py                           # FastAPI application entry point
├── config.py                         # Configuration and settings
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Docker container definition
├── docker-compose.yml                # Docker orchestration
│
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
├── README.md                         # Project documentation
├── QUICKSTART.md                     # Quick start guide
├── PROJECT_STRUCTURE.md              # This file
│
├── setup.ps1                         # Windows setup script
├── start.ps1                         # Quick start script
├── test_api.py                       # API testing script
├── examples.py                       # Usage examples
│
├── models/                           # Data models and database
│   ├── __init__.py
│   ├── database.py                   # MongoDB connection setup
│   └── schemas.py                    # Pydantic models for API
│
├── services/                         # Business logic services
│   ├── __init__.py
│   ├── openrouter_service.py        # LLM integration (OpenRouter)
│   └── docker_sandbox.py            # Docker container management
│
├── routes/                           # API route handlers
│   ├── __init__.py
│   ├── aptitude.py                   # Aptitude mode endpoints
│   └── code.py                       # Code mode endpoints
│
└── .vscode/                          # VS Code configuration
    ├── settings.json                 # Editor settings
    └── extensions.json               # Recommended extensions
```

## File Descriptions

### Core Files

- **main.py**: FastAPI application with lifespan management, CORS, exception handling, and route registration

- **config.py**: Centralized configuration using Pydantic Settings, loads from environment variables

### Data Layer

- **models/database.py**: 
  - MongoDB connection management
  - Database initialization and cleanup
  - Connection pooling

- **models/schemas.py**:
  - Pydantic models for request/response validation
  - Enums for mode types and difficulty levels
  - Data structures for questions, submissions, and evaluations

### Service Layer

- **services/openrouter_service.py**:
  - OpenRouter API integration
  - Question generation (aptitude and code)
  - Answer evaluation using LLM
  - JSON parsing and error handling

- **services/docker_sandbox.py**:
  - Docker container lifecycle management
  - Code execution in isolated environments
  - TTL-based container cleanup
  - Test case execution and validation

### API Routes

- **routes/aptitude.py**:
  - POST /aptitude/generate-question - Generate aptitude questions
  - POST /aptitude/submit-answer - Submit and evaluate answers
  - GET /aptitude/user-summary/{user_id} - Get user's mistake summary

- **routes/code.py**:
  - POST /code/generate-question - Generate coding challenges
  - POST /code/submit-code - Submit and evaluate code
  - POST /code/run-code - Quick code testing
  - GET /code/user-summary/{user_id} - Get user's coding mistakes

### Database Collections

The application creates the following MongoDB collections:

1. **aptitude_questions**
   - Stores generated aptitude questions
   - Fields: question_id, question_text, options, correct_answer, explanation, difficulty, topic, user_id, generated_at

2. **code_questions**
   - Stores generated coding challenges
   - Fields: question_id, title, description, difficulty, topic, test_cases, starter_code, solution_explanation, user_id, generated_at

3. **aptitude_submissions**
   - Stores user submissions for aptitude questions
   - Fields: submission_id, user_id, question_id, user_answer, is_correct, score, feedback, submitted_at

4. **code_submissions**
   - Stores user code submissions
   - Fields: submission_id, user_id, question_id, code, language, execution_result, is_correct, score, feedback, submitted_at

5. **user_attempt_summaries**
   - Stores summaries of incorrect attempts with learning points
   - Fields: user_id, mode, question_id, question_text, user_answer, correct_answer, is_correct, why_wrong, learning_points, attempted_at

### Configuration Files

- **.env.example**: Template for environment variables
- **docker-compose.yml**: Production deployment configuration
- **Dockerfile**: Container build instructions
- **.gitignore**: Files to ignore in version control
- **.vscode/**: VS Code workspace settings

### Documentation

- **README.md**: Complete project documentation
- **QUICKSTART.md**: Step-by-step getting started guide
- **PROJECT_STRUCTURE.md**: This file

### Scripts

- **setup.ps1**: Complete Windows setup automation
- **start.ps1**: Quick start after initial setup
- **test_api.py**: Synchronous API testing
- **examples.py**: Async usage examples

## Dependencies

### Core
- fastapi: Web framework
- uvicorn: ASGI server
- pydantic: Data validation
- pydantic-settings: Settings management

### Database
- motor: Async MongoDB driver
- pymongo: MongoDB driver

### External Services
- httpx: Async HTTP client for OpenRouter
- docker: Docker SDK for Python

### Utilities
- python-dotenv: Environment variable management

## Architecture Flow

```
Client Request
    ↓
FastAPI (main.py)
    ↓
Route Handler (routes/)
    ↓
Service Layer (services/)
    ├→ OpenRouter Service (LLM)
    └→ Docker Sandbox (Code Execution)
    ↓
Database (MongoDB via motor)
    ↓
Response to Client
```

## Data Flow

### Aptitude Mode
1. User requests question → OpenRouter generates → Store in DB
2. Return question to user (without answer)
3. User submits answer → Evaluate with OpenRouter
4. Store submission and summary → Return feedback

### Code Mode
1. User requests challenge → OpenRouter generates → Store in DB
2. Return challenge with test cases
3. User submits code → Execute in Docker
4. Evaluate results with OpenRouter
5. Store submission and summary → Return feedback

## Security Considerations

- Docker containers run in isolated environments
- No network access for code execution
- Resource limits prevent DoS
- TTL cleanup prevents container accumulation
- Environment variables for sensitive data
- MongoDB connection string not hardcoded

## Extension Points

- Add more programming languages (services/docker_sandbox.py)
- Custom difficulty adjustment algorithms
- Additional question types
- User authentication (main.py middleware)
- Rate limiting per user
- WebSocket support for live execution
- Question caching
- Analytics dashboard
