import json
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

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

def setup_request_logging(app):
    @app.before_request
    def before_request():
        pass

    @app.after_request
    def after_request(response):
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            jwt_identity = get_jwt_identity()
            if jwt_identity:
                user_id = int(jwt_identity)
        except:
            pass
        log_request(response.status_code, user_id)
        return response

def setup_error_handler(app):
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
        from flask import jsonify
        return jsonify({'error': 'Internal server error'}), 500