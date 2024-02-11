from app import db
# from datetime import datetime
from sqlalchemy import text
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, DateTime


class User(db.Model):
    __table_args__ = {
        'schema': 'public'
    }
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)
    is_active = db.Column(db.Boolean,default=True)
    created_on = db.Column(DateTime(timezone=True), server_default=func.now())
    last_login = db.Column(db.DATETIME)
    jwt_token = db.Column(db.Text)

class ImageData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    bold_text = db.Column(db.Text, nullable=False)
    created_on = db.Column(DateTime(timezone=True), server_default=func.now())
