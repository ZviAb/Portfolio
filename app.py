import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Enable CORS and disable caching for development
CORS(app)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

db = SQLAlchemy()
db.init_app(app)
jwt = JWTManager(app)

# Configure JWT to accept tokens from Authorization header
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# JWT Error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"DEBUG: Token expired - {jwt_payload}")
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"DEBUG: Invalid token - {error}")
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"DEBUG: Missing token - {error}")
    return jsonify({'error': 'Authorization token is required'}), 401

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    quizzes = db.relationship('Quiz', backref='creator', lazy=True)
    answers = db.relationship('Answer', backref='user', lazy=True)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    topic = db.Column(db.String(100), nullable=False, default='General')
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

def log_request(status_code, user_id=None):
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'endpoint': request.endpoint,
        'url': request.url,
        'user_id': user_id,
        'status_code': status_code,
        'ip': request.remote_addr
    }
    logger.info(json.dumps(log_data))

@app.before_request
def before_request():
    pass

@app.after_request
def after_request(response):
    user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        jwt_identity = get_jwt_identity()
        if jwt_identity:
            user_id = int(jwt_identity)
    except:
        pass
    log_request(response.status_code, user_id)
    return response

@app.errorhandler(Exception)
def handle_error(e):
    error_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'error': str(e),
        'method': request.method,
        'endpoint': request.endpoint,
        'url': request.url
    }
    logger.error(json.dumps(error_data))
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ('first_name', 'last_name', 'email', 'password')):
        return jsonify({'error': 'First name, last name, email and password required'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    
    logger.info(json.dumps({
        'event': 'user_registered',
        'user_id': user.id,
        'email': user.email,
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    return jsonify({'message': 'User registered successfully', 'user_id': user.id}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = create_access_token(identity=str(user.id))
    
    logger.info(json.dumps({
        'event': 'user_login',
        'user_id': user.id,
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    return jsonify({
        'token': token, 
        'user_id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.full_name,
        'email': user.email
    }), 200

@app.route('/quiz', methods=['POST'])
@jwt_required()
def create_quiz():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title required'}), 400
    
    current_user_id = int(get_jwt_identity())
    print(f"DEBUG: JWT Identity: {current_user_id}")  # Debug line
    
    try:
        quiz = Quiz(
            title=data['title'],
            description=data.get('description', ''),
            creator_id=current_user_id
        )
        
        # Only set topic if the model supports it
        if hasattr(Quiz, 'topic'):
            quiz.topic = data.get('topic', 'General')
        
        db.session.add(quiz)
        db.session.commit()
    except Exception as e:
        print(f"Error creating quiz: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create quiz'}), 500
    
    logger.info(json.dumps({
        'event': 'quiz_created',
        'quiz_id': quiz.id,
        'user_id': get_jwt_identity(),
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    return jsonify({
        'id': quiz.id,
        'title': quiz.title,
        'description': quiz.description,
        'topic': getattr(quiz, 'topic', 'General'),
        'creator_id': quiz.creator_id,
        'created_at': quiz.created_at.isoformat()
    }), 201

@app.route('/quiz', methods=['GET'])
def get_quizzes():
    try:
        quizzes = Quiz.query.join(User).all()
        return jsonify([{
            'id': q.id,
            'title': q.title,
            'description': q.description,
            'topic': getattr(q, 'topic', 'General'),
            'creator_id': q.creator_id,
            'creator_name': q.creator.full_name,
            'created_at': q.created_at.isoformat(),
            'question_count': len(q.questions)
        } for q in quizzes]), 200
    except Exception as e:
        print(f"Error in get_quizzes: {e}")
        # If there's a database schema issue, return empty list for now
        return jsonify([]), 200

@app.route('/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    return jsonify({
        'id': quiz.id,
        'title': quiz.title,
        'description': quiz.description,
        'topic': getattr(quiz, 'topic', 'General'),
        'creator_id': quiz.creator_id,
        'created_at': quiz.created_at.isoformat(),
        'questions': [{
            'id': q.id,
            'text': q.text,
            'option_a': q.option_a,
            'option_b': q.option_b,
            'option_c': q.option_c,
            'option_d': q.option_d,
            'correct_option': q.correct_option
        } for q in quiz.questions]
    }), 200

@app.route('/quiz/<int:quiz_id>', methods=['PUT'])
@jwt_required()
def update_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.creator_id != int(get_jwt_identity()):
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.get_json()
    if data.get('title'):
        quiz.title = data['title']
    if 'description' in data:
        quiz.description = data['description']
    if data.get('topic'):
        quiz.topic = data['topic']
    
    db.session.commit()
    return jsonify({'message': 'Quiz updated successfully'}), 200

@app.route('/quiz/<int:quiz_id>', methods=['DELETE'])
@jwt_required()
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.creator_id != int(get_jwt_identity()):
        return jsonify({'error': 'Not authorized'}), 403
    
    db.session.delete(quiz)
    db.session.commit()
    return jsonify({'message': 'Quiz deleted successfully'}), 200

@app.route('/quiz/<int:quiz_id>/question', methods=['POST'])
@jwt_required()
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.creator_id != int(get_jwt_identity()):
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.get_json()
    required_fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
    if not data or not all(k in data for k in required_fields):
        return jsonify({'error': 'All question fields required'}), 400
    
    if data['correct_option'] not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'Correct option must be A, B, C, or D'}), 400
    
    question = Question(
        quiz_id=quiz_id,
        text=data['text'],
        option_a=data['option_a'],
        option_b=data['option_b'],
        option_c=data['option_c'],
        option_d=data['option_d'],
        correct_option=data['correct_option']
    )
    db.session.add(question)
    db.session.commit()
    
    return jsonify({
        'id': question.id,
        'text': question.text,
        'option_a': question.option_a,
        'option_b': question.option_b,
        'option_c': question.option_c,
        'option_d': question.option_d,
        'correct_option': question.correct_option
    }), 201

@app.route('/question/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.quiz.creator_id != int(get_jwt_identity()):
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'text' in data:
        question.text = data['text']
    if 'option_a' in data:
        question.option_a = data['option_a']
    if 'option_b' in data:
        question.option_b = data['option_b']
    if 'option_c' in data:
        question.option_c = data['option_c']
    if 'option_d' in data:
        question.option_d = data['option_d']
    if 'correct_option' in data:
        if data['correct_option'] not in ['A', 'B', 'C', 'D']:
            return jsonify({'error': 'Correct option must be A, B, C, or D'}), 400
        question.correct_option = data['correct_option']
    
    db.session.commit()
    return jsonify({'message': 'Question updated successfully'}), 200

@app.route('/question/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    if question.quiz.creator_id != int(get_jwt_identity()):
        return jsonify({'error': 'Not authorized'}), 403
    
    db.session.delete(question)
    db.session.commit()
    return jsonify({'message': 'Question deleted successfully'}), 200

@app.route('/quiz/<int:quiz_id>/question/<int:question_id>/answer', methods=['POST'])
@jwt_required()
def submit_answer(quiz_id, question_id):
    question = Question.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
    
    data = request.get_json()
    if not data or 'selected_option' not in data:
        return jsonify({'error': 'Selected option required'}), 400
    
    if data['selected_option'] not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'Selected option must be A, B, C, or D'}), 400
    
    user_id = int(get_jwt_identity())
    existing_answer = Answer.query.filter_by(user_id=user_id, question_id=question_id).first()
    
    is_correct = data['selected_option'] == question.correct_option
    
    if existing_answer:
        existing_answer.selected_option = data['selected_option']
        existing_answer.is_correct = is_correct
        existing_answer.answered_at = datetime.utcnow()
    else:
        answer = Answer(
            user_id=user_id,
            question_id=question_id,
            selected_option=data['selected_option'],
            is_correct=is_correct
        )
        db.session.add(answer)
    
    db.session.commit()
    
    # Debug info
    print(f"DEBUG - Answer stored: user_id={user_id}, quiz_id={quiz_id}, question_id={question_id}, is_correct={is_correct}")
    
    logger.info(json.dumps({
        'event': 'question_answered',
        'user_id': user_id,
        'quiz_id': quiz_id,
        'question_id': question_id,
        'is_correct': is_correct,
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    return jsonify({'correct': is_correct}), 200

@app.route('/quiz/<int:quiz_id>/score', methods=['GET'])
@jwt_required()
def get_quiz_score(quiz_id):
    user_id = get_jwt_identity()
    quiz = Quiz.query.get_or_404(quiz_id)
    
    total_questions = len(quiz.questions)
    if total_questions == 0:
        return jsonify({'score': 0, 'total': 0, 'percentage': 0}), 200
    
    correct_answers = db.session.query(Answer).join(Question).filter(
        Answer.user_id == user_id,
        Question.quiz_id == quiz_id,
        Answer.is_correct == True
    ).count()
    
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    return jsonify({
        'score': correct_answers,
        'total': total_questions,
        'percentage': round(percentage, 2)
    }), 200

@app.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_details(user_id):
    current_user_id = int(get_jwt_identity())
    
    # Users can only access their own details
    if current_user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'full_name': user.full_name,
        'created_at': user.created_at.isoformat()
    }), 200

@app.route('/user/change-password', methods=['POST'])
@jwt_required()
def change_password():
    data = request.get_json()
    if not data or not all(k in data for k in ('current_password', 'new_password')):
        return jsonify({'error': 'Current password and new password required'}), 400
    
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Verify current password
    if not check_password_hash(user.password_hash, data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    # Check if new password is the same as current password
    if data['current_password'] == data['new_password']:
        return jsonify({'error': 'New password must be different from current password'}), 400
    
    # Validate new password length
    if len(data['new_password']) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long'}), 400
    
    # Update password
    user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()
    
    logger.info(json.dumps({
        'event': 'password_changed',
        'user_id': user.id,
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    return jsonify({'message': 'Password changed successfully'}), 200

@app.route('/user/stats', methods=['GET'])
@jwt_required()
def get_user_stats():
    user_id = int(get_jwt_identity())
    
    # Count quizzes created by user
    quizzes_created = Quiz.query.filter_by(creator_id=user_id).count()
    
    # Count questions created by user
    questions_created = db.session.query(Question).join(Quiz).filter(Quiz.creator_id == user_id).count()
    
    # Count unique quizzes taken (quizzes where user has answered at least one question)
    # Use a simpler approach - get all answers by user, then count distinct quiz_ids
    user_answers = db.session.query(Answer).filter(Answer.user_id == user_id).all()
    quiz_ids_answered = set()
    for answer in user_answers:
        quiz_ids_answered.add(answer.question.quiz_id)
    quizzes_taken = len(quiz_ids_answered)
    
    # Count total answers given by user
    total_answers = Answer.query.filter_by(user_id=user_id).count()
    
    # Calculate average score across all quizzes taken
    correct_answers = Answer.query.filter_by(user_id=user_id, is_correct=True).count()
    average_score = (correct_answers / total_answers * 100) if total_answers > 0 else 0
    
    # Debug info
    print(f"DEBUG - User {user_id}: answers={total_answers}, quizzes_taken={quizzes_taken}")
    
    return jsonify({
        'quizzes_created': quizzes_created,
        'questions_created': questions_created,
        'quizzes_taken': quizzes_taken,
        'total_answers': total_answers,
        'average_score_percentage': round(average_score, 2)
    }), 200

@app.route('/debug/answers', methods=['GET'])
@jwt_required()
def debug_answers():
    user_id = int(get_jwt_identity())
    
    # Get all answers for this user
    answers = Answer.query.filter_by(user_id=user_id).all()
    
    answer_data = []
    for answer in answers:
        answer_data.append({
            'id': answer.id,
            'user_id': answer.user_id,
            'question_id': answer.question_id,
            'quiz_id': answer.question.quiz_id,
            'selected_option': answer.selected_option,
            'is_correct': answer.is_correct,
            'answered_at': answer.answered_at.isoformat()
        })
    
    return jsonify({
        'user_id': user_id,
        'total_answers': len(answers),
        'answers': answer_data
    }), 200

@app.route('/metrics', methods=['GET'])
def get_metrics():
    total_users = User.query.count()
    total_quizzes = Quiz.query.count()
    total_questions = Question.query.count()
    total_answers = Answer.query.count()
    
    avg_score = db.session.query(db.func.avg(
        db.case((Answer.is_correct == True, 1), else_=0) * 100
    )).scalar() or 0
    
    return jsonify({
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'average_score_percentage': round(float(avg_score), 2)
    }), 200

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/quiz/<int:quiz_id>/play')
def quiz_play_page(quiz_id):
    try:
        return render_template('test_quiz.html', quiz_id=quiz_id)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>", 500

# New route to take a quiz
@app.route('/quiz/<int:quiz_id>/take')
def take_quiz_page(quiz_id):
    return render_template('take_quiz.html', quiz_id=quiz_id)

# Route to preview a quiz
@app.route('/quiz/<int:quiz_id>/preview')
def preview_quiz_page(quiz_id):
    return render_template('preview_quiz.html', quiz_id=quiz_id)

@app.route('/my-quizzes')
def my_quizzes_page():
    return render_template('my_quizzes.html')

@app.route('/profile')
def profile_page():
    return render_template('profile.html')

@app.route('/create-quiz')
def create_quiz_page():
    return render_template('create_quiz.html')

@app.route('/quiz/<int:quiz_id>/manage')
def manage_quiz_page(quiz_id):
    return render_template('manage_quiz.html', quiz_id=quiz_id)

@app.route('/quiz/<int:quiz_id>/add-questions')
def add_questions_page(quiz_id):
    return render_template('add_questions.html', quiz_id=quiz_id)

@app.route('/browse-quizzes')
def browse_quizzes_page():
    return render_template('browse_quizzes.html')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist (but don't drop existing data)
        db.create_all()
        
        # Add topic column to existing quizzes if it doesn't exist
        try:
            # Check if topic column exists first
            from sqlalchemy import text
            with db.engine.connect() as conn:
                # Check if column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='quiz' AND column_name='topic'
                """))
                
                if result.fetchone() is None:
                    # Column doesn't exist, add it
                    conn.execute(text("ALTER TABLE quiz ADD COLUMN topic VARCHAR(100) DEFAULT 'General'"))
                    conn.commit()
                    print("Added topic column to quiz table")
                else:
                    print("Topic column already exists in quiz table")
        except Exception as e:
            # Handle any other database errors
            print(f"Topic column handling error: {e}")
        
        print("Database tables ready!")
    app.run(debug=True, host='0.0.0.0', port=5000)