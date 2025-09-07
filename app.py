from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import sqlite3
import os
from datetime import datetime
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import PyPDF2
import docx

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///internship_recommendation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Custom Jinja filter for JSON parsing
@app.template_filter('from_json')
def from_json(value):
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Profile information
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    education_level = db.Column(db.String(50))
    stream = db.Column(db.String(100))
    skills = db.Column(db.Text)  # JSON string
    certifications = db.Column(db.Text)  # JSON string
    projects = db.Column(db.Text)  # JSON string
    location_preference = db.Column(db.String(100))
    resume_path = db.Column(db.String(200))

class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    stipend = db.Column(db.String(100))
    status = db.Column(db.String(50))
    skills_required = db.Column(db.Text)
    apply_by = db.Column(db.String(50))
    about_internship = db.Column(db.Text)
    who_can_apply = db.Column(db.Text)
    about_company = db.Column(db.Text)
    end_date = db.Column(db.String(50))

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Import internship data if not already imported
        if Internship.query.count() == 0:
            import_internship_data()

def import_internship_data():
    """Import internship data from CSV file"""
    try:
        df = pd.read_csv('IntershipDataset.csv')
        
        for _, row in df.iterrows():
            internship = Internship(
                title=row['Title'],
                company_name=row['Company Name'],
                location=row['Location'],
                start_date=row['Start Date'],
                duration=row['Duration'],
                stipend=row['Stipend'],
                status=row['Status'],
                skills_required=row['skills required'],
                apply_by=row['apply by'],
                about_internship=row['about the internship'],
                who_can_apply=row['who can apply'],
                about_company=row['About the company'],
                end_date=row['End Date']
            )
            db.session.add(internship)
        
        db.session.commit()
        print(f"Imported {len(df)} internships successfully!")
        
    except Exception as e:
        print(f"Error importing data: {e}")

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Force a fresh query from database
    user = User.query.get(session['user_id'])
    
    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            print(f"Profile update request received for user {user.username}")
            print(f"Form data: {dict(request.form)}")
            
            # Update basic profile fields
            user.full_name = request.form.get('full_name', '').strip()
            user.phone = request.form.get('phone', '').strip()
            user.education_level = request.form.get('education_level', '').strip()
            user.stream = request.form.get('stream', '').strip()
            user.location_preference = request.form.get('location_preference', '').strip()
            
            # Handle skills as JSON
            skills_text = request.form.get('skills', '').strip()
            if skills_text:
                skills = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
                user.skills = json.dumps(skills)
            else:
                user.skills = json.dumps([])
            
            # Handle certifications as JSON
            certifications_text = request.form.get('certifications', '').strip()
            if certifications_text:
                certifications = [cert.strip() for cert in certifications_text.split(',') if cert.strip()]
                user.certifications = json.dumps(certifications)
            else:
                user.certifications = json.dumps([])
            
            # Handle projects as JSON
            projects_text = request.form.get('projects', '').strip()
            if projects_text:
                projects = [project.strip() for project in projects_text.split(',') if project.strip()]
                user.projects = json.dumps(projects)
            else:
                user.projects = json.dumps([])
            
            print(f"Before commit - User data: full_name={user.full_name}, phone={user.phone}, education_level={user.education_level}")
            
            # Commit changes
            db.session.commit()
            print(f"Profile updated successfully for user {user.username}: {user.full_name}")
            
            # Force a fresh query to verify the data was saved
            db.session.expunge(user)  # Remove from session
            fresh_user = User.query.get(session['user_id'])  # Get fresh data
            
            print(f"After commit - Fresh user data:")
            print(f"  Full Name: {fresh_user.full_name}")
            print(f"  Phone: {fresh_user.phone}")
            print(f"  Education Level: {fresh_user.education_level}")
            print(f"  Stream: {fresh_user.stream}")
            print(f"  Skills: {fresh_user.skills}")
            print(f"  Location Preference: {fresh_user.location_preference}")
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            print(f"Error updating profile: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
            return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Force a fresh query from database instead of using cached session data
    user = User.query.get(session['user_id'])
    
    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Debug: Print user data to verify it's up to date
    print(f"=== RECOMMENDATIONS DEBUG ===")
    print(f"User ID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Full Name: {user.full_name}")
    print(f"Education Level: {user.education_level}")
    print(f"Stream: {user.stream}")
    print(f"Skills: {user.skills}")
    print(f"Location Preference: {user.location_preference}")
    print(f"Phone: {user.phone}")
    print(f"Certifications: {user.certifications}")
    print(f"Projects: {user.projects}")
    print(f"=============================")
    
    recommendations = get_recommendations(user, limit=5)
    
    return render_template('recommendations.html', 
                         user=user, 
                         recommendations=recommendations)

@app.route('/all_internships')
def all_internships():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get all internships with pagination
    internships = Internship.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('all_internships.html', 
                         user=user, 
                         internships=internships)

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    
    if 'resume' not in request.files:
        flash('No file selected!', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['resume']
    
    if file.filename == '':
        flash('No file selected!', 'error')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user.id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text from resume
        text = ""
        try:
            if filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
                print(f"PDF text extracted: {len(text)} characters")
                if not text:
                    flash('Could not extract text from PDF. The file might be corrupted or password-protected. Please try a different file or add skills manually.', 'warning')
                    return redirect(url_for('profile'))
            elif filename.lower().endswith('.docx'):
                text = extract_text_from_docx(file_path)
                print(f"DOCX text extracted: {len(text)} characters")
                if not text:
                    flash('Could not extract text from DOCX. The file might be corrupted. Please try a different file or add skills manually.', 'warning')
                    return redirect(url_for('profile'))
            else:
                flash('Unsupported file format. Please upload PDF or DOCX files only.', 'error')
                return redirect(url_for('profile'))
        except Exception as e:
            print(f"Error extracting text: {e}")
            flash(f'Error processing resume: {str(e)}. Please try a different file or add skills manually.', 'error')
            return redirect(url_for('profile'))
        
        if text and len(text.strip()) > 10:  # Ensure we have meaningful text
            try:
                # Extract comprehensive profile data from resume
                profile_data = extract_profile_data_from_resume(text)
                print(f"Extracted profile data: {profile_data}")
                
                # Update user profile with extracted data
                updated_fields = []
                
                # Update full name if found and not already set
                if profile_data['full_name'] and not user.full_name:
                    user.full_name = profile_data['full_name']
                    updated_fields.append('Full Name')
                
                # Update phone if found and not already set
                if profile_data['phone'] and not user.phone:
                    user.phone = profile_data['phone']
                    updated_fields.append('Phone')
                
                # Update education level if found and not already set
                if profile_data['education_level'] and not user.education_level:
                    user.education_level = profile_data['education_level']
                    updated_fields.append('Education Level')
                
                # Update stream if found and not already set
                if profile_data['stream'] and not user.stream:
                    user.stream = profile_data['stream']
                    updated_fields.append('Stream')
                
                # Update skills (merge with existing)
                if profile_data['skills']:
                    existing_skills = json.loads(user.skills) if user.skills else []
                    all_skills = list(set(existing_skills + profile_data['skills']))
                    user.skills = json.dumps(all_skills)
                    updated_fields.append(f'{len(profile_data["skills"])} Skills')
                
                # Update certifications (merge with existing)
                if profile_data['certifications']:
                    existing_certs = json.loads(user.certifications) if user.certifications else []
                    all_certs = list(set(existing_certs + profile_data['certifications']))
                    user.certifications = json.dumps(all_certs)
                    updated_fields.append(f'{len(profile_data["certifications"])} Certifications')
                
                # Update projects (merge with existing)
                if profile_data['projects']:
                    existing_projects = json.loads(user.projects) if user.projects else []
                    all_projects = list(set(existing_projects + profile_data['projects']))
                    user.projects = json.dumps(all_projects)
                    updated_fields.append(f'{len(profile_data["projects"])} Projects')
                
                # Update location preference if found and not already set
                if profile_data['location_preference'] and not user.location_preference:
                    user.location_preference = profile_data['location_preference']
                    updated_fields.append('Location Preference')
                
                # Save resume path
                user.resume_path = file_path
                
                # Commit changes
                db.session.commit()
                print(f"Resume data saved for user {user.username}")
                
                # Prepare success message
                if updated_fields:
                    success_msg = f'✅ Resume uploaded successfully! Updated: {", ".join(updated_fields)}'
                    
                    # Check for missing fields
                    missing_fields = []
                    if not user.full_name:
                        missing_fields.append('Full Name')
                    if not user.phone:
                        missing_fields.append('Phone')
                    if not user.education_level:
                        missing_fields.append('Education Level')
                    if not user.stream:
                        missing_fields.append('Stream')
                    if not user.location_preference:
                        missing_fields.append('Location Preference')
                    
                    if missing_fields:
                        success_msg += f'<br><br>⚠️ Please manually update: {", ".join(missing_fields)}'
                    
                    flash(success_msg, 'success')
                else:
                    flash('Resume uploaded but no new information could be extracted. Your profile is already complete!', 'info')
            except Exception as e:
                print(f"Error processing resume data: {e}")
                flash(f'Error processing resume data: {str(e)}. Please try again or add information manually.', 'error')
        else:
            flash('Could not extract meaningful text from resume. Please ensure the file is not corrupted and try again.', 'error')
        
        return redirect(url_for('profile'))
    else:
        flash('Invalid file type! Please upload PDF or DOCX files only.', 'error')
        return redirect(url_for('profile'))

@app.route('/internship/<int:internship_id>')
def internship_detail(internship_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    internship = db.session.get(Internship, internship_id)
    if not internship:
        flash('Internship not found!', 'error')
        return redirect(url_for('recommendations'))
    
    user = db.session.get(User, session['user_id'])
    return render_template('internship_detail.html', internship=internship, user=user)

@app.route('/apply_internship/<int:internship_id>')
def apply_internship(internship_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    internship = db.session.get(Internship, internship_id)
    if not internship:
        flash('Internship not found!', 'error')
        return redirect(url_for('recommendations'))
    
    user = db.session.get(User, session['user_id'])
    
    # Create application record (in a real app, this would be stored in database)
    application_data = {
        'user_id': user.id,
        'user_name': user.full_name or user.username,
        'user_email': user.email,
        'internship_id': internship.id,
        'internship_title': internship.title,
        'company_name': internship.company_name,
        'applied_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # In a real application, this would:
    # 1. Store application in database
    # 2. Send email to company
    # 3. Redirect to company's application portal
    # 4. Send confirmation email to user
    
    flash(f'✅ Application submitted successfully for {internship.title} at {internship.company_name}! You will receive a confirmation email shortly.', 'success')
    return redirect(url_for('internship_detail', internship_id=internship_id))

@app.route('/extract_from_text', methods=['POST'])
def extract_from_text():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.session.get(User, session['user_id'])
    resume_text = request.form.get('resume_text', '')
    
    if not resume_text.strip():
        flash('Please paste your resume text first!', 'error')
        return redirect(url_for('profile'))
    
    # Extract comprehensive profile data from resume text
    profile_data = extract_profile_data_from_resume(resume_text)
    print(f"Extracted profile data from text: {profile_data}")
    
    # Update user profile with extracted data
    updated_fields = []
    
    # Update full name if found and not already set
    if profile_data['full_name'] and not user.full_name:
        user.full_name = profile_data['full_name']
        updated_fields.append('Full Name')
    
    # Update phone if found and not already set
    if profile_data['phone'] and not user.phone:
        user.phone = profile_data['phone']
        updated_fields.append('Phone')
    
    # Update education level if found and not already set
    if profile_data['education_level'] and not user.education_level:
        user.education_level = profile_data['education_level']
        updated_fields.append('Education Level')
    
    # Update stream if found and not already set
    if profile_data['stream'] and not user.stream:
        user.stream = profile_data['stream']
        updated_fields.append('Stream')
    
    # Update skills (merge with existing)
    if profile_data['skills']:
        existing_skills = json.loads(user.skills) if user.skills else []
        all_skills = list(set(existing_skills + profile_data['skills']))
        user.skills = json.dumps(all_skills)
        updated_fields.append(f'{len(profile_data["skills"])} Skills')
    
    # Update certifications (merge with existing)
    if profile_data['certifications']:
        existing_certs = json.loads(user.certifications) if user.certifications else []
        all_certs = list(set(existing_certs + profile_data['certifications']))
        user.certifications = json.dumps(all_certs)
        updated_fields.append(f'{len(profile_data["certifications"])} Certifications')
    
    # Update projects (merge with existing)
    if profile_data['projects']:
        existing_projects = json.loads(user.projects) if user.projects else []
        all_projects = list(set(existing_projects + profile_data['projects']))
        user.projects = json.dumps(all_projects)
        updated_fields.append(f'{len(profile_data["projects"])} Projects')
    
    # Update location preference if found and not already set
    if profile_data['location_preference'] and not user.location_preference:
        user.location_preference = profile_data['location_preference']
        updated_fields.append('Location Preference')
    
    # Commit changes
    db.session.commit()
    
    # Prepare success message
    if updated_fields:
        success_msg = f'✅ Profile updated successfully! Updated: {", ".join(updated_fields)}'
        
        # Check for missing fields
        missing_fields = []
        if not user.full_name:
            missing_fields.append('Full Name')
        if not user.phone:
            missing_fields.append('Phone')
        if not user.education_level:
            missing_fields.append('Education Level')
        if not user.stream:
            missing_fields.append('Stream')
        if not user.location_preference:
            missing_fields.append('Location Preference')
        
        if missing_fields:
            success_msg += f'<br><br>⚠️ Please manually update: {", ".join(missing_fields)}'
        
        flash(success_msg, 'success')
    else:
        flash('No new information could be extracted from the text. Your profile is already complete!', 'info')
    
    return redirect(url_for('profile'))

@app.route('/my_applications')
def my_applications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    # In a real app, this would fetch from applications table
    return render_template('my_applications.html', user=user)

@app.route('/test_recommendations')
def test_recommendations():
    """Test route to debug recommendations"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    print(f"=== TEST RECOMMENDATIONS ===")
    print(f"User: {user.username}")
    print(f"Profile data:")
    print(f"  Full Name: {user.full_name}")
    print(f"  Education: {user.education_level}")
    print(f"  Stream: {user.stream}")
    print(f"  Skills: {user.skills}")
    print(f"  Location: {user.location_preference}")
    
    # Test recommendation generation
    recommendations = get_recommendations(user, limit=3)
    
    return jsonify({
        'user_profile': {
            'username': user.username,
            'full_name': user.full_name,
            'education_level': user.education_level,
            'stream': user.stream,
            'skills': user.skills,
            'location_preference': user.location_preference
        },
        'recommendations_count': len(recommendations),
        'recommendations': [{'title': r.title, 'company': r.company_name} for r in recommendations]
    })

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_error:
                    print(f"Error extracting text from page {page_num + 1}: {page_error}")
                    continue
            return text.strip()
    except Exception as e:
        print(f"Error reading PDF file {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text.strip() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading DOCX file {file_path}: {e}")
        return ""

def extract_profile_data_from_resume(text):
    """Extract comprehensive profile data from resume text"""
    import re
    
    text_lower = text.lower()
    profile_data = {
        'full_name': '',
        'phone': '',
        'email': '',
        'education_level': '',
        'stream': '',
        'skills': [],
        'certifications': [],
        'projects': [],
        'location_preference': ''
    }
    
    # Extract Full Name (usually at the beginning)
    lines = text.split('\n')
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if len(line) > 3 and len(line) < 50 and not any(word in line.lower() for word in ['email', 'phone', 'address', 'contact', 'resume', 'cv']):
            # Check if it looks like a name (contains letters and possibly spaces)
            if re.match(r'^[A-Za-z\s\.]+$', line) and len(line.split()) <= 4:
                profile_data['full_name'] = line.title()
                break
    
    # Extract Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        profile_data['email'] = emails[0]
    
    # Extract Phone Number
    phone_patterns = [
        r'\+?91[-.\s]?\d{10}',
        r'\+?1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{10}'
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            profile_data['phone'] = phones[0]
            break
    
    # Extract Education Level
    education_keywords = {
        'phd': ['phd', 'doctor of philosophy', 'doctorate'],
        'master': ['master', 'mba', 'ms', 'ma', 'mtech', 'mca'],
        'bachelor': ['bachelor', 'btech', 'bca', 'be', 'bsc', 'ba', 'bcom'],
        'diploma': ['diploma', 'certificate'],
        'high school': ['high school', '12th', 'intermediate']
    }
    
    for level, keywords in education_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            profile_data['education_level'] = level.title()
            break
    
    # Extract Stream/Field
    stream_keywords = {
        'computer science': ['computer science', 'cs', 'cse', 'computer engineering', 'software engineering'],
        'electronics': ['electronics', 'ece', 'electronic engineering', 'electrical'],
        'mechanical': ['mechanical', 'me', 'mechanical engineering'],
        'civil': ['civil', 'ce', 'civil engineering'],
        'business': ['business', 'management', 'mba', 'business administration'],
        'marketing': ['marketing', 'digital marketing', 'marketing management'],
        'finance': ['finance', 'financial', 'accounting', 'commerce'],
        'design': ['design', 'graphic design', 'ui/ux', 'visual design'],
        'data science': ['data science', 'data analytics', 'machine learning', 'ai'],
        'human resources': ['human resources', 'hr', 'personnel management']
    }
    
    for stream, keywords in stream_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            profile_data['stream'] = stream.title()
            break
    
    # Extract Skills
    technical_skills = [
        'python', 'java', 'javascript', 'html', 'css', 'react', 'angular', 'vue',
        'node.js', 'express', 'django', 'flask', 'spring', 'mysql', 'postgresql',
        'mongodb', 'redis', 'aws', 'azure', 'docker', 'kubernetes', 'git',
        'machine learning', 'data science', 'artificial intelligence', 'ai',
        'android', 'ios', 'flutter', 'react native', 'xamarin',
        'photoshop', 'illustrator', 'figma', 'sketch', 'adobe',
        'excel', 'powerpoint', 'word', 'office', 'google analytics',
        'seo', 'sem', 'digital marketing', 'social media', 'content writing',
        'project management', 'agile', 'scrum', 'tensorflow', 'scikit-learn',
        'pandas', 'numpy', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'linux', 'windows', 'macos', 'android studio', 'xcode'
    ]
    
    soft_skills = [
        'leadership', 'communication', 'teamwork', 'problem solving',
        'time management', 'creativity', 'adaptability', 'critical thinking',
        'analytical', 'research', 'presentation', 'negotiation', 'mentoring',
        'collaboration', 'innovation', 'decision making', 'conflict resolution'
    ]
    
    found_skills = []
    for skill in technical_skills + soft_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    profile_data['skills'] = list(set(found_skills))
    
    # Extract Certifications
    cert_keywords = ['certified', 'certification', 'certificate', 'license', 'diploma']
    cert_pattern = r'([A-Za-z\s]+(?:certified|certification|certificate|license|diploma)[A-Za-z\s]*)'
    certifications = re.findall(cert_pattern, text, re.IGNORECASE)
    profile_data['certifications'] = [cert.strip().title() for cert in certifications if len(cert.strip()) > 5]
    
    # Extract Projects
    project_keywords = ['project', 'developed', 'built', 'created', 'implemented']
    projects = []
    for keyword in project_keywords:
        # Look for sentences containing project keywords
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            if keyword in sentence.lower() and len(sentence.strip()) > 10:
                # Extract project name (first few words after keyword)
                words = sentence.strip().split()
                if len(words) > 3:
                    project_name = ' '.join(words[:min(6, len(words))])
                    if len(project_name) > 5 and project_name not in projects:
                        projects.append(project_name)
    
    profile_data['projects'] = projects[:5]  # Limit to 5 projects
    
    # Extract Location Preference
    location_keywords = [
        'bangalore', 'mumbai', 'delhi', 'chennai', 'kolkata', 'hyderabad', 'pune',
        'gurgaon', 'noida', 'work from home', 'remote', 'hybrid'
    ]
    
    for location in location_keywords:
        if location in text_lower:
            if location in ['work from home', 'remote', 'hybrid']:
                profile_data['location_preference'] = 'Work From Home'
            else:
                profile_data['location_preference'] = location.title()
            break
    
    return profile_data

def extract_skills_from_text(text):
    """Extract skills from resume text using simple keyword matching"""
    profile_data = extract_profile_data_from_resume(text)
    return profile_data['skills']

def get_recommendations(user, limit=5):
    """Generate internship recommendations based on user profile"""
    # Get all internships
    internships = Internship.query.all()
    
    if not internships:
        print("No internships found in database!")
        return []
    
    scored_internships = []
    
    print(f"=== RECOMMENDATION ALGORITHM ===")
    print(f"Processing {len(internships)} internships for user: {user.username}")
    print(f"User profile summary:")
    print(f"  Skills: {user.skills}")
    print(f"  Education: {user.education_level}")
    print(f"  Stream: {user.stream}")
    print(f"  Location: {user.location_preference}")
    print(f"=================================")
    
    for internship in internships:
        score = 0
        
        # Skill matching (40 points)
        if user.skills and internship.skills_required:
            try:
                user_skills = json.loads(user.skills) if user.skills else []
                required_skills = [skill.strip().lower() for skill in internship.skills_required.split(',')]
                user_skills_lower = [skill.strip().lower() for skill in user_skills]
                
                # Calculate skill overlap
                skill_matches = len(set(required_skills) & set(user_skills_lower))
                skill_score = (skill_matches / len(required_skills)) * 40 if required_skills else 0
                score += skill_score
                
                if skill_score > 0:
                    print(f"  {internship.title}: Skill match = {skill_matches}/{len(required_skills)} = {skill_score:.1f} points")
            except Exception as e:
                print(f"  Error processing skills for {internship.title}: {e}")
                pass
        
        # Education level matching (20 points)
        if user.education_level and internship.who_can_apply:
            education_keywords = {
                "bachelor's degree": ['bachelor', 'btech', 'bca', 'be', 'bsc', 'ba', 'bcom'],
                "master's degree": ['master', 'mba', 'ms', 'ma', 'mtech', 'mca'],
                'phd': ['phd', 'doctor', 'doctorate'],
                'diploma': ['diploma', 'certificate'],
                'high school': ['high school', '12th', 'intermediate']
            }
            
            user_edu_lower = user.education_level.lower()
            internship_text_lower = internship.who_can_apply.lower()
            
            if user_edu_lower in education_keywords:
                for keyword in education_keywords[user_edu_lower]:
                    if keyword in internship_text_lower:
                        score += 20
                        print(f"  {internship.title}: Education match = +20 points")
                        break
        
        # Stream matching (15 points)
        if user.stream and internship.who_can_apply:
            stream_keywords = {
                'computer science': ['computer science', 'cs', 'cse', 'computer engineering', 'software engineering', 'it'],
                'electronics': ['electronics', 'ece', 'electronic engineering', 'electrical'],
                'mechanical': ['mechanical', 'me', 'mechanical engineering'],
                'civil': ['civil', 'ce', 'civil engineering'],
                'business': ['business', 'management', 'mba', 'business administration'],
                'marketing': ['marketing', 'digital marketing', 'marketing management'],
                'finance': ['finance', 'financial', 'accounting', 'commerce'],
                'design': ['design', 'graphic design', 'ui/ux', 'visual design'],
                'data science': ['data science', 'data analytics', 'machine learning', 'ai'],
                'human resources': ['human resources', 'hr', 'personnel management']
            }
            
            user_stream_lower = user.stream.lower()
            internship_text_lower = internship.who_can_apply.lower()
            
            if user_stream_lower in stream_keywords:
                for keyword in stream_keywords[user_stream_lower]:
                    if keyword in internship_text_lower:
                        score += 15
                        print(f"  {internship.title}: Stream match = +15 points")
                        break
        
        # Location preference (15 points)
        if user.location_preference and internship.location:
            user_loc_lower = user.location_preference.lower()
            internship_loc_lower = internship.location.lower()
            
            if user_loc_lower in internship_loc_lower or internship_loc_lower == 'work from home':
                score += 15
                print(f"  {internship.title}: Location match = +15 points")
            elif 'work from home' in internship_loc_lower:
                score += 10
                print(f"  {internship.title}: Work from home = +10 points")
        
        # Duration preference (10 points)
        if internship.duration:
            duration_lower = internship.duration.lower()
            if '1 month' in duration_lower:
                score += 10
            elif '2 month' in duration_lower:
                score += 8
            elif '3 month' in duration_lower:
                score += 5
        
        # Add base score for all internships
        score += 5
        
        scored_internships.append((internship, score))
        
        if score > 5:  # Only print if score is above base score
            print(f"  {internship.title}: Total score = {score:.1f}")
    
    # Sort by score and return top results
    scored_internships.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Top {limit} recommendations:")
    for i, (internship, score) in enumerate(scored_internships[:limit]):
        print(f"  {i+1}. {internship.title} - Score: {score:.1f}")
    
    if not scored_internships:
        print("WARNING: No internships scored! Check if user profile has data.")
    
    print(f"=== END RECOMMENDATION ALGORITHM ===")
    
    return [item[0] for item in scored_internships[:limit]]

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
