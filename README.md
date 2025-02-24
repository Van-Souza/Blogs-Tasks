# Sistema de Gerenciamento de Tarefas

## Configuração Inicial

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
5. Crie um arquivo `.env` com as variáveis de ambiente:
   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   ```

## Comandos do Banco de Dados

### Inicialização
```bash
# Criar banco novo com usuário master (admin/admin)
flask init-db

# OU resetar banco (apaga tudo e recria)
flask reset-db
```

### Migrations
```bash
# Inicializar sistema de migrations
flask db init

# Criar nova migration
flask db migrate -m "Descrição da alteração"

# Aplicar migrations pendentes
flask db upgrade

# Reverter última migration
flask db downgrade
```

### Backup e Restauração
```bash
# Backup (Windows)
copy instance\tasks.db instance\tasks.db.backup

# Backup (Linux/Mac)
cp instance/tasks.db instance/tasks.db.backup

# Restaurar (Windows)
copy instance\tasks.db.backup instance\tasks.db

# Restaurar (Linux/Mac)
cp instance/tasks.db.backup instance/tasks.db
```

### Usuário Master Padrão
- Username: admin
- Password: admin
- Email: admin@sistema.com

## Executando o Sistema
```bash
flask run
``` 