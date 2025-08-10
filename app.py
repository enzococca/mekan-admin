"""
MEKAN Admin Interface - User and Role Management
Web interface for managing users, roles, and permissions
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import secrets
from datetime import datetime, timedelta
import os
from functools import wraps
from api_routes_simple import api_bp
from api_archaeological import api_arch
from api_archaeological_fixed import api_arch_fixed

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Enable CORS for API routes
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://mekan-admin.onrender.com", "http://localhost:5001"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Database configuration - Supabase
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'aws-0-eu-central-1.pooler.supabase.com'),
    'port': os.getenv('POSTGRES_PORT', 5432),
    'database': os.getenv('POSTGRES_DATABASE', 'postgres'),
    'user': os.getenv('POSTGRES_USER', 'postgres.ctlqtgwyuknxpkssidcd'),
    'password': os.getenv('POSTGRES_PASSWORD', '6pRZELCQUoGFIcf')
}

# Set config for blueprint access
app.config.update(DB_CONFIG)

# Register API blueprints
app.register_blueprint(api_bp)
app.register_blueprint(api_arch)
app.register_blueprint(api_arch_fixed)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['user_id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.full_name = user_data['full_name']
        self.role_id = user_data['role_id']
        self.role_name = user_data.get('role_name')
        self.permissions = user_data

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT u.*, r.role_name, r.can_view, r.can_create, 
                   r.can_edit, r.can_delete, r.can_manage_users,
                   r.can_export, r.can_generate_reports
            FROM system_users u
            JOIN user_roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s AND u.is_active = true
            """,
            (user_id,)
        )
        user_data = cursor.fetchone()
        return User(user_data) if user_data else None
    finally:
        cursor.close()
        conn.close()

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.permissions.get('can_manage_users'):
            flash('Admin access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    """Dashboard"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get statistics
        stats = {}
        
        cursor.execute("SELECT COUNT(*) as count FROM system_users WHERE is_active = true")
        stats['active_users'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM invitation_tokens WHERE is_active = true")
        stats['active_tokens'] = cursor.fetchone()['count']
        
        cursor.execute(
            """
            SELECT r.role_name, COUNT(u.user_id) as count
            FROM user_roles r
            LEFT JOIN system_users u ON r.role_id = u.role_id AND u.is_active = true
            GROUP BY r.role_name, r.role_id
            ORDER BY r.role_level
            """
        )
        stats['users_by_role'] = cursor.fetchall()
        
        # Get recent activity
        cursor.execute(
            """
            SELECT l.*, u.username, u.full_name
            FROM user_activity_log l
            JOIN system_users u ON l.user_id = u.user_id
            ORDER BY l.created_at DESC
            LIMIT 10
            """
        )
        recent_activity = cursor.fetchall()
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_activity=recent_activity)
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT u.*, r.role_name, r.can_view, r.can_create, 
                       r.can_edit, r.can_delete, r.can_manage_users,
                       r.can_export, r.can_generate_reports
                FROM system_users u
                JOIN user_roles r ON u.role_id = r.role_id
                WHERE u.username = %s AND u.is_active = true
                """,
                (username,)
            )
            user_data = cursor.fetchone()
            
            if user_data and bcrypt.checkpw(password.encode('utf-8'), 
                                           user_data['password_hash'].encode('utf-8')):
                user = User(user_data)
                login_user(user)
                
                # Update last login
                cursor.execute(
                    "UPDATE system_users SET last_login = NOW() WHERE user_id = %s",
                    (user.id,)
                )
                
                # Log activity
                cursor.execute(
                    "SELECT log_user_activity(%s, %s)",
                    (user.id, 'login')
                )
                
                conn.commit()
                
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
                
        finally:
            cursor.close()
            conn.close()
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    # Log activity
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT log_user_activity(%s, %s)",
            (current_user.id, 'logout')
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
        
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT u.*, r.role_name
            FROM system_users u
            JOIN user_roles r ON u.role_id = r.role_id
            ORDER BY u.created_at DESC
            """
        )
        users = cursor.fetchall()
        
        cursor.execute("SELECT * FROM user_roles ORDER BY role_level")
        roles = cursor.fetchall()
        
        return render_template('users.html', users=users, roles=roles)
    finally:
        cursor.close()
        conn.close()

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        if request.method == 'POST':
            # Update user
            cursor.execute(
                """
                UPDATE system_users 
                SET full_name = %s, email = %s, role_id = %s, 
                    organization = %s, is_active = %s
                WHERE user_id = %s
                """,
                (
                    request.form['full_name'],
                    request.form['email'],
                    request.form['role_id'],
                    request.form.get('organization'),
                    'is_active' in request.form,
                    user_id
                )
            )
            
            # Log activity
            cursor.execute(
                "SELECT log_user_activity(%s, %s, %s, %s::uuid)",
                (current_user.id, 'edit_user', 'system_users', None)
            )
            
            conn.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('users'))
            
        # Get user data
        cursor.execute(
            """
            SELECT u.*, r.role_name
            FROM system_users u
            JOIN user_roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
            """,
            (user_id,)
        )
        user = cursor.fetchone()
        
        cursor.execute("SELECT * FROM user_roles ORDER BY role_level")
        roles = cursor.fetchall()
        
        return render_template('edit_user.html', user=user, roles=roles)
        
    finally:
        cursor.close()
        conn.close()

