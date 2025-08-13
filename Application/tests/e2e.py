import unittest
import json
import os
import sys
import uuid
import logging
import time
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app import app
from models import db, User, Quiz, Question, Answer
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token


def wait_for_app_health(max_retries=30, delay=2):
    """
    Wait for the application to be healthy before starting E2E tests
    Similar to: wget -q --spider http://127.0.0.1:5000/health
    """
    print("🏥 Performing health check before starting E2E tests...")
    
    # Try different possible URLs for the health endpoint
    health_urls = [
        "http://127.0.0.1:5000/health",
        "http://localhost:5000/health", 
        "http://app:5000/health"  # Docker service name
    ]
    
    for attempt in range(max_retries):
        for url in health_urls:
            try:
                request = urllib.request.Request(url)
                with urllib.request.urlopen(request, timeout=5) as response:
                    if response.getcode() == 200:
                        print(f"✅ Application is healthy at {url}")
                        return True
            except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                pass  # Try next URL
        
        if attempt < max_retries - 1:
            print(f"⏳ Health check attempt {attempt + 1}/{max_retries} failed, retrying in {delay}s...")
            time.sleep(delay)
    
    print(f"❌ Health check failed after {max_retries} attempts")
    print("⚠️  Continuing with tests anyway...")
    return False


class E2ETestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = defaultdict(list)
        self.current_section = "Unknown"
        self.start_time = None
        
    def startTest(self, test):
        super().startTest(test)
        self.start_time = datetime.now()
        test_name = test._testMethodName
        
        # Add separator between individual tests
        if hasattr(self, 'test_count'):
            print(f"\n{'='*80}")
        else:
            self.test_count = 0
        self.test_count += 1
            
        print(f"   Running: {test_name}")
        print("-" * 80)
        
    def addSuccess(self, test):
        super().addSuccess(test)
        test_name = test._testMethodName
        duration = (datetime.now() - self.start_time).total_seconds()
        self.test_results[self.current_section].append((test_name, 'PASS', duration))
        print(f"✅ PASSED: {test_name} ({duration:.2f}s)")
        
    def addError(self, test, err):
        super().addError(test, err)
        test_name = test._testMethodName
        duration = (datetime.now() - self.start_time).total_seconds()
        self.test_results[self.current_section].append((test_name, 'ERROR', duration))
        print(f"❌ ERROR: {test_name} ({duration:.2f}s)")
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_name = test._testMethodName
        duration = (datetime.now() - self.start_time).total_seconds()
        self.test_results[self.current_section].append((test_name, 'FAIL', duration))
        print(f"❌ FAILED: {test_name} ({duration:.2f}s)")


class E2ETestRunner(unittest.TextTestRunner):
    def __init__(self, **kwargs):
        kwargs['resultclass'] = E2ETestResult
        super().__init__(**kwargs)
        
    def run(self, test):
        result = super().run(test)
        self.print_final_summary(result)
        return result
        
    def print_final_summary(self, result):
        print(f"\n{'='*80}")
        print(f"🎯 END-TO-END TEST RESULTS SUMMARY")
        print(f"{'='*80}")
        
        # Calculate totals across all tests
        total_tests = result.testsRun
        total_failed = len(result.failures)
        total_errors = len(result.errors)
        total_passed = total_tests - total_failed - total_errors
        
        # Calculate total time from our test results
        total_time = 0
        for section, tests in result.test_results.items():
            total_time += sum([t[2] for t in tests])
        
        overall_icon = "✅" if (total_failed + total_errors) == 0 else "❌"
        print(f"{overall_icon} OVERALL E2E RESULTS: {total_passed}/{total_tests} workflows completed")
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")
        
        if total_failed > 0 or total_errors > 0:
            print(f"\n   Issues found:")
            for test, error in result.failures:
                print(f"     ❌ {test._testMethodName} (FAILED)")
            for test, error in result.errors:
                print(f"     ❌ {test._testMethodName} (ERROR)")
        
        if (total_failed + total_errors) == 0:
            print(f"\n🎉 ALL E2E WORKFLOWS PASSED! Your application is ready for production!")
        else:
            print(f"\n🔧 Please review and fix the failing workflows.")
            
        print(f"{'='*80}")
        print("")


