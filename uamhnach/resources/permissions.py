from flask import request
from flask.ext.restful import abort, Resource
from sqlalchemy.exc import IntegrityError

from uamhnach import api, db, models, permission_required


class Permissions(Resource):

    @permission_required('permission_read')
    def get(self):
        return [p.to_json() for p in models.Permission.query.all()]

    @permission_required('permission_create')
    def post(self):
        payload = request.get_json()

        try:
            name = payload['name']
        except KeyError:
            abort(400)

        permission = models.Permission(name)
        db.session.add(permission)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)

        return permission.to_json(), 201


class Permission(Resource):

    @permission_required('permission_read')
    def get(self, permission_id):
        permission = \
            models.Permission.query.filter_by(id=permission_id).first()
        if permission is None:
            abort(404)
        return permission.to_json()

    @permission_required('permission_update')
    def put(self, permission_id):
        permission = \
            models.Permission.query.filter_by(id=permission_id).first()
        if permission is None:
            abort(404)

        payload = request.get_json()

        for group_id, action in payload.iteritems():
            group = models.Group.query.filter_by(id=group_id).first()
            if group is None:
                abort(403)
            if action == 'add':
                permission.groups.append(group)
            elif action == 'delete':
                if group not in permission.groups:
                    abort(403)
                permission.groups.remove(group)
            else:
                abort(403)

        db.session.add(permission)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)
        return permission.to_json(), 200

    @permission_required('permission_delete')
    def delete(self, permission_id):
        permission = \
            models.Permission.query.filter_by(id=permission_id).first()
        if permission is None:
            abort(404)

        db.session.delete(permission)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)


api.add_resource(Permissions, '/permissions')
api.add_resource(Permission, '/permission/<int:permission_id>')
