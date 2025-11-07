from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from dotenv import load_dotenv
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
import os
from bson.objectid import ObjectId
from datetime import datetime # ¡Nuevo! Para guardar la fecha de la encuesta
from flask_cors import CORS

# Cargar variables de entorno (desde tu archivo .env)
load_dotenv()

# --- 1. Inicialización y Configuración ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')
bcrypt = Bcrypt(app)

# --- 2. Configuración de MongoDB ---
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'users') # Colección de usuarios
COLLECTION_NAME_SURVEYS = 'user_surveys' # Nueva colección para encuestas

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database('Base_de_datos_we')
    users_collection = db[COLLECTION_NAME]
    surveys_collection = db[COLLECTION_NAME_SURVEYS] # ¡Nuevo! Colección de encuestas
    print("✅ MongoDB Conectado a la base de datos:", 'keniarcctpa_db_use')
except Exception as e:
    print(f" Error al conectar a MongoDB: {e}")
    # En producción, podrías detener el servidor aquí

# --- 3. Rutas para Servir Vistas HTML ---

@app.route('/')
def home():
    """Ruta principal, que según tu descripción, debe llevar a Inicio.html."""
    return render_template('index.html')

@app.route('/iniciore')
def show_register():
    """Ruta para mostrar la página de registro (iniciore.html)."""
    return render_template('iniciore.html')

@app.route('/iniciose')
def show_login():
    """Ruta para mostrar la página de inicio de sesión (iniciose.html)."""
    return render_template('iniciose.html')

@app.route('/tips')
def show_tips():
    """Ruta para mostrar la página de consejos (tips.html)."""
    # Flask buscará 'tips.html' dentro de la carpeta 'templates'
    return render_template('tips.html')

@app.route('/index')
def index():
    """Ruta para la página principal después del login (index.html)."""
    # IMPORTANTE: Se debería verificar si el usuario está en la sesión
    if 'user_id' not in session:
         return redirect(url_for('show_login'))
    
    return render_template('index.html')

# --- NUEVA RUTA DE ENCUESTA ---
@app.route('/encuesta')
def show_survey():
    """Ruta para mostrar la página de la encuesta (encuesta.html) y cargar resultados previos."""
    if 'user_id' not in session:
        return redirect(url_for('show_login'))
    
    user_id = session['user_id']
    
    # Buscar el resultado de la última encuesta
    last_survey = surveys_collection.find_one(
        {"user_id": user_id},
        sort=[('timestamp', -1)] # Ordenar por fecha descendente (más reciente)
    )
    
    result = None
    if last_survey:
        result = {
            "score": last_survey['score'],
            "level": last_survey['level'],
            # Formatear la fecha para mostrar en el HTML
            "date": last_survey['timestamp'].strftime("%d/%m/%Y a las %H:%M") 
        }
    
    # Se pasa el resultado al template
    return render_template('encuesta.html', result=result)
# ------------------------------

# --- 4. Rutas de la API de Autenticación (Los Endpoints) ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Endpoint para el registro de nuevos usuarios."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Faltan email o contraseña"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"msg": "El usuario ya existe"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = {"email": email, "password": hashed_password}
    users_collection.insert_one(new_user)

    return jsonify({"msg": "Registro exitoso. Serás redirigido para iniciar sesión."}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Endpoint para el inicio de sesión."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Faltan email o contraseña"}), 400

    user = users_collection.find_one({"email": email})

    if user and bcrypt.check_password_hash(user['password'], password):
        # 3. Iniciar sesión en Flask
        session['user_id'] = str(user['_id'])
        
        # Devuelve éxito.
        return jsonify({"msg": "Inicio de sesión exitoso"}), 200
    else:
        return jsonify({"msg": "Credenciales inválidas"}), 401

# --- NUEVO ENDPOINT PARA LA ENCUESTA ---
@app.route('/api/survey/submit', methods=['POST'])
def submit_survey():
    """Endpoint para recibir y procesar las respuestas de la encuesta."""
    if 'user_id' not in session:
        return jsonify({"msg": "No autorizado, inicie sesión."}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    
    score = 0
    questions = data.get('questions', {})
    
    # Índice de la respuesta que otorga 1 punto (0=A, 1=B, 2=C, 3=D)
    # Basado en la opción más positiva para cada habilidad blanda
    correct_answers = {
        'q1': 0, 'q2': 1, 'q3': 2, 'q4': 2, 'q5': 0,
        'q6': 2, 'q7': 2, 'q8': 2, 'q9': 0, 'q10': 1,
        'q11': 0, 'q12': 2, 'q13': 1, 'q14': 2, 'q15': 2,
        'q16': 2, 'q17': 0, 'q18': 2, 'q19': 0, 'q20': 2,
    }
    
    if len(questions) != 20:
        return jsonify({"msg": "Faltan respuestas en la encuesta. Por favor, responde las 20 preguntas."}), 400
    
    # Calcular la puntuación
    for q_id, answer_index_str in questions.items():
        try:
            answer_index = int(answer_index_str)
            if q_id in correct_answers and answer_index == correct_answers[q_id]:
                score += 1 # 1 punto por respuesta "correcta" (mejor práctica)
        except ValueError:
             return jsonify({"msg": f"Respuesta inválida para la pregunta {q_id}."}), 400

    # Asignación de Nivel
    # 1 a 8 bajo | 9 a 14 medio | 15 a 20 alto
    if 1 <= score <= 8:
        level = "Bajo"
    elif 9 <= score <= 14:
        level = "Medio"
    elif 15 <= score <= 20:
        level = "Alto"
    else:
        level = "Bajo" # Asume el nivel más bajo si el puntaje es 0 (aunque es improbable con 20 preguntas)
        
    # Guardar resultados en MongoDB
    survey_result = {
        "user_id": user_id,
        "score": score,
        "level": level,
        "timestamp": datetime.utcnow(),
        "responses": questions 
    }
    
    surveys_collection.insert_one(survey_result)
    
    return jsonify({
        "msg": "Encuesta guardada exitosamente. Recargando resultados...",
        "score": score,
        "level": level
    }), 200
# ---------------------------------------

# --- 5. Ejecutar la aplicación ---
if __name__ == '__main__':
    # Usar un puerto diferente al 5000 si es necesario.
    app.run(debug=True, port=5000)