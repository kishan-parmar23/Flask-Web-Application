from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_Name = "database.db"

def create_App():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'oiewrunfmcoiweh'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_Name}'
    db.init_app(app)
    from flask_login import LoginManager
    
     
    
    from .views import views 
    from .auth import auth
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    from .models import User, Note
    
    create_database(app)
    
    Login_manager = LoginManager()
    Login_manager.login_view = 'auth.login'
    Login_manager.init_app(app)
    
    @Login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
     
    return app

def create_database(app):
    if not path.exists('website/' + DB_Name):
        with app.app_context():
            db.create_all()
        print('Database Created!')