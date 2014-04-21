from flask import Flask, g, request
from flask.ext.restful import Api, abort
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object('config')
api = Api(app, prefix='/v1')
db = SQLAlchemy(app)


# enforce foreign key constraints in sqlite
if app.config['SQLALCHEMY_DATABASE_ENGINE'] == 'sqlite':
    from sqlalchemy.engine import Engine
    from sqlalchemy import event

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


from uamhnach import models


@app.before_request
def before_request():
    # prune expired tokens
    for token in models.Token.query.all():
        if not token.is_valid():
            db.session.delete(token)
    db.session.commit()

    # validate current one and set g.user
    user = None
    if 'X-Auth-Token' in request.headers:
        auth_token_id = request.headers['X-Auth-Token']
        auth_token = models.Token.query.filter_by(id=auth_token_id).first()
        if auth_token and auth_token.is_valid():
            user = auth_token.get_user()
    g.user = user


def permission_required(permission, or_self=False):
    def inner(func):
        def wrapper(*args, **kwargs):
            if g.user:
                user_id = kwargs.get('user_id', None)
                if or_self and user_id and g.user.id == user_id:
                    return func(*args, **kwargs)
                if g.user.has_permission(permission):
                    return func(*args, **kwargs)
            else:
                abort(401)
        return wrapper
    return inner


from uamhnach.resources import tokens
from uamhnach.resources import users
from uamhnach.resources import groups
from uamhnach.resources import permissions
