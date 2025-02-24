from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone
from sqlalchemy import case  # Importação adicionada
brasilia_tz = timezone('America/Sao_Paulo')
import requests
import os
from functools import wraps
from pytz import timezone
from datetime import datetime
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from flask_socketio import SocketIO, emit, join_room, leave_room

brasilia_tz = timezone('America/Sao_Paulo')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SYNC_URLS'] = [
    'https://meuatendimentovirtual.com.br/wp-json/wp/v2/docs?doc_category=35&per_page=100',
    'https://meuatendimentovirtual.com.br/wp-json/wp/v2/docs?doc_category=51&per_page=100',
    'https://meuatendimentovirtual.com.br/wp-json/wp/v2/docs?doc_category=50&per_page=100',
    'https://meuatendimentovirtual.com.br/wp-json/wp/v2/docs?doc_category=45&per_page=100',
    'https://meuatendimentovirtual.com.br/wp-json/wp/v2/docs?doc_category=46&per_page=100',
    'https://blog.eagenda.com.br/wp-json/wp/v2/docs?doc_category=27&per_page=100',
    'https://blog.eagenda.com.br/wp-json/wp/v2/docs?doc_category=4&per_page=100',
    'https://blog.eagenda.com.br/wp-json/wp/v2/docs?doc_category=9&per_page=100',
    'https://blog.eagenda.com.br/wp-json/wp/v2/docs?doc_category=28&per_page=100',
    'https://blog.eagenda.com.br/wp-json/wp/v2/docs?doc_category=29&per_page=100',
    'https://blog.eagenda.com.br/wp-json/wp/v2/docs?doc_category=32&per_page=100',
    'https://blog.eagenda.com.br/wp-json/wp/v2/docs?doc_category=30&per_page=100',
]
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Inicializar Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Models
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
    completion_date = db.Column(db.DateTime)  # Data quando foi marcada como concluída
    auto_pending_days = db.Column(db.Integer, default=30)  # Dias até voltar para pendente
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
        view = ChatView.query.filter_by(task_id=self.id, user_id=user_id).first()
        
        # Se não houver comentários, não há novas mensagens
        if not self.comments:
            return False
            
        # Se não houver visualização
        if not view:
            # Retorna True se houver comentários que não são do usuário atual
            return any(comment.user_id != user_id for comment in self.comments)
        
        # Verifica se há comentários mais recentes que a última visualização
        # que não são do usuário atual
        latest_comment = max(
            (c for c in self.comments if c.user_id != user_id), 
            key=lambda x: x.created_at,
            default=None
        )
        
        return latest_comment and latest_comment.created_at > view.last_viewed_at

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Task.query.filter_by(is_active=True)
    
    # Aplicar filtros
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority', type=int)
    search = request.args.get('search', '').strip()
    user_filter = request.args.get('user', type=int)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))
    if user_filter:
        query = query.filter_by(assigned_to=user_filter)
    
    # Se o usuário não for admin, filtrar apenas suas tarefas
    if session.get('role') != 'admin':
        query = query.filter_by(assigned_to=session['user_id'])
    
    # Ordenação personalizada
    query = query.order_by(
        case(
            (Task.assigned_to == session['user_id'], 0),
            else_=1
        ),
        Task.status == 'completed',
        Task.priority.asc(),
        Task.deadline.asc()
    )
    
    # Paginar as tarefas
    tasks = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Obter lista de usuários ativos para o filtro
    users = User.query.filter_by(is_active=True).all()
    
    # Garantir que a data atual tenha fuso horário
    current_time = datetime.now(brasilia_tz)
    
    # Converter os deadlines para terem fuso horário
    for task in tasks.items:
        if task.deadline:
            # Se o deadline não tiver fuso horário, adiciona
            if task.deadline.tzinfo is None:
                task.deadline = brasilia_tz.localize(task.deadline)
    
    return render_template('index.html', 
                         tasks=tasks,
                         users=users,
                         Task=Task,
                         status_filter=status_filter,
                         priority_filter=priority_filter,
                         user_filter=user_filter,
                         search=search,
                         now=current_time)

