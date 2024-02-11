from flask import Flask,jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from os import environ 
from dotenv import load_dotenv
from flask_restful import Api
from flask_jwt import JWT
from flask_jwt_extended import JWTManager
# from flask_mail import Mail, Message
from flask_cors import CORS


load_dotenv()



app = Flask(__name__)
CORS(app)

api = Api(app)
app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('SQLALCHEMY_DATABASE_URI') #Postgresql connection
app.config['JWT_AUTH_USERNAME_KEY'] = 'email'
#
# app.config['MAIL_SERVER']='smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'mailsendertestdaily@gmail.com'
# app.config['MAIL_PASSWORD'] = 'ppcwnlkcdirbxnik'
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True



db = SQLAlchemy(app)
# mail = Mail(app)



from app import routes
from security import authenticate, identity
# app.config['JWT_AUTH_URL_RULE'] = '/login'
jwt = JWTManager(app)
