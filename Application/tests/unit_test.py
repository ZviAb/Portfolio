import unittest
import json
import os
import sys
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

# Set up environment before importing app
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key')
os.environ.setdefault('FLASK_ENV', 'testing')

from app import app
from models import db, User, Quiz, Question, Answer
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token



class FullAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test configuration and suppress app logging"""
        # Suppress app's logging and debug output during tests 
        import utils as utils_module
        import builtins
        
        cls.original_log_request = utils_module.log_request
        cls.original_logger_info = utils_module.logger.info
        cls.original_logger_error = utils_module.logger.error
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
    
    @classmethod
    def tearDownClass(cls):
        """Restore original logging and print functions"""
        import utils as utils_module
        import builtins
        
        utils_module.log_request = cls.original_log_request
        utils_module.logger.info = cls.original_logger_info
        utils_module.logger.error = cls.original_logger_error
        builtins.print = cls.original_print
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

            user = User(
                first_name='Test',
                last_name='User',
                email='test@example.com',
                password_hash=generate_password_hash('123456')
            )
            db.session.add(user)
            db.session.commit()

            self.user_id = user.id
            self.token = create_access_token(identity=str(user.id))
            self.auth_header = {'Authorization': f'Bearer {self.token}'}

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # ============================================================================
    # 🔐 AUTHENTICATION & AUTHORIZATION TESTS
    # ============================================================================
    def test_register(self):
        res = self.client.post('/register', json={
            'first_name': 'Alice',
            'last_name': 'Tester',
            'email': 'alice@example.com',
            'password': 'secret123'
        })
        self.assertEqual(res.status_code, 201)
        self.assertIn('user_id', res.get_json())

    def test_login(self):
        res = self.client.post('/login', json={
            'email': 'test@example.com',
            'password': '123456'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('token', res.get_json())

    # ============================================================================
    # 📝 QUIZ MANAGEMENT TESTS
    # ============================================================================
    def test_create_quiz(self):
        res = self.client.post('/quiz', json={
            'title': 'Math Quiz',
            'description': 'A simple quiz',
            'topic': 'Math'
        }, headers=self.auth_header)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data['title'], 'Math Quiz')

    def test_get_quizzes(self):
        # יצירת חידון ישירות בבסיס הנתונים
        with app.app_context():
            quiz = Quiz(title='Test Quiz', description='...', topic='General', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()

        res = self.client.get('/quiz')
        self.assertEqual(res.status_code, 200)
        self.assertGreaterEqual(len(res.get_json()), 1)

    # --- Questions ---
    def test_add_question(self):
        with app.app_context():
            quiz = Quiz(title='Quiz with question', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

        res = self.client.post(f'/quiz/{quiz_id}/question', json={
            'text': 'What is 2 + 2?',
            'option_a': '3',
            'option_b': '4',
            'option_c': '5',
            'option_d': '6',
            'correct_option': 'B'
        }, headers=self.auth_header)

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()['correct_option'], 'B')

    # ============================================================================
    # 📋 ANSWER SUBMISSION & SCORING TESTS
    # ============================================================================
    def test_submit_answer(self):
        with app.app_context():
            quiz = Quiz(title='Quiz to answer', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

            question = Question(
                quiz_id=quiz_id,
                text='Capital of France?',
                option_a='London',
                option_b='Paris',
                option_c='Berlin',
                option_d='Madrid',
                correct_option='B'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        res = self.client.post(f'/quiz/{quiz_id}/question/{question_id}/answer', json={
            'selected_option': 'B'
        }, headers=self.auth_header)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['correct'])

    # --- Score ---
    def test_get_score(self):
        with app.app_context():
            quiz = Quiz(title='Quiz score', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

            question = Question(
                quiz_id=quiz_id,
                text='1+1=?',
                option_a='2',
                option_b='3',
                option_c='4',
                option_d='1',
                correct_option='A'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        # הגש תשובה
        self.client.post(f'/quiz/{quiz_id}/question/{question_id}/answer', json={
            'selected_option': 'A'
        }, headers=self.auth_header)

        # בקשת ציון
        res = self.client.get(f'/quiz/{quiz_id}/score', headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertIn('score', res.get_json())

    # --- User profile ---
    def test_user_details(self):
        res = self.client.get(f'/user/{self.user_id}', headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()['email'], 'test@example.com')

    def test_user_stats(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for stats', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

            question = Question(
                quiz_id=quiz_id,
                text='What is 5 + 5?',
                option_a='9',
                option_b='10',
                option_c='11',
                option_d='8',
                correct_option='B'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        self.client.post(f'/quiz/{quiz_id}/question/{question_id}/answer', json={
            'selected_option': 'B'
        }, headers=self.auth_header)

        res = self.client.get('/user/stats', headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertIn('average_score_percentage', res.get_json())


    # --- Quiz Management (Update/Delete) ---
    def test_update_quiz_as_creator(self):
        with app.app_context():
            quiz = Quiz(title='Original Quiz', description='Original desc', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

        res = self.client.put(f'/quiz/{quiz_id}', json={
            'title': 'Updated Quiz',
            'description': 'Updated description',
            'topic': 'Science'
        }, headers=self.auth_header)
        
        self.assertEqual(res.status_code, 200)
        self.assertIn('updated successfully', res.get_json()['message'])

    def test_update_quiz_unauthorized(self):
        # Create another user
        with app.app_context():
            other_user = User(
                first_name='Other',
                last_name='User',
                email='other@example.com',
                password_hash=generate_password_hash('password')
            )
            db.session.add(other_user)
            db.session.commit()
            other_user_id = other_user.id

            quiz = Quiz(title='Other User Quiz', creator_id=other_user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

        res = self.client.put(f'/quiz/{quiz_id}', json={
            'title': 'Trying to hack'
        }, headers=self.auth_header)
        
        self.assertEqual(res.status_code, 403)
        self.assertIn('Not authorized', res.get_json()['error'])

    def test_delete_quiz_as_creator(self):
        with app.app_context():
            quiz = Quiz(title='Quiz to Delete', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

        res = self.client.delete(f'/quiz/{quiz_id}', headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertIn('deleted successfully', res.get_json()['message'])

    def test_delete_quiz_unauthorized(self):
        with app.app_context():
            other_user = User(
                first_name='Other',
                last_name='User2',
                email='other2@example.com',
                password_hash=generate_password_hash('password')
            )
            db.session.add(other_user)
            db.session.commit()
            other_user_id = other_user.id

            quiz = Quiz(title='Protected Quiz', creator_id=other_user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

        res = self.client.delete(f'/quiz/{quiz_id}', headers=self.auth_header)
        self.assertEqual(res.status_code, 403)
        self.assertIn('Not authorized', res.get_json()['error'])

    # --- Question Management (Update/Delete) ---
    def test_update_question(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for Question Update', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()

            question = Question(
                quiz_id=quiz.id,
                text='Original question?',
                option_a='A',
                option_b='B',
                option_c='C',
                option_d='D',
                correct_option='A'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        res = self.client.put(f'/question/{question_id}', json={
            'text': 'Updated question?',
            'option_a': 'New A',
            'correct_option': 'B'
        }, headers=self.auth_header)

        self.assertEqual(res.status_code, 200)
        self.assertIn('updated successfully', res.get_json()['message'])

    def test_update_question_invalid_correct_option(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for Invalid Update', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()

            question = Question(
                quiz_id=quiz.id,
                text='Test question?',
                option_a='A',
                option_b='B',
                option_c='C',
                option_d='D',
                correct_option='A'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        res = self.client.put(f'/question/{question_id}', json={
            'correct_option': 'X'  # Invalid option
        }, headers=self.auth_header)

        self.assertEqual(res.status_code, 400)
        self.assertIn('Correct option must be A, B, C, or D', res.get_json()['error'])

    def test_delete_question(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for Question Delete', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()

            question = Question(
                quiz_id=quiz.id,
                text='Question to delete?',
                option_a='A',
                option_b='B',
                option_c='C',
                option_d='D',
                correct_option='A'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        res = self.client.delete(f'/question/{question_id}', headers=self.auth_header)
        self.assertEqual(res.status_code, 200)
        self.assertIn('deleted successfully', res.get_json()['message'])

    # --- Password Change ---
    def test_change_password_success(self):
        res = self.client.post('/user/change-password', json={
            'current_password': '123456',
            'new_password': 'newpassword123'
        }, headers=self.auth_header)
        
        self.assertEqual(res.status_code, 200)
        self.assertIn('changed successfully', res.get_json()['message'])

    def test_change_password_wrong_current(self):
        res = self.client.post('/user/change-password', json={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }, headers=self.auth_header)
        
        self.assertEqual(res.status_code, 400)
        self.assertIn('Current password is incorrect', res.get_json()['error'])

    def test_change_password_same_as_current(self):
        res = self.client.post('/user/change-password', json={
            'current_password': '123456',
            'new_password': '123456'
        }, headers=self.auth_header)
        
        self.assertEqual(res.status_code, 400)
        self.assertIn('must be different', res.get_json()['error'])

    def test_change_password_too_short(self):
        res = self.client.post('/user/change-password', json={
            'current_password': '123456',
            'new_password': '123'
        }, headers=self.auth_header)
        
        self.assertEqual(res.status_code, 400)
        self.assertIn('at least 6 characters', res.get_json()['error'])

    # --- Validation Tests ---
    def test_register_missing_fields(self):
        res = self.client.post('/register', json={
            'first_name': 'John',
            'email': 'john@example.com'
            # Missing last_name and password
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('required', res.get_json()['error'])

    def test_register_duplicate_email(self):
        res = self.client.post('/register', json={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'test@example.com',  # Same as existing user
            'password': 'password123'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('already registered', res.get_json()['error'])

    def test_login_missing_fields(self):
        res = self.client.post('/login', json={
            'email': 'test@example.com'
            # Missing password
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn('required', res.get_json()['error'])

    def test_login_invalid_credentials(self):
        res = self.client.post('/login', json={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn('Invalid credentials', res.get_json()['error'])

    def test_create_quiz_missing_title(self):
        res = self.client.post('/quiz', json={
            'description': 'A quiz without title'
        }, headers=self.auth_header)
        self.assertEqual(res.status_code, 400)
        self.assertIn('Title required', res.get_json()['error'])

    def test_add_question_missing_fields(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for Incomplete Question', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

        res = self.client.post(f'/quiz/{quiz_id}/question', json={
            'text': 'What is incomplete?',
            'option_a': 'A',
            'option_b': 'B'
            # Missing option_c, option_d, correct_option
        }, headers=self.auth_header)

        self.assertEqual(res.status_code, 400)
        self.assertIn('All question fields required', res.get_json()['error'])

    def test_add_question_invalid_correct_option(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for Invalid Question', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

        res = self.client.post(f'/quiz/{quiz_id}/question', json={
            'text': 'Invalid question?',
            'option_a': 'A',
            'option_b': 'B',
            'option_c': 'C',
            'option_d': 'D',
            'correct_option': 'X'  # Invalid
        }, headers=self.auth_header)

        self.assertEqual(res.status_code, 400)
        self.assertIn('Correct option must be A, B, C, or D', res.get_json()['error'])

    def test_submit_answer_invalid_option(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for Invalid Answer', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

            question = Question(
                quiz_id=quiz_id,
                text='Test question?',
                option_a='A',
                option_b='B',
                option_c='C',
                option_d='D',
                correct_option='A'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        res = self.client.post(f'/quiz/{quiz_id}/question/{question_id}/answer', json={
            'selected_option': 'X'  # Invalid option
        }, headers=self.auth_header)

        self.assertEqual(res.status_code, 400)
        self.assertIn('Selected option must be A, B, C, or D', res.get_json()['error'])

    # --- Authorization Tests ---
    def test_access_other_user_details(self):
        with app.app_context():
            other_user = User(
                first_name='Other',
                last_name='User3',
                email='other3@example.com',
                password_hash=generate_password_hash('password')
            )
            db.session.add(other_user)
            db.session.commit()
            other_user_id = other_user.id

        res = self.client.get(f'/user/{other_user_id}', headers=self.auth_header)
        self.assertEqual(res.status_code, 403)
        self.assertIn('Access denied', res.get_json()['error'])

    # --- Metrics Tests ---
    def test_get_metrics(self):
        res = self.client.get('/metrics')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('total_users', data)
        self.assertIn('total_quizzes', data)
        self.assertIn('total_questions', data)
        self.assertIn('total_answers', data)
        self.assertIn('average_score_percentage', data)

    # --- Answer Update Tests ---
    def test_submit_answer_update_existing(self):
        with app.app_context():
            quiz = Quiz(title='Quiz for Answer Update', creator_id=self.user_id)
            db.session.add(quiz)
            db.session.commit()
            quiz_id = quiz.id

            question = Question(
                quiz_id=quiz_id,
                text='Update answer test?',
                option_a='Wrong',
                option_b='Correct',
                option_c='Wrong',
                option_d='Wrong',
                correct_option='B'
            )
            db.session.add(question)
            db.session.commit()
            question_id = question.id

        # Submit first answer (wrong)
        res1 = self.client.post(f'/quiz/{quiz_id}/question/{question_id}/answer', json={
            'selected_option': 'A'
        }, headers=self.auth_header)
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.get_json()['correct'])

        # Update answer (correct)
        res2 = self.client.post(f'/quiz/{quiz_id}/question/{question_id}/answer', json={
            'selected_option': 'B'
        }, headers=self.auth_header)
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.get_json()['correct'])

    # --- Error Handling Tests ---
    def test_get_nonexistent_quiz(self):
        res = self.client.get('/quiz/99999')
        # The global error handler catches 404s and returns 500
        self.assertEqual(res.status_code, 500)

    def test_get_nonexistent_user(self):
        res = self.client.get('/user/99999', headers=self.auth_header)
        # Returns 403 because user can only access their own details (security by design)
        self.assertEqual(res.status_code, 403)


class CustomTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = defaultdict(list)
        self.current_section = "Unknown"
        
    def startTest(self, test):
        super().startTest(test)
        test_name = test._testMethodName
        
        # Determine section based on test name
        if test_name.startswith(('test_register', 'test_login', 'test_access_other_user', 'test_change_password')):
            section = "🔐 Authentication & Authorization"
        elif test_name.startswith(('test_create_quiz', 'test_get_quiz', 'test_update_quiz', 'test_delete_quiz')):
            section = "📝 Quiz Management" 
        elif test_name.startswith(('test_add_question', 'test_update_question', 'test_delete_question')):
            section = "❓ Question Management"
        elif test_name.startswith(('test_submit_answer', 'test_get_score')):
            section = "📋 Answer Submission & Scoring"
        elif test_name.startswith(('test_user_details', 'test_user_stats')):
            section = "👤 User Profile & Statistics"
        elif test_name.startswith(('test_get_metrics')):
            section = "📊 System Metrics"
        elif 'validation' in test_name or 'missing' in test_name or 'invalid' in test_name or 'duplicate' in test_name:
            section = "✅ Input Validation"
        elif 'nonexistent' in test_name or 'error' in test_name:
            section = "⚠️ Error Handling"
        else:
            section = "🔧 Other Tests"
            
        if section != self.current_section:
            # Print results of previous section if it exists
            if hasattr(self, 'current_section') and self.current_section != "Unknown":
                self._print_section_results()
            
            self.current_section = section
            print(f"\n{'='*60}")
            print(f"🧪 TESTING SECTION: {section}")
            print(f"{'='*60}")
            
        print(f"Running: {test_name}")
    
    def _print_section_results(self):
        """Print results for the current section"""
        if self.current_section in self.test_results:
            tests = self.test_results[self.current_section]
            passed = len([t for t in tests if t[1] == 'PASS'])
            failed = len([t for t in tests if t[1] == 'FAIL'])
            errors = len([t for t in tests if t[1] == 'ERROR'])
            total = len(tests)
            
            status_icon = "✅" if (failed + errors) == 0 else "❌"
            print(f"{status_icon} SECTION PASSED: {passed}/{total}")
            
            if failed > 0 or errors > 0:
                for test_name, status in tests:
                    if status in ['FAIL', 'ERROR']:
                        print(f"   • {test_name} ({status})")
        
    def addSuccess(self, test):
        super().addSuccess(test)
        test_name = getattr(test, '_testMethodName', str(test))
        self.test_results[self.current_section].append((test_name, 'PASS'))
        print(f"PASSED: {test_name}")
        
    def addError(self, test, err):
        super().addError(test, err)
        test_name = getattr(test, '_testMethodName', str(test))
        self.test_results[self.current_section].append((test_name, 'ERROR'))
        print(f"ERROR: {test_name}")
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_name = getattr(test, '_testMethodName', str(test))
        self.test_results[self.current_section].append((test_name, 'FAIL'))
        print(f"FAILED: {test_name}")

class CustomTestRunner(unittest.TextTestRunner):
    def __init__(self, **kwargs):
        kwargs['resultclass'] = CustomTestResult
        super().__init__(**kwargs)
        
    def run(self, test):
        result = super().run(test)
        self.print_final_summary(result)
        return result
        
    def print_final_summary(self, result):
        # Print results for the last section
        if hasattr(result, 'current_section') and result.current_section != "Unknown":
            result._print_section_results()
        
        # Simple overall summary
        total_tests = result.testsRun
        total_failed = len(result.failures)
        total_errors = len(result.errors)
        total_passed = total_tests - total_failed - total_errors
        
        print(f"\n{'='*80}")
        overall_icon = "✅" if (total_failed + total_errors) == 0 else "❌"
        print(f"{overall_icon} OVERALL RESULTS: {total_passed}/{total_tests} tests passed")
        
        if (total_failed + total_errors) == 0:
            print(f"🎉 ALL TESTS PASSED! Excellent work!")
        else:
            print(f"🔧 Please review and fix the failing tests.")
            
        print(f"{'='*80}\n")

if __name__ == '__main__':
    print("🚀 Starting Quiz Application Test Suite...")
    print("=" * 80)
    
    # Create custom test runner with no default output
    runner = CustomTestRunner(verbosity=0)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(FullAppTest)
    
    runner.run(suite)