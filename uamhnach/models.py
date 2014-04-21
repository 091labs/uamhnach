from datetime import datetime, timedelta
import hashlib
import uuid

from flask import g

from uamhnach import app, db


groups = db.Table('groups',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
)
permissions = db.Table('permissions',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True, unique=True)
    pw_hash = db.Column(db.String(128))
    pw_salt = db.Column(db.String(32))
    groups = db.relationship('Group',
                             secondary=groups,
                             lazy='dynamic',
                             backref=db.backref('users', lazy='dynamic'))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.set_password(password)

    def __repr__(self):
        return '<User %s>' % self.email

    def set_password(self, password):
        self.pw_salt = uuid.uuid4().hex
        self.pw_hash = hashlib.sha512(password + self.pw_salt).hexdigest()
        for token in Token.query.filter_by(user_id=self.id):
            token.expire()

    def check_password(self, password):
        check_hash = hashlib.sha512(password + self.pw_salt).hexdigest()
        return check_hash == self.pw_hash

    def has_permission(self, name):
        permission = Permission.query.filter_by(name=name).first()
        if not permission:
            return False
        for group in self.groups:
            if permission in group.permissions:
                return True
        return False

    def to_json(self):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
        }
        if g.user and g.user.has_permission('group_read'):
            data['groups'] = [gr.to_json() for gr in self.groups]
        return data


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    permissions = db.relationship('Permission',
                                  secondary=permissions,
                                  lazy='dynamic',
                                  backref=db.backref('groups',
                                                     lazy='dynamic'))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Group %s>' % self.name

    def to_json(self):
        data = {
            'id': self.id,
            'name': self.name,
        }
        if g.user and g.user.has_permission('permission_read'):
            data['permissions'] = [p.to_json() for p in self.permissions]
        return data


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Permission %s>' % self.name

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class Token(db.Model):
    id = db.Column(db.String(32), index=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created = db.Column(db.DateTime)
    expires = db.Column(db.DateTime)

    def __init__(self, user_id):
        self.id = uuid.uuid4().hex
        self.user_id = user_id
        self.created = datetime.utcnow()
        lifespan = timedelta(seconds=app.config['TOKEN_LIFESPAN'])
        self.expires = self.created + lifespan

    def __repr__(self):
        return '<Token %s>' % self.id

    def get_user(self):
        user = User.query.filter_by(id=self.user_id).first()
        return user

    def is_valid(self):
        return datetime.utcnow() < self.expires

    def has_permission(self, name):
        user = self.get_user()
        if user is None:
            return False
        return self.is_valid() and user.has_permission(name)

    def to_json(self):
        return {
            'id': self.id,
            'created': str(self.created),
            'expires': str(self.expires),
        }

    def expire(self):
        self.expires = datetime.utcnow()
