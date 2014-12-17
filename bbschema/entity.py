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

"""This module specifies a class, Resource, which is designed to be used as the
base class for all resource models specified in this package."""

import sqlalchemy.sql as sql
from bbschema.base import Base
from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Table, UnicodeText)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text


class Entity(Base):
    """Resource class, from which all other resource models are derived."""

    __tablename__ = 'entity'
    __table_args__ = {'schema': 'bookbrainz'}

    gid = Column(UUID(as_uuid=True), primary_key=True,
                 server_default=text('public.uuid_generate_v4()'))

    last_updated = Column(DateTime, nullable=False,
                          server_default=sql.func.now())
    master_revision_id = Column(
        Integer, ForeignKey('bookbrainz.entity_revision.id', use_alter=True,
                            name='fk_master_revision_id')
    )

    master_revision = relationship(
        'EntityRevision', foreign_keys=[master_revision_id], post_update=True
    )

class EntityRedirect(Base):
    __tablename__ = 'entity_redirect'
    __table_args__ = {'schema': 'bookbrainz'}

    source_gid = Column(UUID(as_uuid=True), primary_key=True)
    target_gid = Column(UUID(as_uuid=True),
                        ForeignKey('bookbrainz.entity.gid'), nullable=False)


entity_tree_alias = Table('entity_tree_alias', Base.metadata,
    Column('entity_tree_id', Integer, ForeignKey('bookbrainz.entity_tree.id')),
    Column('alias_id', Integer, ForeignKey('bookbrainz.alias.id')),
    schema='bookbrainz'
)


class EntityTree(Base):
    __tablename__ = 'entity_tree'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)

    annotation_id = Column(Integer, ForeignKey('bookbrainz.annotation.id'))
    disambiguation_id = Column(Integer,
                               ForeignKey('bookbrainz.disambiguation.id'))

    data_id = Column(Integer, ForeignKey('bookbrainz.entity_data.id'), nullable=False)

    annotation = relationship('Annotation')
    disambiguation = relationship('Disambiguation')
    data = relationship('EntityData')
    aliases = relationship("Alias", secondary=entity_tree_alias)


class EntityData(Base):
    __tablename__ = 'entity_data'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)

    # For inheritance and url redirection
    _type = Column(Integer, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 0,
        'polymorphic_on': _type
    }


class Annotation(Base):
    __tablename__ = 'annotation'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)

    content = Column(UnicodeText, nullable=False, server_default="")
    created_at = Column(DateTime, nullable=False,
                        server_default=sql.func.now())


class Disambiguation(Base):
    __tablename__ = 'disambiguation'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)
    comment = Column(UnicodeText, nullable=False, server_default="")


class Alias(Base):
    """An alias, or alternative name, for some Resource."""

    __tablename__ = 'alias'
    __table_args__ = {'schema': 'bookbrainz'}

    id = Column(Integer, primary_key=True)

    name = Column(UnicodeText, nullable=False)
    sort_name = Column(UnicodeText, nullable=False)

    language_id = Column(Integer)