class QuizAppE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database configuration"""
        # Disable Flask app logging during tests to reduce noise
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        app.logger.setLevel(logging.WARNING)
        
        # Get DATABASE_URL once and store it for reuse
        cls.database_url = os.getenv('DATABASE_URL')
        if not cls.database_url:
            raise ValueError("DATABASE_URL environment variable is required for E2E tests")
            
        cls.test_db_name = f"quiz_db_e2e_test_{uuid.uuid4().hex[:8]}"
        
        # Parse original URI and replace database name
        if 'postgresql://' in cls.database_url:
            base_uri = cls.database_url.rsplit('/', 1)[0]
            cls.test_db_uri = f"{base_uri}/{cls.test_db_name}"
            cls.admin_db_uri = cls.database_url.replace('/quiz_db', '/postgres')
        else:
            cls.test_db_uri = cls.database_url
            cls.admin_db_uri = cls.database_url
            
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = cls.test_db_uri
        app.config['JWT_SECRET_KEY'] = 'e2e-test-secret-key'
        
        # Suppress app's logging and debug output during tests 
        import utils as utils_module
        cls.original_log_request = utils_module.log_request
        cls.original_logger_info = utils_module.logger.info
        cls.original_logger_error = utils_module.logger.error
        
        # Store original print function to suppress DEBUG prints
        import builtins
        cls.original_print = builtins.print
        
        # Replace logging functions with no-op functions during tests
        utils_module.log_request = lambda *_, **__: None
        utils_module.logger.info = lambda *_, **__: None  
        utils_module.logger.error = lambda *_, **__: None
        
        # Override print to filter out DEBUG messages
        def filtered_print(*args, **kwargs):
            if args and isinstance(args[0], str) and args[0].startswith('DEBUG'):
                return  # Skip DEBUG messages
            cls.original_print(*args, **kwargs)
        
        builtins.print = filtered_print
        
        # Create test database
        cls._create_test_database()
        
        print(f"🗄️  Created E2E test database: {cls.test_db_name}")

    @classmethod 
    def tearDownClass(cls):
        """Clean up test database"""
        # Restore original logging functions and print
        import utils as utils_module
        import builtins
        utils_module.log_request = cls.original_log_request
        utils_module.logger.info = cls.original_logger_info
        utils_module.logger.error = cls.original_logger_error
        builtins.print = cls.original_print
        
        cls._drop_test_database()
        print(f"🗑️  Dropped E2E test database: {cls.test_db_name}")

    @classmethod
    def _create_test_database(cls):
        """Create a dedicated test database"""
        try:
            from sqlalchemy import create_engine
            
            # Use the admin database URI we already prepared
            admin_engine = create_engine(cls.admin_db_uri, isolation_level='AUTOCOMMIT')
            
            with admin_engine.connect() as conn:
                # Drop if exists and create new test database
                conn.execute(text(f"DROP DATABASE IF EXISTS {cls.test_db_name}"))
                conn.execute(text(f"CREATE DATABASE {cls.test_db_name}"))
            
            admin_engine.dispose()
            
        except Exception as e:
            print(f"⚠️  Could not create test database: {e}")
            print("   Using configured database URI as-is")

    @classmethod  
    def _drop_test_database(cls):
        """Drop the test database"""
        try:
            from sqlalchemy import create_engine
            
            # Use the admin database URI we already prepared
            admin_engine = create_engine(cls.admin_db_uri, isolation_level='AUTOCOMMIT')
            
            with admin_engine.connect() as conn:
                # Terminate connections and drop database
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = '{cls.test_db_name}' AND pid <> pg_backend_pid()
                """))
                conn.execute(text(f"DROP DATABASE IF EXISTS {cls.test_db_name}"))
            
            admin_engine.dispose()
            
        except Exception as e:
            print(f"⚠️  Could not drop test database: {e}")

    def setUp(self):
        """Set up each test with clean database state"""
        self.client = app.test_client()
        
        with app.app_context():
            # Create all tables for each test
            db.create_all()
            
        # Track created data for cleanup
        self.created_user_ids = []
        self.created_quiz_ids = []
        self.created_question_ids = []
        self.created_answer_ids = []
        
        # Test data storage
        self.test_users = {}
        self.test_quizzes = {}
        self.test_questions = {}

    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            try:
                # Simple approach: delete all data using CASCADE
                # This is more reliable for test cleanup
                if self.created_user_ids or self.created_quiz_ids:
                    db.session.execute(text('TRUNCATE TABLE answer, question, quiz, "user" RESTART IDENTITY CASCADE'))
                    db.session.commit()
                    
            except Exception as e:
                print(f"⚠️  Cleanup error: {e}")
                db.session.rollback()
            finally:
                db.session.remove()

    def register_user(self, first_name, last_name, email, password):
        """Helper to register a user and return token"""
        response = self.client.post('/register', json={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password
        })
        self.assertEqual(response.status_code, 201)
        user_data = response.get_json()
        
        # Track user for cleanup
        self.created_user_ids.append(user_data['user_id'])
        
        # Login to get token
        login_response = self.client.post('/login', json={
            'email': email,
            'password': password
        })
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.get_json()
        
        return {
            'user_id': user_data['user_id'],
            'token': login_data['token'],
            'user_info': login_data,
            'auth_header': {'Authorization': f'Bearer {login_data["token"]}'}
        }

    def create_quiz(self, auth_header, title, description="", topic="General"):
        """Helper to create a quiz"""
        response = self.client.post('/quiz', json={
            'title': title,
            'description': description,
            'topic': topic
        }, headers=auth_header)
        self.assertEqual(response.status_code, 201)
        quiz_data = response.get_json()
        
        # Track quiz for cleanup
        self.created_quiz_ids.append(quiz_data['id'])
        
        return quiz_data

    def add_question(self, auth_header, quiz_id, text, options, correct_option):
        """Helper to add a question to a quiz"""
        response = self.client.post(f'/quiz/{quiz_id}/question', json={
            'text': text,
            'option_a': options[0],
            'option_b': options[1], 
            'option_c': options[2],
            'option_d': options[3],
            'correct_option': correct_option
        }, headers=auth_header)
        self.assertEqual(response.status_code, 201)
        question_data = response.get_json()
        
        # Track question for cleanup
        self.created_question_ids.append(question_data['id'])
        
        return question_data

    def submit_answer(self, auth_header, quiz_id, question_id, selected_option):
        """Helper to submit an answer"""
        response = self.client.post(f'/quiz/{quiz_id}/question/{question_id}/answer', json={
            'selected_option': selected_option
        }, headers=auth_header)
        self.assertEqual(response.status_code, 200)
        
        # Note: We don't track individual answer IDs since they're handled by cascading deletes
        # when we delete users, but we could track them if needed for more granular cleanup
        
        return response.get_json()

    # ============================================================================
    # 🚀 CRITICAL USER JOURNEY TESTS
    # ============================================================================
    def test_complete_quiz_creation_and_taking_workflow(self):
        """
        Main E2E test: Complete workflow from user registration to quiz completion
        """
        print("   Step 1: Register quiz creator and create quiz")
        creator = self.register_user("John", "Creator", "creator@example.com", "password123")
        quiz = self.create_quiz(creator['auth_header'], "Programming Quiz", "Test your knowledge")
        
        print("   Step 2: Add questions to quiz")
        q1 = self.add_question(creator['auth_header'], quiz['id'],
                              "What is the output of print(type([]))?",
                              ["<class 'list'>", "<class 'array'>", "<class 'dict'>", "<class 'tuple'>"],
                              "A")
        
        q2 = self.add_question(creator['auth_header'], quiz['id'],
                              "Which keyword defines a function in Python?",
                              ["function", "def", "define", "func"],
                              "B")
        
        print("   Step 3: Update quiz details (PUT)")
        update_response = self.client.put(f'/quiz/{quiz["id"]}', json={
            'title': 'Updated Programming Quiz',
            'description': 'Updated description',
            'topic': 'Computer Science'
        }, headers=creator['auth_header'])
        self.assertEqual(update_response.status_code, 200)
        
        print("   Step 4: Update question (PUT)")
        question_update = self.client.put(f'/question/{q1["id"]}', json={
            'text': 'Updated: What is the output of print(type([]))?',
            'option_a': 'Updated <class \'list\'>',
            'correct_option': 'A'
        }, headers=creator['auth_header'])
        self.assertEqual(question_update.status_code, 200)
        
        print("   Step 5: Delete one question (DELETE)")
        delete_question = self.client.delete(f'/question/{q2["id"]}', headers=creator['auth_header'])
        self.assertEqual(delete_question.status_code, 200)
        
        print("   Step 6: Register quiz taker and take quiz")
        taker = self.register_user("Jane", "Taker", "taker@example.com", "password456")
        
        # Take quiz with remaining question
        answer1 = self.submit_answer(taker['auth_header'], quiz['id'], q1['id'], 'A')  # Correct
        self.assertTrue(answer1['correct'])
        
        print("   Step 7: Verify final results")
        score_response = self.client.get(f'/quiz/{quiz["id"]}/score', headers=taker['auth_header'])
        score_data = score_response.get_json()
        self.assertEqual(score_data['score'], 1)
        self.assertEqual(score_data['total'], 1)  # Only one question left after deletion
        self.assertEqual(score_data['percentage'], 100.0)

    def test_multi_user_quiz_scenario(self):
        """
        E2E test: Multiple users taking the same quiz
        """
        print("   Step 1: Create quiz")
        creator = self.register_user("Teacher", "Smith", "teacher@school.edu", "teacher123")
        quiz = self.create_quiz(creator['auth_header'], "Math Quiz", "Basic mathematics")
        
        question = self.add_question(creator['auth_header'], quiz['id'],
                                   "What is 5 + 3?",
                                   ["7", "8", "9", "10"],
                                   "B")
        
        print("   Step 2: Multiple students take quiz")
        student1 = self.register_user("Alice", "Student", "alice@school.edu", "student123")
        student2 = self.register_user("Bob", "Student", "bob@school.edu", "student456")
        
        # Student 1 gets it right
        answer1 = self.submit_answer(student1['auth_header'], quiz['id'], question['id'], 'B')
        self.assertTrue(answer1['correct'])
        
        # Student 2 gets it wrong
        answer2 = self.submit_answer(student2['auth_header'], quiz['id'], question['id'], 'A')
        self.assertFalse(answer2['correct'])
        
        print("   Step 3: Verify individual scores")
        score1 = self.client.get(f'/quiz/{quiz["id"]}/score', headers=student1['auth_header'])
        self.assertEqual(score1.get_json()['percentage'], 100.0)
        
        score2 = self.client.get(f'/quiz/{quiz["id"]}/score', headers=student2['auth_header'])
        self.assertEqual(score2.get_json()['percentage'], 0.0)


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Starting Quiz Application End-to-End Test Suite...")
    print("🎯 Testing complete user workflows and real-world scenarios...")
    print("=" * 80)
    
    # Wait for application to be healthy before starting tests
    wait_for_app_health()
    print("=" * 80)
    
    # Create custom test runner with no default output
    runner = E2ETestRunner(verbosity=0)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(QuizAppE2ETest)
    
    runner.run(suite)