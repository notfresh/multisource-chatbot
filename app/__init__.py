# coding=utf-8
import os
import random
from datetime import datetime, timedelta
import json
from flask import jsonify

from flask import Flask, render_template, flash, url_for, request
from flask_login import LoginManager, login_required
from flask_mail import Mail
from flask_wtf import FlaskForm as Form
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, AnonymousUserMixin

from werkzeug.utils import redirect
from config import CONFIGS

from .models import User


# 在全局创建 app，供模块级别的路由装饰器使用
app = Flask(__name__)

# redis_client = FlaskRedis()
mail = Mail()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

shorten_items = []
shorten_items_mapping = {}
shorten_items_init_flag = False

def create_app(flask_config='development', **kwargs):
    # 使用全局 app 变量（第 28 行已创建），这样所有在模块级别注册的路由都能正常工作
    # 优先使用 FLASK_DEBUG，如果没有则使用 FLASK_ENV（向后兼容）
    # Flask 2.3+ 推荐使用 FLASK_DEBUG 而不是 FLASK_ENV
    flask_debug = os.getenv('FLASK_DEBUG')
    if flask_debug is not None:
        # FLASK_DEBUG 是字符串 '1' 或 'true' 表示 True
        config_name = 'development' if flask_debug.lower() in ('1', 'true', 'yes', 'on') else 'production'
    else:
        # 向后兼容：如果没有 FLASK_DEBUG，使用 FLASK_ENV
        config_name = os.getenv('FLASK_ENV', flask_config)
    app.config.from_object(CONFIGS[config_name])
    # 确保 SECRET_KEY 是字符串类型
    if 'SECRET_KEY' not in app.config or not isinstance(app.config['SECRET_KEY'], str):
        app.config['SECRET_KEY'] = 'so easy you are'
    from . import models # 创建表（Flask-SQLAlchemy 模型）
    # 导入原生 SQLAlchemy 模型（app/core/db.py），让 Flask-Migrate 能够检测到
    from .core.db import ConversationDBModel, MessageDBModel, Base
    from . import errorhandlers
    errorhandlers.init_app(app)
    from . import db
    db.init_app(app)
    
    # 初始化 Flask-Migrate
    from flask_migrate import Migrate
    migrate = Migrate(app, db)
    
    bootstrap = Bootstrap(app)
    # redis_client.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    # 注册 API 蓝图
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)
    
    with app.app_context():
        init_shorten_urls(None)
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class AnonymousUser(AnonymousUserMixin):
    pass

login_manager.anonymous_user = AnonymousUser


# 注册聊天页面路由
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    return redirect('/chat')

