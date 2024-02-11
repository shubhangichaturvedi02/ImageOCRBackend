from werkzeug.security import check_password_hash
from app.models import User


def authenticate(email, password):
    user:User = User.query.filter(User.email== email).with_entities(User.id,User.public_id,User.email,User.password).first()
    print(user)
    if user and check_password_hash(user.password, password):
        return user


def identity(payload):
    user_id = payload['identity']
    return User.find_by_id(user_id)