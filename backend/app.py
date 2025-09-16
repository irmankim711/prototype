from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
import pandas as pd
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stratosys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    group = db.Column(db.String(50))
    responses = db.Column(db.JSON)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(50))
    format = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')
    file_path = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create sample data if none exists
    if User.query.count() == 0:
        admin_user = User(
            email='admin@stratosys.com',
            full_name='Administrator',
            role='admin'
        )
        db.session.add(admin_user)
        
        # Add sample submissions
        sample_submissions = [
            Submission(name='Alice Johnson', email='alice@email.com', score=94, group='Group A'),
            Submission(name='Bob Smith', email='bob@email.com', score=85, group='Group B'),
            Submission(name='Charlie Brown', email='charlie@email.com', score=78, group='Group A'),
            Submission(name='Diana Ross', email='diana@email.com', score=92, group='Group B'),
            Submission(name='Eve Williams', email='eve@email.com', score=88, group='Group C'),
        ]
        
        for submission in sample_submissions:
            db.session.add(submission)
            
        db.session.commit()

@app.route('/fetch-data', methods=['GET'])
def fetch_data():
    try:
        submissions = Submission.query.all()
        data = []
        for sub in submissions:
            data.append({
                'name': sub.name,
                'email': sub.email,
                'score': sub.score,
                'date': sub.date.strftime('%Y-%m-%d'),
                'group': sub.group
            })
        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    try:
        submissions = Submission.query.all()
        data = []
        for sub in submissions:
            data.append({
                'id': sub.id,
                'name': sub.name,
                'email': sub.email,
                'score': sub.score,
                'date': sub.date.strftime('%Y-%m-%d'),
                'group': sub.group
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submissions', methods=['POST'])
def create_submission():
    try:
        data = request.get_json()
        submission = Submission(
            name=data['name'],
            email=data['email'],
            score=data.get('score', 0),
            group=data.get('group', 'Default')
        )
        db.session.add(submission)
        db.session.commit()
        return jsonify({'message': 'Submission created successfully', 'id': submission.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        reports = Report.query.all()
        data = []
        for report in reports:
            data.append({
                'id': report.id,
                'title': report.title,
                'type': report.report_type,
                'format': report.format,
                'created_at': report.created_at.strftime('%Y-%m-%d'),
                'status': report.status
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        report_type = data.get('report_type', 'summary')
        report_format = data.get('format', 'pdf')
        
        # Create report record
        report = Report(
            title=f"{report_type.title()} Report",
            report_type=report_type,
            format=report_format,
            user_id=1  # Default admin user
        )
        db.session.add(report)
        db.session.commit()
        
        # Generate actual report file
        if report_format == 'excel':
            submissions = Submission.query.all()
            df_data = []
            for sub in submissions:
                df_data.append({
                    'Name': sub.name,
                    'Email': sub.email,
                    'Score': sub.score,
                    'Date': sub.date.strftime('%Y-%m-%d'),
                    'Group': sub.group
                })
            df = pd.DataFrame(df_data)
            output_path = f'reports/report_{report.id}.xlsx'
            os.makedirs('reports', exist_ok=True)
            df.to_excel(output_path, index=False)
            report.file_path = output_path
            db.session.commit()
            
            return jsonify({
                'message': 'Report generated successfully',
                'report_id': report.id,
                'download_url': f'/download-report/{report.id}'
            })
        
        return jsonify({'message': 'Report generation started', 'report_id': report.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-report/<int:report_id>')
def download_report(report_id):
    try:
        report = Report.query.get_or_404(report_id)
        if report.file_path and os.path.exists(report.file_path):
            return send_file(report.file_path, as_attachment=True)
        else:
            return jsonify({'error': 'Report file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Simple authentication (in production, use proper password hashing)
        if email == 'admin@stratosys.com' and password == 'password':
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(email=email, full_name='Administrator', role='admin')
                db.session.add(user)
                db.session.commit()
            
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                }
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        total_submissions = Submission.query.count()
        scores = [s.score for s in Submission.query.all() if s.score]
        avg_score = sum(scores) / len(scores) if scores else 0
        top_score = max(scores) if scores else 0
        
        # Calculate median
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        median_score = sorted_scores[n//2] if n % 2 == 1 else (sorted_scores[n//2-1] + sorted_scores[n//2]) / 2 if n > 0 else 0
        
        return jsonify({
            'totalSubmissions': total_submissions,
            'averageScore': round(avg_score, 2),
            'activeUsers': total_submissions,  # Simplified
            'topScore': top_score,
            'medianScore': round(median_score, 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    # Return current settings
    return jsonify({
        'companyName': 'StratoSys Report',
        'timezone': 'UTC+8',
        'emailNotifications': True,
        'language': 'English'
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        data = request.get_json()
        # In a real app, save to database
        return jsonify({'message': 'Settings updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
