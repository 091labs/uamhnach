from flask import g, request
from flask.ext.restful import abort, Resource
from sqlalchemy.exc import IntegrityError

from uamhnach import api, db, permission_required
from uamhnach.models import User, Token


class Tokens(Resource):

    def post(self):
        payload = request.get_json()

        try:
            email = payload['email']
            password = payload['password']
        except KeyError:
            abort(400)

        user = User.query.filter_by(email=email).first()
        if user is None:
            abort(403)
        if not user.check_password(password):
            abort(401)

        token = Token(user.id)
        db.session.add(token)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)
        return token.to_json(), 201


class Revoker(Resource):

    def post(self):
        payload = request.get_json()

        try:
            token_id = payload['id']
        except KeyError:
            abort(400)

        token = Token.query.filter_by(id=token_id).first()
        if token is None or not token.is_valid():
            abort(403)

        user_id = token.get_user().id
        self._post(user_id=user_id, token=token)

    @permission_required('token_revoke', or_self=True)
    def _post(self, user_id, token):
        token.expire()
        db.session.add(token)
        db.session.commit()
        return {'message': '%s revoked' % token.id}, 200


class Validator(Resource):

    def post(self):
        payload = request.get_json()

        try:
            token_id = payload['id']
        except KeyError:
            abort(400)

        token = Token.query.filter_by(id=token_id).first()
        data = {
            'id': token_id,
            'valid': 'false'
        }
        if token is None:
            return data

        if token.is_valid():
            data['valid'] = 'true'
        return data


api.add_resource(Tokens, '/tokens')
api.add_resource(Revoker, '/token/revoke')
api.add_resource(Validator, '/token/validate')
