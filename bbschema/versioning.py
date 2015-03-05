# -*- coding: utf8 -*-

# Copyright (C) 2014  Ben Ockmore

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This module specifies two structures to allow people to modify the data
contained in BookBrainz - Editor and Edit. Editors can make edits, which
are changes to the database."""

import sqlalchemy.orm
import sqlalchemy.sql as sql
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, SmallInteger,
                        Table, UnicodeText)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import text

from . import Base, Entity, EntityTree

edit_revision_table = Table(
    'edit_revision', Base.metadata,
    Column('edit_id', Integer, ForeignKey('bookbrainz.edit.id'),
           primary_key=True),
    Column('revision_id', Integer, ForeignKey('bookbrainz.revision.id'),
           primary_key=True),
    schema='bookbrainz'
)


class Edit(Base):
    __tablename__ = 'edit'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('bookbrainz.user.id'), nullable=False)
    status = Column(Integer, nullable=False)

    user = relationship('User', backref='edits')
    edit_notes = relationship('EditNote')
    revisions = relationship('Revision', secondary=edit_revision_table,
                             backref='edits')


class Revision(Base):
    __tablename__ = 'revision'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('bookbrainz.user.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False,
                        server_default=sql.func.now())

    user = relationship('User', backref='revisions')

    _type = Column(SmallInteger, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 0,
        'polymorphic_on': _type
    }


class EntityRevision(Revision):
    __tablename__ = 'entity_revision'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, ForeignKey('bookbrainz.revision.id'),
                primary_key=True)

    entity_gid = Column(UUID(as_uuid=True),
                        ForeignKey('bookbrainz.entity.gid'), nullable=False)
    entity_tree_id = Column(
        Integer, ForeignKey('bookbrainz.entity_tree.id'), nullable=False
    )

    entity = relationship('Entity', foreign_keys=[entity_gid])
    entity_tree = relationship('EntityTree')

    __mapper_args__ = {
        'polymorphic_identity': 1,
    }

    @classmethod
    def create(cls, user, revision_json):
        entity = Entity()

        entity_tree = EntityTree.create(revision_json)

        revision = cls()
        revision.user = user
        revision.entity = entity
        revision.entity_tree = entity_tree

        return revision

    @classmethod
    def update(cls, user, revision_json, session):
        try:
            entity = session.query(Entity).\
                filter_by(gid=revision_json['gid'][0]).one()
        except NoResultFound:
            return None

        if entity.master_revision_id is None:
            return None

        old_tree = entity.master_revision.entity_tree

        new_tree = old_tree.update(revision_json)

        if new_tree == old_tree:
            return None

        revision = cls()
        revision.user = user
        revision.entity = entity
        revision.entity_tree = new_tree

        return revision


class RelationshipRevision(Revision):
    __tablename__ = 'rel_revision'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, ForeignKey('bookbrainz.revision.id'),
                primary_key=True)

    relationship_id = Column(Integer, ForeignKey('bookbrainz.rel.id'),
                             nullable=False)
    relationship_tree_id = Column(
        Integer, ForeignKey('bookbrainz.rel_tree.id'), nullable=False
    )

    relationship = sqlalchemy.orm.relationship('Relationship',
                                               foreign_keys=[relationship_id])
    relationship_tree = sqlalchemy.orm.relationship('RelationshipTree')

    __mapper_args__ = {
        'polymorphic_identity': 2,
    }


class EditNote(Base):
    __tablename__ = 'edit_note'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('bookbrainz.user.id'),
                     nullable=False)
    edit_id = Column(Integer, ForeignKey('bookbrainz.edit.id'),
                     nullable=False)
    content = Column(UnicodeText, nullable=False)
    posted_at = Column(DateTime(timezone=True), nullable=False,
                       server_default=sql.func.now())

    user = relationship('User')
