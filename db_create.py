#!/usr/bin/env python

from getpass import getpass
import os.path

from migrate.versioning import api
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO
from uamhnach import db
from uamhnach.models import User, Group, Permission


db.create_all()
if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI,
                        SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI,
                        SQLALCHEMY_MIGRATE_REPO,
                        api.version(SQLALCHEMY_MIGRATE_REPO))


# create some default permissions
db.session.add(Permission('user_create'))
db.session.add(Permission('user_read'))
db.session.add(Permission('user_update'))
db.session.add(Permission('user_delete'))
db.session.add(Permission('group_create'))
db.session.add(Permission('group_read'))
db.session.add(Permission('group_update'))
db.session.add(Permission('group_delete'))
db.session.add(Permission('permission_create'))
db.session.add(Permission('permission_read'))
db.session.add(Permission('permission_update'))
db.session.add(Permission('permission_delete'))
db.session.add(Permission('token_revoke'))

# create some default groups
db.session.add(Group('nobody'))
db.session.add(Group('superuser'))

# create a default user
username = raw_input('Please enter a name for the superuser: ')
email = raw_input('Please enter an email for the superuser: ')
password = getpass('Please enter a password for the superuser: ')
superuser = User(username, email, password)
db.session.add(superuser)

db.session.commit()

g = Group.query.filter_by(name='superuser').first()
for perm in Permission.query.all():
    g.permissions.append(perm)

superuser.groups.append(g)

db.session.add(superuser)
db.session.commit()
