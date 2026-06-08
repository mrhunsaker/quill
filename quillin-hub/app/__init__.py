from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost/quillin_hub')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    
    # Extensions
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Blueprints
    from .api.plugins import plugins_bp
    from .web.routes import web_bp
    from .forge.forms import forge_bp
    
    app.register_blueprint(plugins_bp, url_prefix='/api/v1')
    app.register_blueprint(web_bp)
    app.register_blueprint(forge_bp, url_prefix='/forge')
    
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        
    return app
