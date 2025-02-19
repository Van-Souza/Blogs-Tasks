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
5. Crie um arquivo `.env` com as variáveis de ambiente necessárias
6. Inicialize o banco de dados:
   ```bash
   python init_db.py
   ``` 