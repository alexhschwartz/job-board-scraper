from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobscraperapp.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    sources = db.relationship('Source', backref='user', lazy=True)
    resume_path = db.Column(db.String(255))
    resume_text = db.Column(db.Text)
    resume_skills = db.Column(db.Text)  # JSON string of skills

class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_scraped = db.Column(db.DateTime)
    
class JobListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100))
    title = db.Column(db.String(100))
    location = db.Column(db.String(100))
    date_posted = db.Column(db.DateTime)
    salary = db.Column(db.String(100))
    source = db.Column(db.String(100))
    link = db.Column(db.String(255))
    description = db.Column(db.Text)
    qualification_score = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    # For demo purposes, using a fixed user ID
    user_id = 1
    user = User.query.get_or_404(user_id)
    jobs = JobListing.query.filter_by(user_id=user_id).order_by(JobListing.qualification_score.desc()).all()
    return render_template('index.html', jobs=jobs, user=user)

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    # For demo purposes, using a fixed user ID
    user_id = 1
    user = User.query.get_or_404(user_id)
    
    if 'resume' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['resume']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Update user's resume info - simplified for demo
        user.resume_path = file_path
        user.resume_text = "Sample resume text"
        user.resume_skills = json.dumps(["python", "javascript", "html", "css"])
        db.session.commit()
        
        flash('Resume uploaded successfully!')
        return redirect(url_for('index'))
    
    flash('Invalid file type')
    return redirect(url_for('index'))

@app.route('/add_source', methods=['POST'])
def add_source():
    # For demo purposes, using a fixed user ID
    user_id = 1
    
    url = request.form.get('url')
    name = request.form.get('name')
    
    if not url:
        flash('URL is required')
        return redirect(url_for('index'))
    
    new_source = Source(url=url, name=name, user_id=user_id)
    db.session.add(new_source)
    db.session.commit()
    
    flash(f'Source "{name}" added successfully!')
    return redirect(url_for('index'))

@app.route('/view_job/<int:job_id>')
def view_job(job_id):
    job = JobListing.query.get_or_404(job_id)
    return render_template('job_details.html', job=job)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default user if not exists
        if not User.query.filter_by(username='demo').first():
            default_user = User(username='demo', email='demo@example.com')
            db.session.add(default_user)
            db.session.commit()
    app.run(debug=True)
