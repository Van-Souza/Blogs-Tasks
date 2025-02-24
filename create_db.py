from app import app, db, User
from datetime import datetime
from pytz import timezone

brasilia_tz = timezone('America/Sao_Paulo')

with app.app_context():
    # Cria todas as tabelas
    db.create_all()
    
    # Verifica se já existe algum usuário
    if User.query.first() is None:
        # Cria o usuário admin
        admin = User(
            username='admin',
            email='admin@sistema.com',
            password='admin',
            role='admin',
            is_active=True,
            created_at=datetime.now(brasilia_tz),
            profile_image='https://ui-avatars.com/api/?name=Admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado com sucesso!")
    else:
        print("Banco de dados já inicializado.") 