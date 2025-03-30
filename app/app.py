from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import segno  # For Aztec code generation
import os
import random
import string

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quick_aid.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    details = db.relationship('Details', backref='user', lazy=True)

class Details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    emergency_contact = db.Column(db.String(15), nullable=False)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    blood_group = db.Column(db.String(50))
    allergies = db.Column(db.String(255))
    differently_abled = db.Column(db.String(255))
    alternate_contact = db.Column(db.String(15))
    aztec_code_path = db.Column(db.String(255))  # Path to the Aztec code image
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Utility Functions
def generate_uid():
    """Generate a unique 8-character UID."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_aztec_code(uid):
    """Generate an Aztec code for the given UID and save it as an image."""
    # Replace '127.0.0.1:5000' with your actual domain or localhost
    url = f"http://127.0.0.1:5000/details/{uid}"  # URL to display details
    aztec = segno.make_qr(url)  # Generate Aztec code with the URL
    aztec_code_path = f"static/aztec_codes/{uid}.png"
    os.makedirs(os.path.dirname(aztec_code_path), exist_ok=True)  # Ensure directory exists
    aztec.save(aztec_code_path, scale=5)  # Save the Aztec code image
    return aztec_code_path

# Routes
@app.route("/", methods=["GET", "HEAD"])
def home():
    return "Quick Aid is Running!", 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists! Please choose another.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    details = Details.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', details=details)

@app.route('/add_details', methods=['GET', 'POST'])
@login_required
def add_details():
    if request.method == 'POST':
        print("Form Data Received:", request.form)  # Debug: Print form data
        uid = generate_uid()
        details = Details(
            uid=uid,
            name=request.form['name'],
            emergency_contact=request.form['emergency_contact'],
            vehicle_number=request.form['vehicle_number'],
            blood_group=request.form.get('blood_group'),
            allergies=request.form.get('allergies'),
            differently_abled=request.form.get('differently_abled'),
            alternate_contact=request.form.get('alternate_contact'),
            user_id=current_user.id
        )
        db.session.add(details)
        db.session.commit()

        # Generate Aztec code
        aztec_code_path = generate_aztec_code(uid)
        details.aztec_code_path = aztec_code_path
        db.session.commit()

        flash('Details added successfully! Aztec code generated.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_details.html')

@app.route('/edit_details/<uid>', methods=['GET', 'POST'])
@login_required
def edit_details(uid):
    # Fetch the details to be edited
    detail = Details.query.filter_by(uid=uid, user_id=current_user.id).first()
    if not detail:
        flash('Details not found!', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Update the details
        detail.name = request.form['name']
        detail.emergency_contact = request.form['emergency_contact']
        detail.vehicle_number = request.form['vehicle_number']
        detail.blood_group = request.form.get('blood_group')
        detail.allergies = request.form.get('allergies')
        detail.differently_abled = request.form.get('differently_abled')
        detail.alternate_contact = request.form.get('alternate_contact')
        db.session.commit()

        flash('Details updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_details.html', detail=detail)

@app.route('/details/<uid>')
def show_details(uid):
    # Fetch the details from the database
    detail = Details.query.filter_by(uid=uid).first()
    if not detail:
        return "Details not found!", 404

    # Render a template to display the details
    return render_template('show_details.html', detail=detail)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

# Run the application
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()  # Create database tables if they don't exist
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    app.run(debug=True)      
