from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, uuid, requests, jwt
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mysql.connector

app = Flask(__name__,static_folder='frontend', template_folder='frontend')
CORS(app, resources={r"/*": {"origins": "*"}},
     allow_headers=["Authorization", "Content-Type"],
     expose_headers=["Authorization"],
     supports_credentials=False)

# diretórios
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
FRONT_DIR = os.path.join(os.path.dirname(__file__), "frontend")

# configuração banco de dados
DB_CONFIG = {
    'host': os.environ.get('MYSQLHOST', 'localhost'),
    'port': int(os.environ.get('MYSQLPORT', 3306)),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQLPASSWORD', ''),
    'database': os.environ.get('MYSQLDATABASE', 'railway')
}

# configuração JWT
JWT_SECRET = "76q+MdoheMmqREW2dR6bM0cXmnFqwJPTUkhp5Uw9COM="
JWT_EXPIRES_MIN = 60

# configuração WeatherAPI
WEATHER_API_KEY = "98e437454a414f88a7f13834252408"

# ------------------ helpers ------------------

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def create_token(user: dict) -> str:
    payload = {
        "sub": str(user["id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=JWT_EXPIRES_MIN)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

def current_user():
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    try:
        return decode_token(token)
    except Exception:
        return None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"erro": "não autorizado"}), 401
        request.user = user
        return f(*args, **kwargs)
    return wrapper

def admin_or_owner_required(get_owner_id):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"erro": "não autorizado"}), 401
            owner_id = get_owner_id(**kwargs)
            if user["role"] == "admin" or int(user["sub"]) == int(owner_id):
                request.user = user
                return f(*args, **kwargs)
            return jsonify({"erro": "proibido"}), 403
        return wrapper
    return decorator

# ------------------ auth ------------------

@app.post("/auth/register")
def register():
    data = request.get_json()
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all([name, email, password]):
        return jsonify({"erro": "dados inválidos"}), 400
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close(); conn.close()
        return jsonify({"erro": "email já cadastrado"}), 400
    hashed = generate_password_hash(password)
    cur.execute("INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,%s)",
                (name, email, hashed, "user"))
    conn.commit()
    uid = cur.lastrowid
    cur.execute("SELECT id,name,email,role FROM users WHERE id=%s", (uid,))
    user = cur.fetchone()
    cur.close(); conn.close()
    token = create_token(user)
    return jsonify({"token": token, "user": user})

@app.post("/auth/login")
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id,name,email,role,password_hash FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close(); conn.close()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"erro": "credenciais inválidas"}), 401
    token = create_token(user)
    return jsonify({"token": token, "user": {k: user[k] for k in ("id","name","email","role")}})

# ------------------ users ------------------

@app.get("/users")
@login_required
def list_users():
    if request.user["role"] != "admin":
        return jsonify({"erro": "apenas admin pode listar usuários"}), 403
    conn=get_db(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT id,name,email,role,created_at FROM users ORDER BY id")
    users=cur.fetchall()
    cur.close(); conn.close()
    return jsonify(users)

@app.put("/users/<int:uid>/promote")
@login_required
def promote_user(uid):
    if request.user["role"] != "admin":
        return jsonify({"erro": "apenas admin pode promover"}), 403
    conn=get_db(); cur=conn.cursor()
    cur.execute("UPDATE users SET role='admin' WHERE id=%s", (uid,))
    conn.commit(); updated=cur.rowcount
    cur.close(); conn.close()
    if not updated:
        return jsonify({"erro": "usuário não encontrado"}), 404
    return jsonify({"mensagem": "usuário promovido a admin"})

@app.delete("/users/<int:uid>")
@login_required
def delete_user(uid):
    if request.user["role"] != "admin":
        return jsonify({"erro": "apenas admin pode excluir"}), 403
    conn=get_db(); cur=conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (uid,))
    conn.commit(); deleted=cur.rowcount
    cur.close(); conn.close()
    if not deleted:
        return jsonify({"erro": "usuário não encontrado"}), 404
    return jsonify({"mensagem": "usuário excluído"})

# ------------------ ocorrencias ------------------

