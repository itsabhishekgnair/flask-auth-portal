from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db, User
from dotenv import load_dotenv
import os
import bcrypt
from itsdangerous import URLSafeTimedSerializer

load_dotenv()

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[]
)

# ── CONFIG ──────────────────────────────────────────
app.config['SECRET_KEY']                     = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER']                    = 'smtp.gmail.com'
app.config['MAIL_PORT']                      = 587
app.config['MAIL_USE_TLS']                   = True
app.config['MAIL_USERNAME']                  = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD']                  = os.getenv('MAIL_PASSWORD')

# ── INIT EXTENSIONS ─────────────────────────────────
db.init_app(app)
mail       = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

login_manager                        = LoginManager(app)
login_manager.login_view             = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── CREATE DB TABLES ─────────────────────────────────
with app.app_context():
    db.create_all()

# ── HELPER FUNCTION — SEND EMAIL ─────────────────────
def send_verification_email(user):
    token      = serializer.dumps(user.email, salt='email-verify')
    verify_url = url_for('verify_email', token=token, _external=True)

    msg      = Message('Verify Your Email',
                       sender=app.config['MAIL_USERNAME'],
                       recipients=[user.email])
    msg.html = f"""
        <h2>Hi {user.username}!</h2>
        <p>Click the button below to verify your email:</p>
        <a href="{verify_url}" style="background:#3498db; color:white;
           padding:10px 20px; text-decoration:none; border-radius:5px;">
           Verify Email
        </a>
        <p>This link expires in 1 hour.</p>
    """
    mail.send(msg)

# ── ROUTE 1 — HOME ───────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

# ── ROUTE 2 — REGISTER ───────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username         = request.form.get('username').strip()
        email            = request.form.get('email').strip().lower()
        password         = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return redirect(url_for('login'))

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(username=username, email=email,
                        password=hashed_pw.decode('utf-8'),
                        is_verified=False)
        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user)
        flash('Account created! Check your email to verify.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ── ROUTE 3 — VERIFY EMAIL ───────────────────────────
@app.route('/verify/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify', max_age=3600)
    except Exception:
        flash('Link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    if user.is_verified:
        flash('Email already verified. Please login.', 'info')
        return redirect(url_for('login'))

    user.is_verified = True
    db.session.commit()

    flash('Email verified! You can now login. ✅', 'success')
    return redirect(url_for('login'))

#-------------- add reset main sender function -------------------

def send_reset_email(user):
    token = serializer.dumps(user.email, salt='password-reset')
    reset_url = url_for('reset_password', token=token, _external=True)

    msg = Message(
        'Reset Your Password',
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )

    msg.html = f"""
        <h2>Password Reset</h2>
        <p>Click below to reset your password:</p>
        <a href="{reset_url}">Reset Password</a>
        <p>This link expires in 1 hour.</p>
    """

    mail.send(msg)

#------------------ Forgot password route ---------------------

@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            send_reset_email(user)

        flash('If the email exists, a reset link has been sent.', 'info')
        return redirect(url_for('login'))

    return render_template('forgot.html')

#-------------- Reset password Route ----------------------------

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except:
        flash('Reset link expired or invalid.', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset.html')

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user.password = hashed.decode()

        db.session.commit()

        flash('Password reset successful.', 'success')
        return redirect(url_for('login'))

    return render_template('reset.html')

# ── ROUTE 4 — LOGIN ──────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        login_input    = request.form.get('login_input').strip().lower()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if '@' in login_input:
            user = User.query.filter_by(email=login_input).first()
        else:
            user = User.query.filter_by(username=login_input).first()

        if not user or not bcrypt.checkpw(password.encode('utf-8'),
                                           user.password.encode('utf-8')):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        if not user.is_verified:
            flash('Please verify your email first.', 'warning')
            return render_template('login.html')

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.username}! 🎉', 'success')

        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))

    return render_template('login.html')

# ── ROUTE 5 — DASHBOARD ──────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

# ── ROUTE 6 — LOGOUT ─────────────────────────────────
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ── RUN ──────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)

