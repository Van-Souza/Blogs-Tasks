from app import app, db, User, socketio
from datetime import datetime
from pytz import timezone
import os

def init_app():
    # Cria a pasta instance se não existir
    if not os.path.exists('instance'):
        os.makedirs('instance')
        print("✓ Pasta instance criada")

    # Cria o banco de dados
    with app.app_context():
        db.create_all()
        print("✓ Banco de dados criado")

        # Cria usuário admin se não existir
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
            db.session.commit()
            print("✓ Usuário admin criado")
            print("\nCredenciais de acesso:")
            print("Login: admin")
            print("Senha: admin")

if __name__ == '__main__':
    print("Inicializando aplicação...")
    init_app()
    print("\nIniciando servidor...")
    socketio.run(app, debug=True) 