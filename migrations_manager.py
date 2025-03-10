from app import app, db, User
from flask_migrate import upgrade, init, migrate, stamp
from datetime import datetime
from pytz import timezone
import os

def init_migrations():
    """Inicializa as migrações se não existirem"""
    if not os.path.exists('migrations'):
        init()
        stamp()

def create_admin():
    """Cria o usuário admin se não existir"""
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@sistema.com',
                password='admin',
                role='admin',
                is_active=True,
                created_at=datetime.now(timezone('America/Sao_Paulo')),
                profile_image='https://ui-avatars.com/api/?name=Admin'
            )
            db.session.add(admin)
            try:
                db.session.commit()
                print("✓ Usuário admin criado com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao criar usuário admin: {e}")

def setup_database():
    """Configura o banco de dados com migrações e usuário admin"""
    with app.app_context():
        # Inicializa migrações se necessário
        init_migrations()
        
        # Aplica as migrações
        upgrade()
        
        # Cria usuário admin
        create_admin()

if __name__ == '__main__':
    setup_database() 