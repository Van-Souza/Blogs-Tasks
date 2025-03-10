from app import app, db, User
from datetime import datetime
from pytz import timezone
import os

brasilia_tz = timezone('America/Sao_Paulo')

def init_database():
    print("Inicializando banco de dados...")
    
    # Criar diretório instance se não existir
    instance_path = os.path.join(os.getcwd(), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"✓ Diretório instance criado em: {instance_path}")
    
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✓ Tabelas criadas com sucesso")
            
            # Verificar se já existe algum usuário admin
            if not User.query.filter_by(username='admin').first():
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
                print("✓ Usuário admin criado com sucesso!")
            else:
                print("✓ Usuário admin já existe")
                
            print("\nInicialização concluída com sucesso!")
            
        except Exception as e:
            print(f"\nErro durante a inicialização: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    init_database() 