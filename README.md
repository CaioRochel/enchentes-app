# APS - Sistema Distribuído de Ocorrências de Alagamentos

Este projeto implementa uma aplicação distribuída para monitoramento de áreas de risco de alagamento.  
O sistema é composto por **backend em Flask (Python)** e **frontend em HTML/JS com Leaflet**.

---

## 1. Estrutura do projeto

```
/app.py            # backend Flask (API + autenticação + lógica)
/frontend/index.html   # página principal (mapa e registro de ocorrências)
/frontend/admin.html   # painel administrativo
/uploads/             # diretório de fotos enviadas
/database.sql         # script inicial do banco de dados
```

---

## 2. Requisitos

### Backend
- Python 3.9+
- Bibliotecas Python:
  ```bash
  pip install flask flask-cors mysql-connector-python werkzeug pyjwt requests
  ```
- Banco de dados MySQL rodando.

### Frontend
- Navegador moderno (Chrome, Edge, Firefox, Safari).
- A página `index.html` funciona em desktop e mobile (responsiva).

---

## 3. Configuração do Banco de Dados

1. Crie o banco `alagamentos` no MySQL:
   ```sql
   CREATE DATABASE alagamentos;
   ```

2. Importe a estrutura inicial:
   ```bash
   mysql -u root -p alagamentos < database.sql
   ```

3. Ajuste as credenciais no `app.py`:
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "user": "root",
       "password": "",   # coloque sua senha do MySQL
       "database": "alagamentos"
   }
   ```

---

## 4. Configuração da WeatherAPI

1. Crie uma conta em [WeatherAPI](https://www.weatherapi.com/).  
2. Copie sua chave gratuita.  
3. Edite o `app.py`:
   ```python
   WEATHER_API_KEY = "SUA_CHAVE_WEATHERAPI"
   ```

---

## 5. Rodando o Backend

Na raiz do projeto:

```bash
python app.py
```

- O backend estará disponível em:  
  `http://127.0.0.1:5000`

- Endpoints principais:
  - `POST /auth/register` → cadastrar usuário
  - `POST /auth/login` → login e token JWT
  - `GET /ocorrencias` → listar ocorrências
  - `POST /ocorrencias` → adicionar ocorrência
  - `GET /risco/<cidade>` → risco heurístico
  - `GET /clima/<cidade>` → clima atual

---

## 6. Rodando o Frontend

Entre na pasta `frontend` e inicie um servidor simples:

```bash
cd frontend
python -m http.server 5500
```

Acesse no navegador:

```
http://127.0.0.1:5500/index.html
```

---

## 7. Funcionalidades

- **Registro de usuários** (com senha criptografada).
- **Login com JWT** (guarda token no navegador).
- **Mapa interativo (Leaflet)** com:
  - Marcadores de ocorrências.
  - Heatmap de densidade.
  - Círculos vermelhos para áreas com ≥3 ocorrências próximas (~10km).
  - Popups com descrição, autor, foto, risco heurístico e clima atual.
- **Painel admin**:
  - Listar usuários e ocorrências.
  - Promover usuário para admin.
  - Editar ou excluir ocorrências.

---

## 8. Notas Finais

- Use navegador em **rede local** se quiser acessar pelo celular.  
  Exemplo: substitua `127.0.0.1` pelo IP da sua máquina (`ipconfig` no Windows).  
- As fotos são salvas no diretório `/uploads`.  
- Para produção, considere usar **Google Cloud Run** ou **Heroku** no backend.

---

## 9. Fluxo do Sistema

```
+-----------+        +-------------+        +-------------+
| Usuário   | <----> | Frontend    | <----> | API Flask   |
| (naveg.)  |        | (HTML/JS)   |        | (app.py)    |
+-----------+        +-------------+        +-------------+
                           |                         |
                           v                         v
                   +---------------+         +---------------+
                   | WeatherAPI    |         | Banco MySQL   |
                   | (clima/chuva) |         | ocorrências   |
                   +---------------+         +---------------+

---

Esse diagrama mostra:  
- O usuário interage com o frontend (index.html/admin.html).  
- O frontend consome dados da API Flask (app.py).  
- O backend consulta o MySQL para histórico e também a WeatherAPI para clima/previsão.  

---



