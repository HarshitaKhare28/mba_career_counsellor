"""
Flask Web Application for MBA Student Counselor Chatbot
Beautiful, responsive UI with modern chat interface
"""

from flask import Flask, render_template, request, jsonify, session
import os
import uuid
import logging
from datetime import datetime
from chatbot import MBAStudentCounselor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'mba-counselor-secret-key-' + str(uuid.uuid4()))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global counselor instance (in production, you'd use proper session management)
counselors = {}

def get_counselor_for_session():
    """Get or create a counselor instance for the current session"""
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    if session_id not in counselors:
        try:
            counselors[session_id] = MBAStudentCounselor()
            logger.info(f"Created new counselor for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to create counselor: {e}")
            return None
    
    return counselors[session_id]

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the UI"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get counselor for this session
        counselor = get_counselor_for_session()
        if not counselor:
            return jsonify({'error': 'Failed to initialize counselor. Please check your database and API settings.'}), 500
        
        # Get bot response
        structured_response = counselor.chat(user_message)
        
        # Handle both old string format and new structured format for backwards compatibility
        if isinstance(structured_response, dict):
            bot_response = structured_response.get("response", "")
            university_cards = structured_response.get("university_cards", [])
            has_recommendations = structured_response.get("has_recommendations", False)
        else:
            # Backwards compatibility for string responses
            bot_response = structured_response
            university_cards = []
            has_recommendations = False
        
        # Return response with metadata
        return jsonify({
            'response': bot_response,
            'timestamp': datetime.now().isoformat(),
            'preferences': counselor.user_preferences,
            'university_cards': university_cards,
            'has_recommendations': has_recommendations
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Sorry, I encountered an issue. Please try again.'}), 500

@app.route('/reset', methods=['POST'])
def reset_chat():
    """Reset the chat session"""
    try:
        session_id = session.get('session_id')
        if session_id and session_id in counselors:
            counselors[session_id].reset_session()
            logger.info(f"Reset session {session_id}")
        
        return jsonify({'success': True, 'message': 'Chat session reset successfully!'})
        
    except Exception as e:
        logger.error(f"Reset error: {e}")
        return jsonify({'error': 'Failed to reset session'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Quick test of counselor initialization
        test_counselor = MBAStudentCounselor()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'ai_models': 'loaded',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Ensure templates and static directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    
    print("🎓 Starting MBA Student Counselor Web Interface...")
    print("📱 Access the chatbot at: http://localhost:5000")
    print("🔧 Health check at: http://localhost:5000/health")
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )