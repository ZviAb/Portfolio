# Interactive Quiz System

An advanced quiz management system built with Flask and PostgreSQL, fully containerized with Docker for easy deployment and scalability. The application enables interactive creation, management, and solving of quizzes.

## Table of Contents

- [Key Features](#key-features)
- [Technologies](#technologies)
- [System Requirements](#system-requirements)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [API Documentation](#api-documentation)
- [Advanced Features](#advanced-features)
- [Testing](#testing)
- [Author](#author)

## Key Features

- **User Management**: Registration, authentication, and JWT-based authorization
- **Quiz Creation**: Create and manage quizzes with multiple-choice questions
- **Quiz Taking**: Intuitive interface for taking quizzes and receiving scores
- **Statistics**: Performance tracking and statistical data
- **Advanced UI**: Responsive design with HTML/CSS/JavaScript
- **Complete API**: Comprehensive REST API for all functionality

### Application Interface

![Main Page](../Pics/main_page_1.png)

![Application Dashboard](../Pics/app_dash.png)

![Quiz Interface](../Pics/quiz_ans.png)

![Quiz Results](../Pics/quiz_ans2.png)

## Technologies

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens)
- **Frontend**: HTML5, CSS3, JavaScript
- **Containerization**: Docker & Docker Compose
- **CI/CD**: Jenkins Pipeline
- **Web Server**: Nginx

## System Requirements

### For Docker Deployment (Recommended)

- Docker 20.10+
- Docker Compose 2.0+

### For Local Development

- Python 3.8+
- PostgreSQL 12+

## Project Structure

```
portfolio-application/
├── app.py                 # Main Flask application with all routes and models
├── requirements.txt       # Python package dependencies (Flask, SQLAlchemy, JWT, etc.)
├── docker-compose.yml     # Multi-container orchestration (app, db, nginx)
├── Dockerfile            # Container image for Flask application
├── Dockerfile.nginx      # Container image for Nginx reverse proxy
├── Dockerfile.test       # Container image for running tests
├── Jenkinsfile          # CI/CD pipeline configuration for automated deployment
├── .env                 # Environment variables (DATABASE_URL, JWT_SECRET_KEY)
├── .gitignore           # Git ignore patterns
├── templates/           # Jinja2 HTML templates
│   ├── home.html        # Landing page
│   ├── login.html       # User authentication
│   ├── register.html    # User registration
│   ├── dashboard.html   # User dashboard
│   ├── create_quiz.html # Quiz creation interface
│   ├── manage_quiz.html # Quiz management
│   ├── take_quiz.html   # Quiz taking interface
│   ├── browse_quizzes.html # Browse available quizzes
│   └── profile.html     # User profile management
├── static/              # Frontend assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   └── images/         # Static images and icons
├── nginx/              # Nginx configuration files
│   └── nginx.conf      # Reverse proxy and load balancing config
└── tests/              # Automated test suite
    ├── unit_test.py    # Unit tests for core functionality
    └── e2e.py          # End-to-end integration tests
```

### Key Files Description

**Core Application:**

- `app.py` - Contains the entire Flask application including database models (User, Quiz, Question, Answer), all API routes, authentication logic, and application configuration

**Docker Configuration:**

- `docker-compose.yml` - Orchestrates three services: Flask app, PostgreSQL database, and Nginx proxy
- `Dockerfile` - Multi-stage build for the Flask application with Python dependencies
- `Dockerfile.nginx` - Lightweight Nginx container for reverse proxy and static file serving

**Frontend:**

- `templates/` - Server-side rendered HTML templates using Jinja2 templating engine
- `static/` - Client-side assets including responsive CSS, interactive JavaScript, and UI images

**DevOps:**

- `Jenkinsfile` - Automated CI/CD pipeline with build, test, and deployment stages
- `requirements.txt` - Pinned Python dependencies for reproducible builds

## Installation and Setup

### Local Installation

1. **Create virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Set environment variables**:
   Create a `.env` file in the project directory:

```env
DB_NAME=quiz_db
DB_USER=quiz_user
DB_PASSWORD=quiz_password
DATABASE_URL=postgresql://quiz_user:quiz_password@localhost:5432/quiz_db
JWT_SECRET_KEY=your-secret-key-change-in-production
```

**Note:** For Docker deployment, change `localhost` to `postgres` in the DATABASE_URL.

4. **Run the application**:

```bash
python app.py
```

The application will automatically create the database tables on first run and be available at: `http://localhost:5000`

### Docker Setup (Recommended)

The application is fully containerized and can be deployed using Docker Compose, which includes:

- Flask application container
- PostgreSQL database container
- Nginx reverse proxy container

1. **Run with Docker Compose**:

```bash
docker-compose up -d
```

2. **View running containers**:

```bash
docker-compose ps
```

3. **View logs**:

```bash
docker-compose logs -f
```

4. **Stop services**:

```bash
docker-compose down
```

The application will be available at: `http://localhost` (port 80)

## API Documentation

### Authentication

- `POST /register` - Register new user
- `POST /login` - User login

### Quiz Management

- `GET /quiz` - Get list of all quizzes
- `POST /quiz` - Create new quiz
- `GET /quiz/{id}` - Get quiz details
- `PUT /quiz/{id}` - Update quiz
- `DELETE /quiz/{id}` - Delete quiz

### Questions

- `POST /quiz/{quiz_id}/question` - Add question to quiz
- `PUT /question/{id}` - Update question
- `DELETE /question/{id}` - Delete question

### Quiz Taking

- `POST /quiz/{quiz_id}/question/{question_id}/answer` - Submit answer
- `GET /quiz/{quiz_id}/score` - Get quiz score

### User Stats

- `GET /user/stats` - User statistics
- `GET /metrics` - System-wide metrics

## Advanced Features

### Security

- Password encryption with Werkzeug
- JWT authentication for all sensitive operations
- CORS attack protection
- Comprehensive logging of all operations

### Performance

- Database connection pooling
- Result caching
- SQL query optimization

### Containerization

- Multi-container Docker architecture
- Nginx reverse proxy for load balancing
- Isolated database container
- Easy horizontal scaling with Docker Swarm

### Monitoring and Logging

- Built-in JSON logging
- User activity tracking
- Performance metrics

## Testing

The application includes a comprehensive test suite to ensure reliability and functionality across all components.

### Test Structure

The test suite is organized into two main categories:

- **Unit Tests** (`unit_test.py`) - Individual component testing, function validation, isolated testing
- **End-to-End Tests** (`e2e.py`) - Full workflow testing, integration testing, user journey validation

### Running Tests

**Local Testing:**

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
python -m pytest tests/

# Run tests with coverage report
python -m pytest tests/ --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/unit_test.py -v
python -m pytest tests/e2e.py -v
```

**Docker Testing (As used in CI/CD Pipeline):**

```bash
# Build unit test container
docker compose --profile unit-test build unit-test

# Run unit tests
docker compose --profile unit-test run --rm unit-test

# Build application containers
docker compose --profile app build

# Run E2E tests with full application stack
docker compose --profile app up -d
docker compose --profile e2e run --rm e2e
docker compose --profile app down
```

### Test Coverage

The test suite covers:

- **User Authentication**: Registration, login, password validation, JWT token management
- **Quiz Management**: CRUD operations, authorization checks, data validation
- **Question Handling**: Adding, updating, deleting questions with proper validation
- **Answer Submission**: Score calculation, answer validation, user progress tracking
- **API Security**: Authentication requirements, input sanitization, error responses
- **Database Operations**: Model relationships, data integrity, transaction handling

### Continuous Integration

Tests are automatically executed in the Jenkins CI/CD pipeline with the following stages:

1. **Build Image for tests** - Creates containerized test environment
2. **Unit Test** - Runs isolated unit tests using Docker Compose profiles
3. **Package** - Builds application containers for integration testing
4. **E2E Tests** - Executes end-to-end tests with full application stack (only on feature branches and main)

![Pipeline Success](../Pics/Pipeline_Completed_Successfully.png)

**Pipeline Test Flow:**

- Unit tests run on every commit to any branch
- E2E tests run only on `feature/*` branches and `main` branch
- Tests use Docker Compose profiles for isolated environments
- Automatic cleanup of containers and images after pipeline completion

## Author

Created by **Zvi Abramovich** - DevOps Engineer

- Email: zviabramovich22@gmail.com
- Domain: zvidevops.cloud

Feel free to reach out if you have questions or suggestions!