# Restante do código...

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        
        flash('Credenciais inválidas', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/task/update/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.json

    if 'assigned_to' in data:
        old_assigned = task.assigned_to
        task.assigned_to = data['assigned_to'] or None
        
        # Se atribuir a alguém, muda para "em andamento"
        if task.assigned_to and not old_assigned:
            task.status = Task.STATUS_IN_PROGRESS
        # Se desatribuir, volta para "pendente"
        elif not task.assigned_to and old_assigned:
            task.status = Task.STATUS_PENDING

    if 'status' in data:
        # Apenas admin pode aprovar tarefas
        if data['status'] == Task.STATUS_COMPLETED and session['role'] != 'admin':
            return jsonify({'success': False, 'message': 'Apenas administradores podem aprovar tarefas'})
        
        # Usuário só pode solicitar aprovação
        if session['role'] != 'admin' and data['status'] == Task.STATUS_COMPLETED:
            task.status = Task.STATUS_WAITING_APPROVAL
        else:
            task.status = data['status']
            
            # Se aprovada, registra a data e remove o usuário
            if data['status'] == Task.STATUS_COMPLETED:
                task.completion_date = datetime.now(brasilia_tz)
                task.assigned_to = None

    if 'priority' in data and session['role'] == 'admin':
        task.priority = data['priority']
    
    if 'deadline' in data and session['role'] == 'admin':
        if data['deadline']:
            try:
                task.deadline = datetime.fromisoformat(data['deadline'])
            except ValueError:
                return jsonify({'success': False, 'message': 'Formato de data inválido'}), 400
        else:
            task.deadline = None
    
    if 'message' in data and data['message'].strip():
        new_comment = TaskComment(
            task_id=task.id,
            user_id=session['user_id'],
            message=data['message'].strip()
        )
        db.session.add(new_comment)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/task/<int:task_id>/chat')
@login_required
def task_chat(task_id):
    task = Task.query.get_or_404(task_id)
    comments = TaskComment.query.filter_by(task_id=task.id).order_by(TaskComment.created_at.asc()).all()
    return render_template('chat.html', task=task, comments=comments)

@app.route('/task/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        try:
            # Capturar dados do formulário
            title = request.form.get('title', '').strip()
            url = request.form.get('url', '').strip()
            priority = int(request.form.get('priority', 3))
            deadline_str = request.form.get('deadline', '')
            comments = request.form.get('comments', '').strip()

            # Validação básica
            if not title:
                flash('Título é obrigatório', 'danger')
                return redirect(url_for('create_task'))
            
            if url and not url.startswith(('http://', 'https://')):
                flash('URL inválida (deve começar com http:// ou https://)', 'danger')
                return redirect(url_for('create_task'))

            # Converter dados
            deadline = datetime.fromisoformat(deadline_str) if deadline_str else None
            
            # Definir responsável
            if session['role'] == 'admin':
                assigned_to = int(request.form.get('assigned_to', session['user_id']))
            else:
                assigned_to = session['user_id']

            # Criar nova tarefa
            new_task = Task(
                title=title,
                url=url if url else None,
                priority=priority,
                deadline=deadline,
                assigned_to=assigned_to
            )

            # Adicionar comentário inicial se existir
            if comments:
                new_comment = TaskComment(
                    message=comments,
                    user_id=session['user_id'],
                    task=new_task  # Usando o relacionamento
                )
                db.session.add(new_comment)

            db.session.add(new_task)
            db.session.commit()
            
            flash('Tarefa criada com sucesso!', 'success')
            return redirect(url_for('index'))

        except ValueError as e:
            db.session.rollback()
            flash(f'Erro de formato: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar tarefa: {str(e)}', 'danger')
        
        return redirect(url_for('create_task'))

    # GET: Mostrar formulário
    users = User.query.all() if session.get('role') == 'admin' else []
    return render_template('create_task.html', users=users)

@app.route('/sync', methods=['POST'])
@login_required
def sync_tasks():
    if session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    
    total_synced = 0
    errors = []

    for api_url in app.config['SYNC_URLS']:
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            external_tasks = response.json()
            
            if isinstance(external_tasks, dict):
                external_tasks = external_tasks.get('items', [])

            synced = 0
            for task_data in external_tasks:
                try:
                    task_id = task_data.get('id')
                    
                    title = task_data.get('title')
                    if isinstance(title, dict):
                        title = title.get('rendered', 'Sem título')
                    elif not title:
                        title = 'Sem título'
                    
                    # Extrair URL
                    url = task_data.get('url') or task_data.get('link', '#')

                    # Ignorar itens sem ID ou título
                    if not task_id or not title:
                        continue

                    # Verificar se a tarefa já existe
                    if not Task.query.get(task_id):
                        new_task = Task(
                            id=task_id,
                            title=title,
                            url=url,
                            status='pending'
                        )
                        db.session.add(new_task)
                        synced += 1
                        
                except Exception as e:
                    errors.append(f"Erro no item {task_id} da {api_url}: {str(e)}")
                    db.session.rollback()  # Rollback para evitar problemas de transação
                    continue

            db.session.commit()
        except requests.exceptions.RequestException as e:
            errors.append(f"Falha na conexão com {api_url}: {str(e)}")
        except ValueError as e:
            errors.append(f"Resposta inválida de {api_url}: {str(e)}")
        except Exception as e:
            errors.append(f"Erro geral em {api_url}: {str(e)}")
            db.session.rollback()

    if errors:
        flash(f"Alguns erros ocorreram: {' | '.join(errors[:3])}", 'danger')
    if total_synced:
        flash(f"Total de tarefas sincronizadas: {total_synced}", 'info')
    else:
        flash("Nenhuma nova tarefa encontrada nas APIs", 'warning')

    return redirect(url_for('index'))

@app.route('/task/comments/<int:task_id>', methods=['GET'])
@login_required
def get_task_comments(task_id):
    task = Task.query.get_or_404(task_id)
    comments = [
        {
            'id': comment.id,
            'user': comment.user.username,
            'message': comment.message,
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
        }
        for comment in task.comments
    ]
    return jsonify(comments)

@app.route('/reports')
@login_required
def reports():
    if session.get('role') != 'admin':
        flash('Acesso negado. Somente administradores podem acessar relatórios.', 'danger')
        return redirect(url_for('index'))

    # Consultas para os relatórios
    tasks_by_status = db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
    tasks_by_user = db.session.query(User.username, db.func.count(Task.id)).join(Task, Task.assigned_to == User.id, isouter=True).group_by(User.username).all()
    tasks_by_priority = db.session.query(Task.priority, db.func.count(Task.id)).group_by(Task.priority).all()
    overdue_tasks = Task.query.filter(Task.deadline < datetime.now()).count()

    return render_template('reports.html', 
                         tasks_by_status=tasks_by_status,
                         tasks_by_user=tasks_by_user,
                         tasks_by_priority=tasks_by_priority,
                         overdue_tasks=overdue_tasks)

@app.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    if session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    
    task = Task.query.get_or_404(task_id)
    
    # Apenas desativa a tarefa ao invés de deletar
    task.is_active = False
    task.updated_at = datetime.now(brasilia_tz)
    db.session.commit()
    
    return jsonify({'success': True})

# Novas rotas para gerenciamento de usuários
@app.route('/members')
@login_required
def members():
    if session.get('role') != 'admin':
        flash('Acesso negado. Somente administradores podem acessar.', 'danger')
        return redirect(url_for('index'))
    
    # Busca todos os usuários, incluindo inativos
    users = User.query.all()
    return render_template('members.html', users=users)

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if session.get('role') != 'admin':
        flash('Acesso negado. Somente administradores podem registrar usuários.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            username = request.form.get('username').strip()
            email = request.form.get('email').strip()
            password = request.form.get('password')
            role = request.form.get('role')
            profile_image = request.form.get('profile_image')

            # Validações
            if User.query.filter_by(username=username).first():
                flash('Nome de usuário já existe.', 'danger')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('Email já cadastrado.', 'danger')
                return redirect(url_for('register'))

            new_user = User(
                username=username,
                email=email,
                password=password,  # Em produção, usar hash da senha
                role=role,
                profile_image=profile_image
            )

            db.session.add(new_user)
            db.session.commit()

            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('members'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/user/update/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    try:
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'profile_image' in data:
            user.profile_image = data['profile_image']

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    user = User.query.get_or_404(user_id)
    
    # Verifica se o usuário tem tarefas associadas
    active_tasks = Task.query.filter_by(assigned_to=user.id, is_active=True).first()
    if active_tasks:
        return jsonify({
            'success': False, 
            'message': 'Não é possível desativar um usuário com tarefas ativas associadas'
        }), 400

    # Desativa o usuário ao invés de deletar
    user.is_active = False
    db.session.commit()
    return jsonify({'success': True})

@app.route('/user/reactivate/<int:user_id>', methods=['POST'])
@login_required
def reactivate_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403

    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    return jsonify({'success': True})

# Nova rota para tarefas arquivadas
@app.route('/archived_tasks')
@login_required
def archived_tasks():
    if session.get('role') != 'admin':
        flash('Acesso negado. Somente administradores podem acessar tarefas arquivadas.', 'danger')
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Task.query.filter_by(is_active=False)
    
    # Aplicar filtros
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority', type=int)
    search = request.args.get('search', '').strip()
    user_filter = request.args.get('user', type=int)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))
    if user_filter:
        query = query.filter_by(assigned_to=user_filter)
    
    tasks = query.order_by(Task.updated_at.desc()).paginate(page=page, per_page=per_page)
    users = User.query.filter_by(is_active=True).all()
    
    return render_template('archived_tasks.html', 
                         tasks=tasks,
                         users=users,
                         status_filter=status_filter,
                         priority_filter=priority_filter,
                         user_filter=user_filter,
                         search=search)

# Rota para reativar tarefa
@app.route('/task/reactivate/<int:task_id>', methods=['POST'])
@login_required
def reactivate_task(task_id):
    if session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Não autorizado'}), 403
    
    task = Task.query.get_or_404(task_id)
    task.is_active = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/task/mark_chat_read/<int:task_id>', methods=['POST'])
@login_required
def mark_chat_read(task_id):
    task = Task.query.get_or_404(task_id)
    
    view = ChatView.query.filter_by(task_id=task_id, user_id=session['user_id']).first()
    if view:
        view.last_viewed_at = datetime.now(brasilia_tz)
    else:
        view = ChatView(task_id=task_id, user_id=session['user_id'])
        db.session.add(view)
    
    db.session.commit()
    
    # Verifica se ainda há mensagens não lidas após marcar como lido
    return jsonify({
        'success': True,
        'hasNewMessages': task.has_new_messages(session['user_id'])
    })

@app.route('/task/comment/<int:task_id>', methods=['POST'])
@login_required
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    message = request.json.get('message')
    
    if not message:
        return jsonify({'success': False, 'message': 'Mensagem vazia'}), 400

    comment = TaskComment(
        task_id=task_id,
        user_id=session['user_id'],
        message=message
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Emitir evento de nova mensagem para a sala do chat
    socketio.emit('new_message', {
        'task_id': task_id,
        'user_id': session['user_id'],
        'username': session['username'],
        'message': message,
        'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
    }, room=f"task_{task_id}")
    
    # Emitir evento para todos os usuários (para atualizar a bolinha)
    socketio.emit('notification', {
        'task_id': task_id,
        'user_id': session['user_id']
    })
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'user': comment.user.username,
            'message': comment.message,
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
        }
    })

