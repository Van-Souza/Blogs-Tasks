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

## Executando o Sistema

Execute o arquivo run.py:
```bash
python run.py
```

Este comando irá:
- Criar a pasta instance se não existir
- Criar o banco de dados
- Criar o usuário admin (se não existir)
- Iniciar o servidor Flask

## Acessando o Sistema

- URL: http://127.0.0.1:5000
- Login padrão:
  - Usuário: admin
  - Senha: admin

## Backup do Banco de Dados

### Backup
```bash
# Windows
copy instance\tasks.db instance\tasks.db.backup

# Linux/Mac
cp instance/tasks.db instance/tasks.db.backup
```

### Restauração
```bash
# Windows
copy instance\tasks.db.backup instance\tasks.db

# Linux/Mac
cp instance/tasks.db.backup instance/tasks.db
``` 