import os
from app import db, User

def reset_database():
    # Caminho do banco de dados
    db_path = 'instance/tasks.db'
    
    # Remove o banco existente se houver
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Banco de dados antigo removido: {db_path}")

    # Cria as tabelas
    db.create_all()
    print("Novas tabelas criadas")

    # Adiciona os usuários iniciais
    admin = User(
        username='Vandeilson',
        email='admin@example.com',
        password='Van9090@',
        role='admin',
        profile_image='https://ui-avatars.com/api/?name=Vandeilson'
    )
    db.session.add(admin)
    
    joao = User(
        username='Joao',
        email='joao@example.com',
        password='123',
        role='reviewer',
        profile_image='https://ui-avatars.com/api/?name=Joao'
    )
    db.session.add(joao)
    
    flavia = User(
        username='Flavia',
        email='flavia@example.com',
        password='123',
        role='reviewer',
        profile_image='https://ui-avatars.com/api/?name=Flavia'
    )
    db.session.add(flavia)
    
    try:
        db.session.commit()
        print("Usuários padrão criados com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar usuários: {str(e)}")

if __name__ == '__main__':
    # Cria o diretório instance se não existir
    if not os.path.exists('instance'):
        os.makedirs('instance')
        print("Diretório 'instance' criado")
    
    reset_database()
