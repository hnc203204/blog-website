from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from blog_api.models.user_model import User
from blog_api.utils.responses import response_with
import blog_api.utils.responses as resp
import logging
from blog_api import db, jwt

auth_blueprint = Blueprint("auth", __name__)

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.get(identity)


@auth_blueprint.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if 'name' in data.keys():
            user = User.query.filter_by(name=data['name']).first()
        elif 'email' in data.keys():
            user = User.query.filter_by(email=data['email']).first()
        if not user or not user.isVerified:
            return response_with(resp.BAD_REQUEST_400, value={"error": "User not found or not verified"})
        if not user.check_password(data['password']):
            return response_with(resp.UNAUTHORIZED_403, value={"error": "Invalid password"})
        
        access_token = create_access_token(identity=user)
        return response_with(resp.SUCCESS_200, value={"access_token": access_token})
    except Exception as e:
        logging.error(e)
        return response_with(resp.SERVER_ERROR_500)
    
@auth_blueprint.route("/confirm/<token>", methods=["GET"])
def confirm_email(token):
    try:
        email = User.decode_email(token)
        user = User.find_by_email(email)
        if not user:
            return response_with(resp.BAD_REQUEST_400, value={"error": "User not found"})
        user.set_verified()
        db.session.commit()
        return response_with(resp.SUCCESS_200, value={"message": "Email confirmed"})
    except Exception as e:
        logging.error(e)
        return response_with(resp.SERVER_ERROR_500)

@auth_blueprint.route("/current_user", methods=["POST"])
@jwt_required()
def current_user():
    user = User.query.get(get_jwt_identity())
    return response_with(resp.SUCCESS_200, value=user.serialize())