@app.route('/tokens')
@login_required
@admin_required
def tokens():
    """Token management page"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT t.*, r.role_name, u.username as created_by_username
            FROM invitation_tokens t
            JOIN user_roles r ON t.role_id = r.role_id
            JOIN system_users u ON t.created_by = u.user_id
            ORDER BY t.created_at DESC
            """
        )
        tokens = cursor.fetchall()
        
        return render_template('tokens.html', tokens=tokens)
    finally:
        cursor.close()
        conn.close()

@app.route('/tokens/create', methods=['POST'])
@login_required
@admin_required
def create_token():
    """Create new invitation token"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Generate token
        cursor.execute("SELECT generate_invitation_token()")
        token = cursor.fetchone()[0]
        
        # Calculate expiration
        days_valid = int(request.form.get('days_valid', 30))
        expires_at = datetime.now() + timedelta(days=days_valid) if days_valid > 0 else None
        
        # Create token
        cursor.execute(
            """
            INSERT INTO invitation_tokens (
                token, role_id, max_uses, expires_at, 
                organization, notes, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                token,
                request.form['role_id'],
                request.form.get('max_uses', 1),
                expires_at,
                request.form.get('organization'),
                request.form.get('notes'),
                current_user.id
            )
        )
        
        # Log activity
        cursor.execute(
            "SELECT log_user_activity(%s, %s, %s)",
            (current_user.id, 'create_token', 'invitation_tokens')
        )
        
        conn.commit()
        
        flash(f'Token created: {token}', 'success')
        return redirect(url_for('tokens'))
        
    finally:
        cursor.close()
        conn.close()

@app.route('/tokens/<int:token_id>/revoke', methods=['POST'])
@login_required
@admin_required
def revoke_token(token_id):
    """Revoke token"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "UPDATE invitation_tokens SET is_active = false WHERE token_id = %s",
            (token_id,)
        )
        
        # Log activity
        cursor.execute(
            "SELECT log_user_activity(%s, %s, %s)",
            (current_user.id, 'revoke_token', 'invitation_tokens')
        )
        
        conn.commit()
        flash('Token revoked', 'success')
        
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('tokens'))

@app.route('/roles')
@login_required
@admin_required
def roles():
    """Role management page"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            """
            SELECT r.*, COUNT(u.user_id) as user_count
            FROM user_roles r
            LEFT JOIN system_users u ON r.role_id = u.role_id
            GROUP BY r.role_id
            ORDER BY r.role_level
            """
        )
        roles = cursor.fetchall()
        
        return render_template('roles.html', roles=roles)
    finally:
        cursor.close()
        conn.close()

@app.route('/activity')
@login_required
def activity():
    """View activity log"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM user_activity_log")
        total = cursor.fetchone()['count']
        
        # Get activities
        cursor.execute(
            """
            SELECT l.*, u.username, u.full_name
            FROM user_activity_log l
            JOIN system_users u ON l.user_id = u.user_id
            ORDER BY l.created_at DESC
            LIMIT %s OFFSET %s
            """,
            (per_page, offset)
        )
        activities = cursor.fetchall()
        
        return render_template('activity.html', 
                             activities=activities,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page)
    finally:
        cursor.close()
        conn.close()

@app.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for statistics"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        stats = {}
        
        # User stats
        cursor.execute(
            """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM system_users
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date
            """
        )
        stats['new_users'] = cursor.fetchall()
        
        # Activity stats
        cursor.execute(
            """
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM user_activity_log
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date
            """
        )
        stats['activity'] = cursor.fetchall()
        
        return jsonify(stats)
        
    finally:
        cursor.close()
        conn.close()

@app.route('/archaeological')
@login_required
def archaeological_enhanced():
    """Enhanced archaeological data management with relationships"""
    return render_template('archaeological_enhanced_fixed.html')

# Create initial admin user if none exists
def create_initial_admin():
    """Create initial admin user"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM system_users")
        if cursor.fetchone()[0] == 0:
            # Create admin user
            password = 'admin123'  # Change this!
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute(
                """
                INSERT INTO system_users (
                    username, email, full_name, password_hash, role_id
                ) VALUES (%s, %s, %s, %s, 
                    (SELECT role_id FROM user_roles WHERE role_name = 'admin')
                )
                """,
                ('admin', 'admin@mekan.local', 'System Administrator', 
                 password_hash.decode('utf-8'))
            )
            conn.commit()
            print("Initial admin user created - Username: admin, Password: admin123")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_initial_admin()
    app.run(debug=True, host='0.0.0.0', port=5001)
