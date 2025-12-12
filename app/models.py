import hashlib
from datetime import datetime

from flask import current_app

from app.db import db
from werkzeug.security import check_password_hash, generate_password_hash
try:
    from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
except ImportError:
    # itsdangerous 2.x 移除了 TimedJSONWebSignatureSerializer，使用 URLSafeTimedSerializer
    from itsdangerous import URLSafeTimedSerializer as Serializer

from flask_login import UserMixin, AnonymousUserMixin

class ShortURL(db.Model):
    __tablename__ = 'urls'
    id = db.Column(db.Integer, primary_key=True)
    origin_url = db.Column(db.String(256), index=True)
    shorten_url = db.Column(db.String(32), index=True) # 务必建立唯一索引
    shorten_url_created_by = db.Column(db.String(64), unique=True) # 务必建立联合唯一索引
    created_at = db.Column(db.DateTime())  # start_at_desc
    created_by = db.Column(db.Integer)  # owner
    is_public = db.Column(db.Integer, default=False)  # 是否是公开的网址

    def __repr__(self):
        return "URL origin %s, shorten %s" % (self.origin_url[:16], self.shorten_url)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), index=True)
    password_hash = db.Column(db.String(256))
    user_type = db.Column(db.Integer) # 用户类型,1表示超级管理员,2表示普通用户
    email = db.Column(db.String(64), unique=True, index=True)
    member_since = db.Column(db.DateTime(), default=datetime.now)
    last_seen = db.Column(db.DateTime(), default=datetime.now)
    confirmed = db.Column(db.Boolean, default=True) # TODO some problems with the sendmail lib or config

    def ping(self):
        self.last_seen = datetime.now()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError("No password attr")

    @password.setter
    def password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self,pwd):
        return check_password_hash(self.password_hash, pwd)

    ###
    def generate_confirmation_token(self, expiration=3600):
        # 确保 SECRET_KEY 是字符串
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key, expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key, expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key, expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True
    ###


    def generate_auth_token(self, expiration):
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key, expires_in=expiration)
        token = s.dumps({'id': self.id})
        # itsdangerous 2.x 返回 bytes，需要解码
        if isinstance(token, bytes):
            return token.decode('ascii')
        return token

    @staticmethod
    def verify_auth_token(token):
        secret_key = str(current_app.config.get('SECRET_KEY', 'default-secret-key'))
        s = Serializer(secret_key)
        try:
            # 如果 token 是字符串，需要编码
            if isinstance(token, str):
                token = token.encode('ascii')
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])


class Conversation(db.Model):
    """会话表 - v0 简化版"""
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))  # 会话标题（自动生成或手动设置）
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.title}>'


class Message(db.Model):
    """消息表 - v0 简化版"""
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)  # 消息内容
    created_at = db.Column(db.DateTime, default=datetime.now)
    order_index = db.Column(db.Integer)  # 消息在会话中的顺序
    
    def __repr__(self):
        return f'<Message {self.id}: {self.role}>'
