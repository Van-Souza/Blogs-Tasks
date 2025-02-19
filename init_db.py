from app import db, create_app

def init_db():
    app = create_app()
    with app.app_context():
        db.drop_all()  # Cuidado! Isso apaga todos os dados
        db.create_all()
        # Adicione dados iniciais se necessário
        # exemplo: db.session.add(User(...))
        db.session.commit()

if __name__ == '__main__':
    init_db() 