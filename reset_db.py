import os
from app import db, User, brasilia_tz
from datetime import datetime

def reset_db():
    """Deleta o banco de dados existente e cria um novo com usuário master."""
    db.drop_all()
    db.create_all()

    # Cria apenas o usuário master
    master = User(
        username='admin',
        email='admin@sistema.com',
        password='admin',  # Em produção, usar hash
        role='admin',
        is_active=True,
        created_at=datetime.now(brasilia_tz),
        profile_image='https://ui-avatars.com/api/?name=Admin'
    )
    db.session.add(master)
    
    db.session.commit()
    print("Banco de dados resetado com sucesso! Usuário master criado.")

if __name__ == '__main__':
    # Cria o diretório instance se não existir
    if not os.path.exists('instance'):
        os.makedirs('instance')
        print("Diretório 'instance' criado")
    
    reset_db()
