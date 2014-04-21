from flask import request
from flask.ext.restful import abort, Resource
from sqlalchemy.exc import IntegrityError

from uamhnach import api, db, models, permission_required


class Users(Resource):

    @permission_required('user_read')
    def get(self):
        return [u.to_json() for u in models.User.query.all()]

    @permission_required('user_create')
    def post(self):
        payload = request.get_json()

        try:
            name = payload['name']
            email = payload['email']
            password = payload['password']
        except KeyError:
            abort(400)

        user = models.User(name, email, password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)

        return user.to_json(), 201


class User(Resource):

    @permission_required('user_read', or_self=True)
    def get(self, user_id):
        user = models.User.query.filter_by(id=user_id).first()
        if user is None:
            abort(404)
        return user.to_json()

    @permission_required('user_update', or_self=True)
    def put(self, user_id):
        user = models.User.query.filter_by(id=user_id).first()
        if user is None:
            abort(404)

        payload = request.get_json()

        for key in payload.keys():
            if key not in ['name', 'email', 'password']:
                abort(400)

        for key, value in payload.iteritems():
            if key == 'password':
                user.set_password(value)
            else:
                setattr(user, key, value)

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)

        return user.to_json()

    @permission_required('user_delete')
    def delete(self, user_id):
        user = models.User.query.filter_by(id=user_id).first()
        if user is None:
            abort(404)

        db.session.delete(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)


api.add_resource(Users, '/users')
api.add_resource(User, '/user/<int:user_id>')
