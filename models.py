from datetime import datetime
from pytz import timezone
from app import db

brasilia_tz = timezone('America/Sao_Paulo')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='reviewer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(brasilia_tz))
    last_login = db.Column(db.DateTime)
    profile_image = db.Column(db.String(200))
    tasks = db.relationship('Task', backref='assignee', lazy=True)
    comments = db.relationship('TaskComment', backref='user', lazy=True)

class TaskComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(brasilia_tz))
    is_system_message = db.Column(db.Boolean, default=False)

class ChatView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_viewed_at = db.Column(db.DateTime, default=lambda: datetime.now(brasilia_tz))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_WAITING_APPROVAL = 'waiting_approval'
    STATUS_COMPLETED = 'completed'
    
    status = db.Column(db.String(20), default='pending')
    completion_date = db.Column(db.DateTime)
    priority = db.Column(db.Integer, default=3)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(brasilia_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(brasilia_tz), onupdate=lambda: datetime.now(brasilia_tz))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    comments = db.relationship('TaskComment', backref='task', lazy=True, order_by='TaskComment.created_at')
    chat_views = db.relationship('ChatView', backref='task', lazy=True)

    def has_new_messages(self, user_id):
        last_view = ChatView.query.filter_by(task_id=self.id, user_id=user_id).first()
        if not last_view:
            return bool(self.comments)
        
        return bool(TaskComment.query.filter(
            TaskComment.task_id == self.id,
            TaskComment.created_at > last_view.last_viewed_at,
            TaskComment.user_id != user_id
        ).first()) 