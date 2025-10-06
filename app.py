from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded from .env file")

app = Flask(__name__)

# Database configuration
database_url = os.getenv(
    'DATABASE_URL', 
    'postgresql://username:password@localhost:5432/users'
)
logger.info(f"Database URL configured: {database_url.replace(database_url.split('@')[0].split('://')[1], '***:***') if '@' in database_url else database_url}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True,
    'connect_args': {
        'connect_timeout': 10,
        'application_name': 'slowerai-backend'
    }
}
logger.info("SQLAlchemy configuration completed")

# Initialize extensions
logger.info("Initializing SQLAlchemy database connection")
db = SQLAlchemy(app)
logger.info("SQLAlchemy database connection initialized")

logger.info("Initializing CORS")
CORS(app)
logger.info("CORS initialized successfully")

# User model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    logger.debug("Health check endpoint accessed")
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
        logger.debug("Database connection test successful")
    except Exception as e:
        db_status = f'error: {str(e)}'
        logger.error(f"Database connection test failed: {str(e)}")
    
    health_data = {
        'status': 'healthy', 
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'environment': os.getenv('FLASK_ENV', 'development')
    }
    
    logger.debug(f"Health check response: {health_data}")
    return jsonify(health_data)

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)
        role = request.args.get('role', '', type=str)
        is_active = request.args.get('is_active', None, type=str)
        
        # Build query
        query = db.session.query(User)
        
        # Apply filters
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%'),
                    User.full_name.ilike(f'%{search}%')
                )
            )
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            active_bool = is_active.lower() == 'true'
            query = query.filter(User.is_active == active_bool)
        
        # Pagination
        total = query.count()
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        pages = (total + per_page - 1) // per_page  # Calculate total pages
        has_next = page < pages
        has_prev = page > 1
        
        return jsonify({
            'users': [user.to_dict() for user in users],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_next': has_next,
                'has_prev': has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        if db.session.query(User).filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if db.session.query(User).filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            role=data.get('role', 'user'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        data = request.get_json()
        
        # Update fields
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'role' in data:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(user.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_users = db.session.query(User).count()
        active_users = db.session.query(User).filter_by(is_active=True).count()
        inactive_users = total_users - active_users
        
        # Role distribution
        roles = db.session.query(User.role, db.func.count(User.id)).group_by(User.role).all()
        role_distribution = {role: count for role, count in roles}
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'role_distribution': role_distribution
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize database tables
def create_tables():
    #Verify database connection
    try:
        logger.info("Testing database connection...")
        db.session.execute(text('SELECT 1'))
        logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        logger.exception("Database connection error details:")
        raise
    
    logger.info("Starting database table creation")
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise
    
    # Add sample data if no users exist
    logger.info("Checking for existing users in database")
    try:
        user_count = db.session.query(User).count()
        logger.info(f"Found {user_count} existing users in database")
    except Exception as e:
        logger.error(f"Error checking user count: {str(e)}")
        logger.exception("User count error details:")
        raise
    
    if user_count == 0:
        logger.info("No users found, creating sample users")
        sample_users = [
            User(username='admin', email='admin@example.com', full_name='Administrator', role='admin'),
            User(username='john_doe', email='john@example.com', full_name='John Doe', role='user'),
            User(username='jane_smith', email='jane@example.com', full_name='Jane Smith', role='moderator'),
            User(username='bob_wilson', email='bob@example.com', full_name='Bob Wilson', role='user'),
            User(username='alice_brown', email='alice@example.com', full_name='Alice Brown', role='user'),
        ]
        
        for user in sample_users:
            db.session.add(user)
        
        try:
            db.session.commit()
            logger.info("Sample users created and committed to database successfully")
        except Exception as e:
            logger.error(f"Error committing sample users to database: {str(e)}")
            db.session.rollback()
            raise
    else:
        logger.info("Users already exist in database, skipping sample user creation")

if __name__ == '__main__':
    logger.info("Starting Flask application initialization")
    
    try:
        with app.app_context():
            logger.info("Application context created, initializing database")
            create_tables()
            logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    # Log environment information
    logger.info(f"Flask environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Flask debug mode: {os.getenv('FLASK_DEBUG', 'True')}")
    logger.info(f"Application will run on host: 0.0.0.0, port: 5000")
    
    logger.info("Starting Flask development server")
    app.run(debug=True, host='0.0.0.0', port=5000)

