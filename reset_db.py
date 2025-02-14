import os
from app import app, db
from app.models import User  # Certifique-se de importar o modelo User corretamente

def reset_database():
    # Caminho para o arquivo do banco de dados
    db_path = os.path.join(app.instance_path, 'tasks.db')
    
    # Verifica se o arquivo do banco de dados existe
    if os.path.exists(db_path):
        print(f"Banco de dados encontrado em: {db_path}")
        print("Apagando banco de dados existente...")
        os.remove(db_path)  # Remove o arquivo do banco de dados
        print("Banco de dados apagado com sucesso!")
    else:
        print("Nenhum banco de dados encontrado para apagar.")

    # Cria uma nova instância do banco de dados
    print("Criando novo banco de dados...")
    with app.app_context():
        db.create_all()  # Cria todas as tabelas definidas nos modelos
        print("Banco de dados criado com sucesso!")

        # Adiciona dados iniciais
        print("Adicionando dados iniciais...")
        if not User.query.filter_by(username='Vandeilson').first():
            admin = User(username='Vandeilson', password='admin123', role='admin')
            db.session.add(admin)
        
        if not User.query.filter_by(username='Joao').first():
            reviewer_joao = User(username='Joao', password='reviewer123', role='reviewer')
            db.session.add(reviewer_joao)

        if not User.query.filter_by(username='Flavia').first():
            reviewer_flavia = User(username='Flavia', password='reviewer123', role='reviewer')
            db.session.add(reviewer_flavia)

        db.session.commit()
        print("Dados iniciais adicionados com sucesso!")

if __name__ == '__main__':
    reset_database()
