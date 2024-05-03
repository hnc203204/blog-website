"""
Module docstring: This module initializes the blog_api package.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL
from flask_migrate import Migrate
from flask_restful import Api
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from blog_api.utils.emails import mail
import blog_api.utils.config as app_config
from blog_api.utils.responses import response_with
import blog_api.utils.responses as resp

db = SQLAlchemy()

url_obj = URL.create(
    "postgresql",
    username=os.getenv("username"),
    password=os.getenv("password"),
    host="localhost",
    port=5432,
    database="Blog_Website",
) 

def create_app(cfg=app_config.Development, alt_config=None):
    """Factory function to create a Flask app."""
    if alt_config is None:
        alt_config = {}
    application = Flask(__name__)
    CORS(application)
    application.config.from_object(cfg)
    application.config.update(alt_config)
    if alt_config.get("SQLALCHEMY_DATABASE_URI"):
        application.config["SQLALCHEMY_DATABASE_URI"] = alt_config.get("SQLALCHEMY_DATABASE_URI")
    @application.after_request
    def add_header(response):
        return response
    if not application.debug:
        file_handler = RotatingFileHandler(application.config["LOG_FILE"], maxBytes=100000, backupCount=10)
        application.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.WARNING)
        application.logger.addHandler(file_handler)
        application.logger.info("Blog application started")
        @application.errorhandler(500)
        def server_error(e):
            logging.error("An error occurred during a request. %s", e)
            return response_with(resp.SERVER_ERROR_500)

        @application.errorhandler(400)
        def bad_request(e):
            logging.error("A bad request occurred during a request. %s", e)
            return response_with(resp.BAD_REQUEST_400)

        @application.errorhandler(404)
        def not_found(e):
            logging.error("A resource was not found during a request. %s", e)
            return response_with(resp.SERVER_ERROR_404)

    return application

app = create_app(alt_config={
    "SQLALCHEMY_DATABASE_URI": url_obj, 
    "LOG_FILE": "application.log"})

mail.init_app(app)
migrate = Migrate(app, db)
api = Api(app)
jwt = JWTManager(app)

from blog_api.users.management.user_management import UserManagement
from blog_api.posts.posts_management.posts_mamagement import PostManagement
from blog_api.users.authenticate.authenticate import auth_blueprint

api.add_resource(UserManagement, "/api/users", "/api/users/<int:id>")
api.add_resource(PostManagement, "/api/posts", "/api/posts/<int:id>", "/api/posts/paginate/<int:page>")
app.register_blueprint(auth_blueprint, url_prefix="/api/authenticate")

db.init_app(app)
with app.app_context():
    db.create_all()
