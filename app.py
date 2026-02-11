"""
============================================================================
APP.PY - SKIN CANCER ANALYZER
Aplicação Flask para análise de câncer de pele com IA
============================================================================
"""

import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image
import logging
from logging.handlers import RotatingFileHandler

# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MODEL_PATH'] = os.getenv('MODEL_PATH', 'models')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# CORS
CORS(app)

# ============================================================================
# LOGGING
# ============================================================================
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10240000,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Skin Cancer Analyzer startup')

# ============================================================================
# CARREGAR MODELO DE IA
# ============================================================================
model = None

def load_model():
    """Carrega o modelo de IA"""
    global model
    try:
        # Descomente quando tiver TensorFlow instalado
        # from tensorflow import keras
        # model_file = os.path.join(app.config['MODEL_PATH'], 'skin_cancer_model.h5')
        # model = keras.models.load_model(model_file)
        # app.logger.info(f'✅ Model loaded successfully from {model_file}')
        app.logger.info('⚠️  Model loading disabled - uncomment code when ready')
        return True
    except Exception as e:
        app.logger.error(f'❌ Error loading model: {str(e)}')
        return False

# Tentar carregar modelo na inicialização
load_model()

# ============================================================================
# CLASSES DE DIAGNÓSTICO
# ============================================================================
SKIN_CLASSES = {
    0: 'Melanoma',
    1: 'Basal Cell Carcinoma',
    2: 'Squamous Cell Carcinoma',
    3: 'Actinic Keratosis',
    4: 'Benign Keratosis',
    5: 'Dermatofibroma',
    6: 'Melanocytic Nevus',
    7: 'Vascular Lesion'
}

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================
def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def preprocess_image(image_path, target_size=(224, 224)):
    """Pré-processa imagem para o modelo"""
    try:
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize(target_size)
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    except Exception as e:
        app.logger.error(f'Error preprocessing image: {str(e)}')
        raise

def predict_skin_cancer(image_path):
    """Realiza predição de câncer de pele"""
    try:
        # Pré-processar imagem
        processed_image = preprocess_image(image_path)
        
        # SIMULAÇÃO - Substitua com predição real do modelo
        if model is None:
            # Simulação para testes
            app.logger.warning('Using simulated prediction - model not loaded')
            predictions = np.random.rand(len(SKIN_CLASSES))
            predictions = predictions / predictions.sum()
        else:
            # Predição real
            predictions = model.predict(processed_image)[0]
        
        # Processar resultados
        predicted_class = np.argmax(predictions)
        confidence = float(predictions[predicted_class])
        
        # Criar dicionário de todas as predições
        all_predictions = {
            SKIN_CLASSES[i]: float(predictions[i])
            for i in range(len(SKIN_CLASSES))
        }
        
        # Ordenar por confiança
        sorted_predictions = dict(
            sorted(all_predictions.items(), key=lambda x: x[1], reverse=True)
        )
        
        return {
            'predicted_class': SKIN_CLASSES[predicted_class],
            'confidence': confidence,
            'all_predictions': sorted_predictions
        }
        
    except Exception as e:
        app.logger.error(f'Error during prediction: {str(e)}')
        raise

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Página inicial"""
    return jsonify({
        'message': 'Skin Cancer Analyzer API',
        'version': '1.0.0',
        'status': 'running',
        'model_loaded': model is not None
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'model_loaded': model is not None
    }), 200

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Endpoint para análise de imagem"""
    start_time = time.time()
    
    try:
        # Verificar se arquivo foi enviado
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Verificar nome do arquivo
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Verificar extensão
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
            }), 400
        
        # Salvar arquivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)
        
        app.logger.info(f'File saved: {filepath}')
        
        # Realizar predição
        prediction_result = predict_skin_cancer(filepath)
        
        # Calcular tempo de processamento
        processing_time = time.time() - start_time
        
        # Preparar resposta
        response = {
            'success': True,
            'filename': filename,
            'prediction': prediction_result['predicted_class'],
            'confidence': prediction_result['confidence'],
            'all_predictions': prediction_result['all_predictions'],
            'processing_time': round(processing_time, 3),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        app.logger.info(f'Analysis completed: {prediction_result["predicted_class"]} ({prediction_result["confidence"]:.2%})')
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f'Error during analysis: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Retorna lista de classes de diagnóstico"""
    return jsonify({
        'classes': SKIN_CLASSES,
        'total': len(SKIN_CLASSES)
    }), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas básicas"""
    upload_folder = app.config['UPLOAD_FOLDER']
    
    if os.path.exists(upload_folder):
        total_analyses = len([f for f in os.listdir(upload_folder) if os.path.isfile(os.path.join(upload_folder, f))])
    else:
        total_analyses = 0
    
    return jsonify({
        'total_analyses': total_analyses,
        'model_loaded': model is not None,
        'available_classes': len(SKIN_CLASSES),
        'uptime': 'N/A'  # Implementar contador de uptime se necessário
    }), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal error: {str(error)}')
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': f'File too large. Maximum size: {app.config["MAX_CONTENT_LENGTH"] / (1024*1024):.1f}MB'
    }), 413

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Modo de execução
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    app.logger.info('=' * 50)
    app.logger.info('  SKIN CANCER ANALYZER - Starting')
    app.logger.info('=' * 50)
    app.logger.info(f'  Debug mode: {debug_mode}')
    app.logger.info(f'  Port: {port}')
    app.logger.info(f'  Upload folder: {app.config["UPLOAD_FOLDER"]}')
    app.logger.info(f'  Model path: {app.config["MODEL_PATH"]}')
    app.logger.info('=' * 50)
    
    # Rodar aplicação
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )
