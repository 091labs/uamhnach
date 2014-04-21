from flask import request
from flask.ext.restful import abort, Resource
from sqlalchemy.exc import IntegrityError

from uamhnach import api, db, models, permission_required


class Groups(Resource):

    @permission_required('group_read')
    def get(self):
        return [g.to_json() for g in models.Group.query.all()]

    @permission_required('group_create')
    def post(self):
        payload = request.get_json()

        try:
            name = payload['name']
        except KeyError:
            abort(400)

        group = models.Group(name)
        db.session.add(group)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)

        return group.to_json(), 201


class Group(Resource):

    @permission_required('group_read')
    def get(self, group_id):
        group = models.Group.query.filter_by(id=group_id).first()
        if group is None:
            abort(404)
        return group.to_json()

    @permission_required('group_update')
    def put(self, group_id):
        group = models.Group.query.filter_by(id=group_id).first()
        if group is None:
            abort(404)

        payload = request.get_json()

        for user_id, action in payload.iteritems():
            user = models.User.query.filter_by(id=user_id).first()
            if user is None:
                abort(403)
            if action == 'add':
                group.users.append(user)
            elif action == 'delete':
                if user not in group.users:
                    abort(403)
                group.users.remove(user)
            else:
                abort(403)

        db.session.add(group)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(403)
        return group.to_json(), 200


    @permission_required('group_delete')
    def delete(self, group_id):
        group = models.Group.query.filter_by(id=group_id).first()
        if group is None:
            abort(404)

        db.session.delete(group)
        try:
            db.session.add(group)
        except IntegrityError:
            db.session.rollback()
            abort(403)


api.add_resource(Groups, '/groups')
api.add_resource(Group, '/group/<int:group_id>')