@app.route('/api/stats')
@login_required
def get_stats():
    query = Task.query.filter_by(is_active=True)
    
    # Se não for admin, filtrar apenas tarefas do usuário
    if session.get('role') != 'admin':
        query = query.filter_by(assigned_to=session['user_id'])
    
    # Contar total de cada status sem paginação
    total = query.count()
    completed = query.filter_by(status='completed').count()
    in_progress = query.filter_by(status='in_progress').count()
    waiting_approval = query.filter_by(status='waiting_approval').count()
    
    return jsonify({
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'waiting_approval': waiting_approval
    })

# Tarefa para verificar tarefas concluídas antigas
def check_completed_tasks():
    with app.app_context():
        tasks = Task.query.filter_by(
            status=Task.STATUS_COMPLETED,
            is_active=True
        ).all()
        
        now = datetime.now(brasilia_tz)
        for task in tasks:
            if task.completion_date:
                days_passed = (now - task.completion_date).days
                if days_passed >= task.auto_pending_days:
                    task.status = Task.STATUS_PENDING
                    task.completion_date = None
        
        db.session.commit()

# Agendar verificação diária
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_completed_tasks, trigger="interval", days=1)
scheduler.start()

# Initialize database
@app.cli.command('init-db')
def init_db_command():
    """Inicializa o banco de dados com usuário master."""
    db.create_all()
    
    # Verifica se já existe algum usuário
    if User.query.first() is None:
        master = User(
            username='admin',
            email='admin@sistema.com',
            password='admin',
            role='admin',
            is_active=True,
            created_at=datetime.now(brasilia_tz),
            profile_image='https://ui-avatars.com/api/?name=Admin'
        )
        db.session.add(master)
        db.session.commit()
        print("Usuário master criado com sucesso!")
    else:
        print("Banco de dados já inicializado.")

# Remover ou comentar o comando reset-db se não for necessário

# Adicionar eventos de Socket.IO
@socketio.on('join')
def on_join(data):
    room = f"task_{data['task_id']}"
    join_room(room)

@socketio.on('leave')
def on_leave(data):
    room = f"task_{data['task_id']}"
    leave_room(room)

@socketio.on('new_message')
def handle_message(data):
    room = f"task_{data['task_id']}"
    emit('message', data, room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)