@app.get("/ocorrencias")
def list_ocorrencias():
    conn=get_db(); cur=conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.id,o.descricao,o.latitude,o.longitude,o.cidade,o.data_ocorrencia,o.foto_url,
               u.id as autor_id,u.name as autor_name,u.email as autor_email,u.role as autor_role
        FROM ocorrencias o
        LEFT JOIN users u ON o.user_id=u.id
        ORDER BY o.data_ocorrencia DESC
    """)
    ocorrencias=cur.fetchall()
    cur.close(); conn.close()
    result=[]
    for o in ocorrencias:
        result.append({
            "id": o["id"],
            "descricao": o["descricao"],
            "localizacao": {
                "latitude": o["latitude"],
                "longitude": o["longitude"],
                "cidade": o["cidade"]
            },
            "data_ocorrencia": o["data_ocorrencia"],
            # aqui garantimos que retorna URL completa
            "foto_url": f"http://{request.host}/uploads/{o['foto_url']}" if o["foto_url"] else None,
            "autor": {
                "id": o["autor_id"],
                "name": o["autor_name"],
                "email": o["autor_email"],
                "role": o["autor_role"]
            }
        })
    return jsonify(result)

@app.post("/ocorrencias")
@login_required
def add_ocorrencia():
    descricao = request.form.get("descricao")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    cidade = request.form.get("cidade")
    if not descricao or not latitude or not longitude:
        return jsonify({"erro": "dados incompletos"}), 400

    foto_file = request.files.get("foto")
    foto_filename = None
    if foto_file:
        foto_filename = secure_filename(f"{uuid.uuid4().hex}_{foto_file.filename}")
        foto_file.save(os.path.join(UPLOAD_DIR, foto_filename))

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO ocorrencias (descricao, latitude, longitude, cidade, user_id, foto_url, data_ocorrencia)
           VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
        (descricao, latitude, longitude, cidade, request.user["sub"], foto_filename),
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensagem": "ocorrência registrada", "cidade": cidade}), 201


@app.put("/ocorrencias/<int:oid>")
@login_required
@admin_or_owner_required(lambda oid: get_owner_id("ocorrencias", oid))
def update_ocorrencia(oid):
    data=request.get_json()
    descricao,cidade=data.get("descricao"),data.get("cidade")
    conn=get_db(); cur=conn.cursor()
    cur.execute("UPDATE ocorrencias SET descricao=%s,cidade=%s WHERE id=%s",(descricao,cidade,oid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"mensagem":"ocorrência atualizada"})

@app.delete("/ocorrencias/<int:oid>")
@login_required
@admin_or_owner_required(lambda oid: get_owner_id("ocorrencias", oid))
def delete_ocorrencia(oid):
    conn=get_db(); cur=conn.cursor()
    cur.execute("DELETE FROM ocorrencias WHERE id=%s",(oid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"mensagem":"ocorrência excluída"})

def get_owner_id(table, oid):
    conn=get_db(); cur=conn.cursor()
    cur.execute(f"SELECT user_id FROM {table} WHERE id=%s",(oid,))
    row=cur.fetchone(); cur.close(); conn.close()
    return row[0] if row else None

# ------------------ risco & clima ------------------

@app.get("/risco/<cidade>")
def calcular_risco(cidade):
    try:
        resp=requests.get("http://api.weatherapi.com/v1/forecast.json",params={
            "key":WEATHER_API_KEY,"q":cidade,"days":1,"lang":"pt"})
        dados=resp.json()
        chuva_prev=dados["forecast"]["forecastday"][0]["day"]["totalprecip_mm"]
        conn=get_db(); cur=conn.cursor()
        cur.execute("SELECT COUNT(*) FROM ocorrencias WHERE cidade=%s",(cidade,))
        total=cur.fetchone()[0]
        cur.close(); conn.close()
        risco="BAIXO"
        if chuva_prev>20 and total>=3: risco="ALTO"
        elif chuva_prev>5 and total>=1: risco="MEDIO"
        return jsonify({"cidade":cidade,"chuva_prevista_mm":chuva_prev,
                        "ocorrencias_historicas":total,"risco":risco})
    except Exception as e:
        return jsonify({"erro":str(e)}),500

@app.get("/clima/<cidade>")
def clima_atual(cidade):
    try:
        resp=requests.get("http://api.weatherapi.com/v1/current.json",params={
            "key":WEATHER_API_KEY,"q":cidade,"lang":"pt"})
        dados=resp.json()
        return jsonify({"condicao":dados["current"]["condition"]["text"],
                        "icone":"https:"+dados["current"]["condition"]["icon"],
                        "temp_c":dados["current"]["temp_c"],
                        "umidade":dados["current"]["humidity"]})
    except Exception as e:
        return jsonify({"erro":str(e)}),500

# ------------------ static ------------------

@app.get("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.get("/")
def serve_index():
    return send_from_directory(FRONT_DIR, "index.html")

@app.get("/<path:path>")
def serve_static(path):
    return send_from_directory(FRONT_DIR, path)

@app.route('/')
def index():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory(app.template_folder, 'admin.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
