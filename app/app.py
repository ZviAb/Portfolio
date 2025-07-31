from config import create_app
from models import db
from routes import register_routes
from utils import setup_request_logging, setup_error_handler

app = create_app()

# Setup utilities
setup_request_logging(app)
setup_error_handler(app)

# Register routes
register_routes(app)

def initialize_database():
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

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True, host='0.0.0.0', port=5000)