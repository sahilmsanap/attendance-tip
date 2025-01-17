# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages and sessions
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db = SQLAlchemy(app)

# Database Models
class Professor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    division = db.Column(db.String(1), nullable=False)  # 'A' or 'B'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Boolean, nullable=False)  # True for present, False for absent

# Create the database and tables
with app.app_context():
    db.create_all()
    # Add a default professor if none exists
    if not Professor.query.filter_by(username='prof1').first():
        default_prof = Professor(username='prof1', password='password123')
        db.session.add(default_prof)
        db.session.commit()

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        professor = Professor.query.filter_by(username=username, password=password).first()
        if professor:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/mark_attendance/<division>')
def mark_attendance(division):
    if 'username' not in session:
        return redirect(url_for('login'))
    students = Student.query.filter_by(division=division).all()
    return render_template('mark_attendance.html', students=students, division=division)

@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    for key, value in request.form.items():
        if key.startswith('student_'):
            student_id = int(key.split('_')[1])
            status = value == 'present'
            
            # Check if attendance already exists for this student on this date
            attendance = Attendance.query.filter_by(student_id=student_id, date=date).first()
            if attendance:
                attendance.status = status
            else:
                attendance = Attendance(student_id=student_id, date=date, status=status)
                db.session.add(attendance)
    
    db.session.commit()
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/manage_students')
def manage_students():
    if 'username' not in session:
        return redirect(url_for('login'))
    students = Student.query.all()
    return render_template('manage_students.html', students=students)

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    name = request.form['name']
    division = request.form['division']
    student = Student(name=name, division=division)
    db.session.add(student)
    db.session.commit()
    flash('Student added successfully!', 'success')
    return redirect(url_for('manage_students'))

@app.route('/delete_student/<int:id>')
def delete_student(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully!', 'success')
    return redirect(url_for('manage_students'))

@app.route('/view_attendance')
def view_attendance():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    students = Student.query.all()
    current_month = datetime.now().month
    attendance_data = []
    
    for student in students:
        monthly_attendance = Attendance.query.filter(
            Attendance.student_id == student.id,
            db.extract('month', Attendance.date) == current_month
        ).all()
        
        present_days = sum(1 for a in monthly_attendance if a.status)
        absent_days = sum(1 for a in monthly_attendance if not a.status)
        
        attendance_data.append({
            'name': student.name,
            'division': student.division,
            'present_days': present_days,
            'absent_days': absent_days
        })
    
    return render_template('view_attendance.html', attendance_data=attendance_data)

if __name__ == '__main__':
    app.run(debug=True)