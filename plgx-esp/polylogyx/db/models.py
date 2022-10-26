# -*- coding: utf-8 -*-
import datetime as dt
import string
import uuid

import sqlalchemy
from sqlalchemy import event
from flask import current_app, json
from flask_login import UserMixin
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous.timed import TimedSerializer as Serializer
from sqlalchemy.ext.hybrid import hybrid_property
from flask_authorize import RestrictionsMixin, AllowancesMixin


from polylogyx.db.database import (
    ARRAY,
    INET,
    JSONB,
    Column,
    ForeignKey,
    Index,
    Model,
    SurrogatePK,
    Table,
    db,
    declared_attr,
    reference_col,
    relationship
)
from polylogyx.extensions import bcrypt

querypacks = Table(
    "query_packs",
    Column("pack.id", db.Integer, ForeignKey("pack.id")),
    Column("query.id", db.Integer, ForeignKey("query.id")),
)

pack_tags = Table(
    "pack_tags",
    Column("tag.id", db.Integer, ForeignKey("tag.id")),
    Column("pack.id", db.Integer, ForeignKey("pack.id"), index=True),
)

node_tags = Table(
    "node_tags",
    Column("tag.id", db.Integer, ForeignKey("tag.id")),
    Column("node.id", db.Integer, ForeignKey("node.id"), index=True),
)

query_tags = Table(
    "query_tags",
    Column("tag.id", db.Integer, ForeignKey("tag.id")),
    Column("query.id", db.Integer, ForeignKey("query.id"), index=True),
)


result_log_maps = Table(
    "result_log_maps",
    Column("result_log_id", db.Integer, ForeignKey("result_log.id")),
    Column("result_log_scan_id", db.Integer, ForeignKey("result_log_scan.id"), index=True),
)

UserGroup = db.Table(
    'user_group', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'))
)

UserRole = db.Table(
    'user_role', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
)


class User(UserMixin, SurrogatePK, Model):
    username = Column(db.String(80), unique=True, nullable=False)
    email = Column(db.String)
    password = db.Column(db.String, nullable=False)
    status = Column(db.Boolean, nullable=True, default=True)
    reset_password = Column(db.Boolean, nullable=True, default=False)
    reset_email = Column(db.Boolean, nullable=True, default=False)
    enable_sso = Column(db.Boolean, nullable=True, default=False)

    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    # `roles` and `groups` are reserved words that *must* be defined
    # on the `User` model to use group- or role-based authorization.
    roles = db.relationship('Role', secondary=UserRole)
    groups = db.relationship('Group', secondary=UserGroup)

    first_name = Column(db.String)
    last_name = Column(db.String)

    def __init__(self, username, password=None, email=None, first_name=None, last_name=None,
                 roles=[], groups=[], reset_password=None, status=None, enable_sso=None, reset_email=None,
                 **kwargs):
        self.username = username
        if password:
            self.set_password(password)
        else:
            self.password = None
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.roles = roles
        self.groups = groups
        if reset_password is not None:
            self.reset_password = reset_password
        if reset_email is not None:
            self.reset_email = reset_email
        if status is not None:
            self.status = status
        if enable_sso is not None:
            self.enable_sso = enable_sso

    def set_password(self, password):
        self.update(password=bcrypt.generate_password_hash(password).decode('utf-8'))
        return

    def check_password(self, value):
        if not self.password:
            # still do the computation
            return bcrypt.generate_password_hash(value) and False
        return bcrypt.check_password_hash(self.password, value)

    def generate_auth_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        if not token:
            return None
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user


class Role(AllowancesMixin, SurrogatePK, Model):
    __tablename__ = 'roles'

    name = Column(db.String, nullable=False, unique=True)
    access_level = Column(db.Integer, nullable=True, unique=True)
    description = Column(db.String, nullable=True)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, name, access_level, description, **kwargs):
        self.name = name
        self.access_level = access_level
        self.description = description

    def __repr__(self):
        return '<Role: {0.name}>'.format(self)


class Group(RestrictionsMixin, SurrogatePK, Model):
    __tablename__ = 'groups'

    name = db.Column(db.String(255), nullable=False, unique=True)
    description = Column(db.String, nullable=True)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, name, description, **kwargs):
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Group: {0.name}>'.format(self)


class Tag(SurrogatePK, Model):
    value = Column(db.String, nullable=False, unique=True)

    nodes = relationship(
        "Node",
        secondary=node_tags,
        back_populates="tags",
    )

    packs = relationship(
        "Pack",
        secondary=pack_tags,
        back_populates="tags",
    )

    queries = relationship(
        "Query",
        secondary=query_tags,
        back_populates="tags",
    )

    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, value, **kwargs):
        self.value = value

    def __repr__(self):
        return "<Tag: {0.value}>".format(self)

    @property
    def packs_count(self):
        return db.session.object_session(self).query(Pack.id).with_parent(self, "packs").count()

    @property
    def nodes_count(self):
        return db.session.object_session(self).query(Node.id).with_parent(self, "nodes").count()

    @property
    def queries_count(self):
        return db.session.object_session(self).query(Query.id).with_parent(self, "queries").count()

    def to_dict(self):
        return self.value


class Query(SurrogatePK, Model):
    name = Column(db.String, nullable=False)
    sql = Column(db.String, nullable=False)
    interval = Column(db.Integer, default=3600)
    platform = Column(db.String, default='all')
    version = Column(db.String)
    description = Column(db.String)
    value = Column(db.String)
    removed = Column(db.Boolean, nullable=False, default=False)
    snapshot = Column(db.Boolean, nullable=False, default=False)
    shard = Column(db.Integer)

    packs = relationship(
        "Pack",
        secondary=querypacks,
        back_populates="queries",
    )

    tags = relationship(
        "Tag",
        secondary=query_tags,
        back_populates="queries",
        lazy="joined",
    )
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(
        self,
        name,
        query=None,
        sql=None,
        interval=3600,
        platform=None,
        version=None,
        description=None,
        value=None,
        removed=False,
        shard=None,
        snapshot=False,
        **kwargs
    ):
        self.name = name
        self.sql = query or sql
        self.interval = int(interval)
        self.platform = platform
        if not self.platform:
            self.platform = 'all'
        self.version = version
        self.description = description
        self.value = value
        self.removed = removed
        self.snapshot = snapshot
        self.shard = shard


    def __repr__(self):
        return "<Query: {0.name}>".format(self)

    def to_dict(self):
        return {
            "id": self.id,
            "query": self.sql,
            "interval": self.interval,
            "platform": self.platform,
            "version": self.version,
            "description": self.description,
            "value": self.value,
            "removed": self.removed,
            "shard": self.shard,
            "snapshot": self.snapshot,
            "tags": [r.to_dict() for r in self.tags],
        }


class VirusTotalAvEngines(SurrogatePK, Model):
    name = Column(db.String, nullable=False)
    status = Column(db.Boolean, nullable=False, default=False)
    description = Column(db.String, nullable=True)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, name, status, description=None):
        self.name = name
        self.status = status
        self.description = description


class NodeQueryCount(SurrogatePK, Model):
    node_id = Column(db.Integer, nullable=False)
    query_name = Column(db.String)
    event_id = Column(db.String, nullable=True)
    total_results = Column(db.Integer, default=0, nullable=False)
    date = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow())


class DefaultQuery(SurrogatePK, Model):
    name = Column(db.String, nullable=False)
    sql = Column(db.String, nullable=False)
    interval = Column(db.Integer, default=3600)
    version = Column(db.String)
    description = Column(db.String)
    value = Column(db.String)
    removed = Column(db.Boolean, nullable=False, default=True)
    snapshot = Column(db.Boolean, nullable=False, default=False)
    shard = Column(db.Integer)
    status = Column(db.Boolean, nullable=False, default=False)
    config_id = reference_col('config', nullable=True)
    config = relationship(
        'Config',
        backref=db.backref('default_query', lazy='dynamic')
    )
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, name, query=None, sql=None, interval=3600,
                 version=None, description=None, value=None, removed=False, config_id=None,
                 shard=None, status=None, snapshot=False, **kwargs):
        self.name = name
        self.sql = query or sql
        self.interval = int(interval)
        self.version = version
        self.description = description
        self.value = value
        self.removed = removed
        self.snapshot = snapshot
        self.shard = shard
        self.status = status
        self.config_id = config_id

    def __repr__(self):
        return "<Query: {0.name}>".format(self)

    def to_dict(self):
        to_return = {
            "id": self.id,
            "query": self.sql,
            "interval": self.interval,
            "version": self.version,
            "description": self.description,
            "value": self.value,
            "removed": False,
            "shard": self.shard,
            "snapshot": self.snapshot,
            "status": self.status
        }
        if self.name == 'windows_real_time_events':
            to_return['blacklist'] = False
            to_return['denylist'] = False
        return to_return

class DefaultFilters(SurrogatePK, Model):
    filters = Column(JSONB)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    config_id = reference_col('config', nullable=False)
    config = relationship(
        'Config',
        backref=db.backref('default_filters', lazy='dynamic')
    )

    def __init__(self, filters, config_id=None, **kwargs):
        self.filters = filters
        self.config_id = config_id

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'filters': json.loads(self.filters),
            'created_at': dump_datetime(self.created_at),
            'updated_at': dump_datetime(self.updated_at)
        }


class Config(SurrogatePK, Model):
    name = Column(db.String)
    platform = Column(db.String)
    description = Column(db.String)
    conditions = Column(JSONB)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    is_default = Column(db.Boolean, default=False, nullable=True)

    def __init__(
        self,
        name,
        platform,
        is_default=False,
        conditions=None,
        description=None,
        **kwargs
    ):
        self.platform = platform
        self.name = name
        self.is_default = is_default
        self.conditions = conditions
        self.description = description


class Pack(SurrogatePK, Model):
    INTRUSION_DETECTION = "Intrusion Detection"
    MONITORING = "Monitoring"

    COMPLIANCE_MANAGEMENT = "Compliance and Management"
    FORENSICS_IR = "Forensics and Incident Response"
    GENERAL = "General"
    OTHERS = "Others"

    name = Column(db.String, nullable=False, unique=True)
    platform = Column(db.String)
    version = Column(db.String)
    description = Column(db.String)
    shard = Column(db.Integer)
    category = Column(db.String, default=GENERAL)

    queries = relationship(
        "Query",
        secondary=querypacks,
        back_populates="packs",
    )

    tags = relationship(
        "Tag",
        secondary=pack_tags,
        back_populates="packs",
    )
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, name, platform=None, version=None, description=None, shard=None, **kwargs):
        self.name = name
        self.platform = platform
        self.version = version
        self.description = description
        self.shard = shard


    def __repr__(self):
        return "<Pack: {0.name}>".format(self)

    def to_dict(self):
        queries = {}
        discovery = []

        for query in self.queries:
            if "discovery" in (t.value for t in query.tags):
                discovery.append(query.sql)
            else:
                queries[query.name] = query.to_dict()

        return {
            "id": self.id,
            "platform": self.platform,
            "version": self.version,
            "shard": self.shard,
            "discovery": discovery,
            "queries": queries,
            "name": self.name,
            "tags": [r.to_dict() for r in self.tags],
        }


class Node(SurrogatePK, Model):

    ACTIVE = 0
    REMOVED = 1
    DELETED = 2

    NA = 0
    DISABLE = 1
    ENABLE = 2
    node_key = Column(db.String, nullable=False, unique=True)
    platform = Column(db.String)
    enroll_secret = Column(db.String)
    enrolled_on = Column(db.DateTime)
    host_identifier = Column(db.String)
    last_checkin = Column(db.DateTime)
    node_info = Column(JSONB, default={}, nullable=False)
    os_info = Column(JSONB, default={}, nullable=False)
    network_info = Column(JSONB, default={}, nullable=False)
    host_details = Column(JSONB, default={}, nullable=False)
    state = Column(db.Integer, default=ACTIVE, nullable=True)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    last_status = Column(db.DateTime)
    last_result = Column(db.DateTime)
    last_config = Column(db.DateTime)
    last_query_read = Column(db.DateTime)
    last_query_write = Column(db.DateTime)

    is_active = Column(db.Boolean, default=False, nullable=False)
    last_ip = Column(INET, nullable=True)

    tags = relationship(
        "Tag",
        secondary=node_tags,
        back_populates="nodes",
        lazy="joined",
    )

    def __init__(self, host_identifier, node_key=None,
                 enroll_secret=None, enrolled_on=None, last_checkin=None,
                 is_active=False, last_ip=None, last_status=None, network_info=None, os_info=None,
                 node_info=None, last_result=None, last_config=None, last_query_read=None, last_query_write=None,
                 state=None,  **kwargs):
        self.network_info = network_info
        self.node_info = node_info
        self.os_info = os_info
        self.node_key = node_key or str(uuid.uuid4())
        self.host_identifier = host_identifier
        self.enroll_secret = enroll_secret
        self.enrolled_on = enrolled_on
        self.last_checkin = last_checkin
        self.is_active = is_active
        self.last_ip = last_ip
        self.last_status = last_status
        self.last_result = last_result
        self.last_config = last_config
        self.last_query_read = last_query_read
        self.last_query_write = last_query_write
        self.state = state

    def __repr__(self):
        return "<Node-{0.id}: node_key={0.node_key}, host_identifier={0.host_identifier}>".format(self)

    def get_platform(self):
        from polylogyx.constants import DEFAULT_PLATFORMS
        platform = self.platform
        if platform not in DEFAULT_PLATFORMS:
            platform = "linux"
        return platform

    def get_config(self, **kwargs):
        from polylogyx.utils.config import assemble_configuration

        return assemble_configuration(self)

    def get_new_queries(self, **kwargs):
        from polylogyx.utils.config import assemble_distributed_queries

        return assemble_distributed_queries(self.id)

    def node_is_active(self):
        from polylogyx.utils.cache import get_a_host
        host_dict = get_a_host(node_key=self.node_key)
        if host_dict and host_dict.get('last_checkin'):
            last_checkin = dt.datetime.strptime(host_dict.get('last_checkin'), "%Y-%m-%d %H:%M:%S.%f")
        else:
            last_checkin = self.last_checkin
        checkin_interval = current_app.config["POLYLOGYX_CHECKIN_INTERVAL"]
        if isinstance(checkin_interval, (int, float)):
            checkin_interval = dt.timedelta(seconds=checkin_interval)
        if (dt.datetime.utcnow() - last_checkin) < checkin_interval:
            return True
        return False

    @property
    def display_name(self):
        if self.node_info:
            if "display_name" in self.node_info and self.node_info["display_name"]:
                return self.node_info["display_name"]
            elif "hostname" in self.node_info and self.node_info["hostname"]:
                return self.node_info["hostname"]
            elif "computer_name" in self.node_info and self.node_info["computer_name"]:
                return self.node_info["computer_name"]
            else:
                return self.host_identifier
        return self.host_identifier

    @property
    def packs(self):
        return (
            db.session.object_session(self)
            .query(Pack)
            .join(pack_tags, pack_tags.c["pack.id"] == Pack.id)
            .join(node_tags, node_tags.c["tag.id"] == pack_tags.c["tag.id"])
            .filter(node_tags.c["node.id"] == self.id)
            .options(db.lazyload("*"))
        )

    @property
    def queries(self):
        return (
            db.session.object_session(self)
            .query(Query)
            .join(query_tags, query_tags.c["query.id"] == Query.id)
            .join(node_tags, node_tags.c["tag.id"] == query_tags.c["tag.id"])
            .filter(node_tags.c["node.id"] == self.id)
            .options(db.lazyload("*"))
        )

    @hybrid_property
    def child_count(self):
        return db.session.query(db.func.count(DistributedQueryTask.id))\
            .filter(DistributedQueryTask.node_id == self.id, DistributedQueryTask.viewed_at == None,
                    DistributedQueryTask.status == DistributedQueryTask.COMPLETE).scalar()

    def to_dict(self):
        # NOTE: deliberately not including any secret values in here, for now.
        if self.network_info is None:
            self.network_info = {}
        if self.os_info is None:
            self.os_info = {}
        if self.node_info is None:
            self.node_info = {}
        return {
            "id": self.id,
            "display_name": self.display_name,
            "enrolled_on": self.enrolled_on,
            "host_identifier": self.host_identifier,
            "last_checkin": self.last_checkin,
            "platform": self.platform,
            "os_info": self.os_info.copy(),
            "node_info": self.node_info.copy(),
            "network_info": self.network_info.copy(),
            "last_ip": self.last_ip,
            "is_active": self.is_active or self.node_is_active(),
        }

    def as_dict(self):
        dictionary = {}
        for c in self.__table__.columns:
            if not (c.name == "enrolled_on" or c.name == "last_checkin"):
                dictionary[c.name] = getattr(self, c.name)
            else:
                if not getattr(self, c.name) is None:
                    dictionary[c.name] = getattr(self, c.name).strftime("%m/%d/%Y %H/%M/%S")
        return dictionary


class NodeConfig(SurrogatePK, Model):
    config_id = db.Column(db.Integer, db.ForeignKey("config.id", ondelete="CASCADE"))
    node_id = db.Column(db.Integer, db.ForeignKey("node.id", ondelete="CASCADE"))
    node = relationship("Node", backref=db.backref("node_config", passive_deletes=True, lazy="dynamic"))
    config = relationship(
        "Config",
        backref=db.backref("node_config", passive_deletes=True, lazy="dynamic"),
    )
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, config=None, config_id=None, node=None, node_id=None):
        if config:
            self.config = config
        if config_id:
            self.config_id = config_id
        if node:
            self.node = node
        if node_id:
            self.node_id = node_id


class ResultLog(SurrogatePK, Model):
    NEW = 0
    PENDING = 1
    COMPLETE = 2
    name = Column(db.String, nullable=False)
    timestamp = Column(db.DateTime, default=dt.datetime.utcnow)
    created_at=Column(db.DateTime, default=dt.datetime.utcnow)
    action = Column(db.String)
    columns = Column(JSONB)
    node_id = reference_col("node", nullable=False)
    node = relationship(
        "Node",
        backref=db.backref("result_logs", cascade="all, delete-orphan", lazy="dynamic"),
    )
    uuid = Column(db.String, nullable=True)
    status = Column(db.Integer, default=NEW, nullable=False)
    task_id = Column(db.String, nullable=True)
    result_log_scans = relationship(
        "ResultLogScan",
        secondary=result_log_maps,
        back_populates="result_logs",
        lazy="joined",
    )

    def __init__(
        self, name=None, action=None, columns=None, timestamp=None, node=None, node_id=None, uuid=None, **kwargs
    ):
        self.name = name
        self.action = action
        self.columns = columns or {}
        self.timestamp = timestamp
        self.uuid = uuid
        if node:
            self.node = node
        elif node_id:
            self.node_id = node_id

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def to_dict(self):
        dictionary = {}
        for c in self.__table__.columns:
            if not c.name == "timestamp":
                dictionary[c.name] = getattr(self, c.name)
            else:
                dictionary[c.name] = getattr(self, c.name).strftime("%m/%d/%Y %H/%M/%S")
        return dictionary


class AlertLog(SurrogatePK, Model):
    name = Column(db.String, nullable=False)
    timestamp = Column(db.DateTime, default=dt.datetime.utcnow)
    action = Column(db.String)
    columns = Column(JSONB)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id", ondelete="CASCADE"))
    result_log_uuid = Column(db.String, nullable=True)

    def __init__(
        self,
        name=None,
        action=None,
        columns=None,
        timestamp=None,
        alert_id=None,
        result_log_uuid=None,
    ):
        self.name = name
        self.action = action
        self.columns = columns or {}
        self.timestamp = timestamp
        self.alert_id = alert_id
        self.result_log_uuid = result_log_uuid

    def to_dict(self):
        dictionary = {}
        for c in self.__table__.columns:
            if not c.name == "timestamp":
                dictionary[c.name] = getattr(self, c.name)
            else:
                dictionary[c.name] = getattr(self, c.name).strftime("%d-%m-%Y %H:%M:%S.%f")
        return dictionary

    @declared_attr
    def __table_args__(cls):
        return (
            Index("idx_%s_name" % cls.__tablename__, "name"),
            Index("idx_%s_result_log_uuid" % cls.__tablename__, "result_log_uuid"),
            Index("idx_%s_alert_id" % cls.__tablename__, "alert_id"),
        )


class StatusLog(SurrogatePK, Model):
    line = Column(db.Integer)
    message = Column(db.String)
    severity = Column(db.Integer)
    filename = Column(db.String)
    created = Column(db.DateTime, default=dt.datetime.utcnow)
    version = Column(db.String)

    node_id = reference_col("node", nullable=False)
    node = relationship(
        "Node",
        backref=db.backref("status_logs", cascade="all, delete-orphan", lazy="dynamic"),
    )

    def __init__(
        self,
        line=None,
        message=None,
        severity=None,
        filename=None,
        created=None,
        node=None,
        node_id=None,
        version=None,
        **kwargs
    ):
        self.line = int(line)
        self.message = message
        self.severity = int(severity)
        self.filename = filename
        self.created = created
        self.version = version
        if node:
            self.node = node
        elif node_id:
            self.node_id = node_id

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                "idx_%s_node_id_created_desc" % cls.__tablename__,
                "node_id",
                cls.created.desc(),
            ),
        )


class DistributedQuery(SurrogatePK, Model):
    description = Column(db.String, nullable=True)
    sql = Column(db.String, nullable=False)
    not_before = Column(db.DateTime, default=dt.datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True, default=None)
    owner = relationship(
        'User',
        # backref=db.backref('user', lazy='dynamic')
    )
    owner_permissions = db.Column(db.Text, nullable=True)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    # tasks = relationship(
    #     'DistributedQueryTask',
    #     backref=db.backref('distributed_query_task'),
    #
    # )

    def __init___(self, sql, description=None, not_before=None):
        self.sql = sql
        self.description = description
        self.not_before = not_before

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class DistributedQueryTask(SurrogatePK, Model):
    NEW = 0
    PENDING = 1
    COMPLETE = 2
    FAILED = 3
    NOT_SENT = 4
    HIGH = 0

    LOW = 1

    save_results_in_db = Column(db.Boolean, nullable=False, default=False)
    guid = Column(db.String, nullable=False, unique=True)
    status = Column(db.Integer, default=0, nullable=False)
    data = Column(JSONB)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    viewed_at = Column(db.DateTime, nullable=True, default=None)
    priority = Column(db.Integer, default=0, nullable=False)

    distributed_query_id = reference_col("distributed_query", nullable=False)
    distributed_query = relationship(
        "DistributedQuery",
        backref=db.backref("tasks", cascade="all, delete-orphan", lazy="dynamic"),
    )

    node_id = db.Column(db.Integer, db.ForeignKey("node.id", ondelete="CASCADE"))
    node = relationship(
        "Node",
        backref=db.backref("distributed_queries", passive_deletes=True, lazy="dynamic"),
    )

    def __init__(
        self,
        node=None,
        node_id=None,
        distributed_query=None,
        save_results_in_db=False,
        distributed_query_id=None,
        priority=0,
        viewed_at=None,
        data=None,
    ):
        self.guid = str(uuid.uuid4())
        
        self.viewed_at = viewed_at
        self.save_results_in_db = save_results_in_db
        self.data = data
        self.priority = priority
        if node:
            self.node = node
        elif node_id:
            self.node_id = node_id
        if distributed_query:
            self.distributed_query = distributed_query
        elif distributed_query_id:
            self.distributed_query_id = distributed_query_id

    @declared_attr
    def __table_args__(cls):
        return (Index("idx_%s_node_id_status" % cls.__tablename__, "node_id", "status"),)

    def to_dict_obj(self):
        return {
            "id": self.id,
            "distributed_query": {
                "description": self.distributed_query.description,
                "sql": self.distributed_query.sql,
            },
            "results": self.data,
        }


class Rule(Model, SurrogatePK):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    INFO = "INFO"
    LOW = "LOW"

    MITRE = "MITRE"
    DEFAULT = "DEFAULT"

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    name = Column(db.String, nullable=False)
    alerters = Column(ARRAY(db.String), nullable=False)
    description = Column(db.String, nullable=True)
    severity = Column(db.String, nullable=True)
    platform = Column(db.String, nullable=True)
    conditions = Column(JSONB)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    status = Column(db.String, nullable=True)
    type = Column(db.String, nullable=True, default=DEFAULT)
    technique_id = Column(db.String, nullable=True)
    tactics = Column(ARRAY(db.String), nullable=True)
    alert_description = Column(db.Boolean, nullable=True, default=False)

    def __init__(
        self,
        name,
        alerters,
        description=None,
        conditions=None,
        status="ACTIVE",
        severity=None,
        type=None,
        technique_id=None,
        tactics=[],
        platform=None,
        alert_description=False,
    ):
        self.name = name
        self.description = description
        self.alerters = alerters
        self.conditions = conditions
        self.status = status
        self.severity = severity
        self.type = type
        self.technique_id = technique_id
        self.tactics = tactics
        self.platform = platform
        self.alert_description = alert_description

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def as_dict(self):
        dictionary = {}
        for c in self.__table__.columns:
            if not c.name == "updated_at":
                dictionary[c.name] = getattr(self, c.name)
            else:
                dictionary[c.name] = getattr(self, c.name).strftime("%m/%d/%Y %H/%M/%S")
        return dictionary

    @property
    def template(self):
        return string.Template("{name}\r\n\r\n{description}".format(name=self.name, description=self.description or ""))


class Alerts(SurrogatePK, Model):

    RULE = "rule"
    THREAT_INTEL = "Threat Intel"
    SOURCE_IOC = "IOC"
    RESOLVED = "RESOLVED"
    OPEN = "OPEN"

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    INFO = "INFO"
    LOW = "LOW"

    NA = 0
    TRUE_POSITIVE = 1
    FALSE_POSITIVE = 2

    query_name = Column(db.String, nullable=False)
    message = Column(JSONB)

    rule_id = reference_col("rule", nullable=True)
    rule = relationship(
        "Rule",
        backref=db.backref("alerts", lazy="dynamic"),
    )

    node_id = reference_col("node", nullable=False)
    node = relationship(
        "Node",
        backref=db.backref("alerts", cascade="all, delete-orphan", lazy="dynamic"),
    )

    severity = Column(db.String, nullable=True)
    type = Column(db.String, nullable=True)
    result_log_uid = Column(db.String)
    source = Column(db.String)
    source_data = Column(JSONB)
    status = Column(db.String, default=OPEN)
    verdict = Column(db.Integer, default=NA)
    comment = Column(db.Text, nullable=True)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(
        self,
        message,
        query_name,
        node_id,
        rule_id,
        result_log_uid,
        type,
        source,
        source_data,
        severity,
    ):
        self.message = message
        self.query_name = query_name
        self.node_id = node_id
        self.rule_id = rule_id
        self.type = type
        self.source = source
        self.source_data = source_data
        self.result_log_uid = result_log_uid
        self.severity = severity

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def as_dict(self):
        dictionary = {}
        for c in self.__table__.columns:
            if not c.name == "created_at":
                dictionary[c.name] = getattr(self, c.name)
            else:
                dictionary[c.name] = getattr(self, c.name).strftime("%m/%d/%Y %H/%M/%S")
        return dictionary

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                "idx_%s_created_at_desc" % cls.__tablename__,
                "created_at",
                cls.created_at.desc(),
            ),
            Index("idx_%s_status" % cls.__tablename__, "status"),
        )


class Settings(SurrogatePK, Model):
    # config = Column(JSONB)
    setting = Column(db.String, nullable=False)
    name = Column(db.String, nullable=False)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, name, setting, **kwargs):
        self.name = name
        self.setting = setting


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return value.strftime("%Y-%m-%d") + " " + value.strftime("%H:%M:%S")


class CarveSession(SurrogatePK, Model):
    # StatusQueried for queried carves that did not hit nodes yet
    StatusQueried = "QUERIED"
    # StatusInitialized for initialized carves
    StatusInitialized = "INITIALIZED"
    # StatusInProgress for carves that are on-going
    StatusInProgress = "IN PROGRESS"
    #  StatusCompleted for carves that finalized
    StatusBuilding = "BUILDING"
    #  StatusCompleted for carves that finalized
    StatusCompleted = "COMPLETED"

    session_id = Column(db.String, nullable=False)
    carve_guid = Column(db.String, nullable=False)

    carve_size = Column(db.Integer)
    block_size = Column(db.Integer)
    block_count = Column(db.Integer)
    completed_blocks = Column(db.Integer, default=0)
    archive = Column(db.String())

    request_id = Column(db.String, nullable=False)
    status = Column(db.String, nullable=False)

    node_id = db.Column(db.Integer, db.ForeignKey("node.id", ondelete="CASCADE"))
    node = relationship(
        "Node",
        backref=db.backref("carve_session", passive_deletes=True, lazy="dynamic"),
    )

    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init___(self, node_id, session_id=None, carve_guid=None, carve_size=0, block_size=0, block_count=0,
                  archive=None, request_id=None):
        self.node_id = node_id
        self.session_id = session_id
        self.carve_guid = carve_guid
        self.carve_size = carve_size
        self.block_size = block_size
        self.block_count = block_count
        self.archive = archive
        self.request_id = request_id


    def to_dict(self):
        """Return object data in easily serializeable format"""
        return {
            "id": self.id,
            "node_id": self.node_id,
            "session_id": self.session_id,
            "carve_guid": self.carve_guid,
            "carve_size": self.carve_size,
            "block_count": self.block_count,
            "archive": self.archive,
            "created_at": dump_datetime(self.created_at),
        }


class CarvedBlock(SurrogatePK, Model):
    request_id = Column(db.String, nullable=False)
    session_id = Column(db.String, nullable=False)
    block_id = Column(db.Integer, nullable=False)
    data = Column(db.String, nullable=False)
    size = Column(db.Integer, nullable=False)

    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init___(self, request_id=None, session_id=None, block_id=None, data=None, size=None):
        self.request_id = request_id
        self.session_id = session_id
        self.block_id = block_id
        self.data = data
        self.size = size


class AlertEmail(SurrogatePK, Model):
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id", ondelete="CASCADE"))
    alert = relationship(
        "Alerts",
        backref=db.backref("alert_email", lazy="dynamic", passive_deletes=True),
    )
    status = Column(db.String, nullable=True)
    node_id = db.Column(db.Integer, db.ForeignKey("node.id", ondelete="CASCADE"))
    node = relationship("Node", backref=db.backref("alert_email", passive_deletes=True, lazy="dynamic"))
    body = Column(db.String, nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    def __init__(self, node=None, node_id=None, alert=None, alert_id=None, body=None, status=None):
        if node:
            self.node = node
        elif node_id:
            self.node_id = node_id
        if alert:
            self.alert = alert
        elif alert_id:
            self.alert_id = alert_id
        self.body = body
        self.status = status


class ResultLogScan(SurrogatePK, Model):
    scan_type = Column(db.String, nullable=False)
    scan_value = Column(db.String, nullable=False)
    reputations = Column(JSONB, default={}, nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    vt_updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    result_logs = relationship(
        'ResultLog',
        secondary=result_log_maps,
        back_populates='result_log_scans',
    )

    def __init__(self, scan_type, scan_value, reputations, **kwargs):
        self.scan_type = scan_type
        self.scan_value = scan_value
        self.reputations = reputations

    @declared_attr
    def __table_args__(cls):
        return (Index("idx_%s_scan_value" % cls.__tablename__, "scan_value"),)


class IOCIntel(SurrogatePK, Model):
    type = Column(db.String, nullable=True)
    intel_type = Column(db.String, nullable=False)
    value = Column(db.String, nullable=False)
    threat_name = Column(db.String, nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    severity = Column(db.String, nullable=False, default="")

    def __init__(self, type, value, threat_name, intel_type, severity, **kwargs):
        self.type = type
        self.intel_type = intel_type
        self.value = value
        self.threat_name = threat_name
        self.severity = severity


class ThreatIntelCredentials(SurrogatePK, Model):
    intel_name = Column(db.String, nullable=True)
    credentials = Column(JSONB, default={}, nullable=False)
    created_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=True, default=dt.datetime.utcnow)

    def __init__(self, intel_name, credentials, **kwargs):
        self.intel_name = intel_name
        self.credentials = credentials


class AuthToken(SurrogatePK, Model):
    token = Column(db.String, nullable=False)
    logged_in_at = Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)
    token_expired = Column(db.Boolean, nullable=False, default=False)
    logged_out_at = Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    user = relationship('User',)

    def __init__(self, token=None, logged_in_at=None, user_id=None, logged_out_at=None, token_expired=None):
        self.token = token
        self.user_id = user_id
        self.logged_in_at = logged_in_at
        self.logged_out_at = logged_out_at
        self.token_expired = token_expired


class OsquerySchema(SurrogatePK, Model):
    name = Column(db.String, nullable=False)
    platform = Column(ARRAY(db.String), nullable=False)
    schema = Column(JSONB, default={}, nullable=False)
    description = Column(db.String, nullable=True)

    def __init__(self, name=None, platform=None, schema=None, description=None, **kwargs):
        self.platform = platform
        self.name = name
        self.schema = schema
        self.description = description


class DownloadCsvExport(SurrogatePK, Model):
    name = Column(db.String, nullable=False)
    task_id = Column(db.String, nullable=False)
    status = Column(db.String, nullable=False)
    description = Column(db.String, nullable=True)

    def __init__(self, name=None, task_id=None, status=None, description=None, **kwargs):
        self.name = name
        self.task_id = task_id
        self.status = status
        self.description = description


class PlatformActivity(SurrogatePK, Model):
    action = Column(db.String, nullable=True)
    text = Column(db.String, nullable=True)
    entity = Column(db.String, nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    user = relationship(
        'User',
    )
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)

    def __init__(self, action=None, user_id=None, entity_id=None, entity=None, text=None):
        self.action = action
        self.text = text
        self.user_id = user_id
        self.entity = entity
        self.entity_id = entity_id


class AnalystNotes(SurrogatePK, Model):
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    notes = Column(db.Text)
    alerts_id = db.Column(db.Integer, db.ForeignKey('alerts.id', ondelete='CASCADE'))
    alerts = relationship(
        'Alerts',
        backref=db.backref('analyst_notes', passive_deletes=True, lazy='dynamic')
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    user = relationship(
        'User',
        backref=db.backref('analyst_notes', passive_deletes=True, lazy='dynamic')
    )

    def __init__(self, alerts_id, notes, user_id, **kwargs):
        self.alerts_id = alerts_id
        self.notes = notes
        self.user_id = user_id


class ContainerMetrics(SurrogatePK, Model):
    container_name = Column(db.String, nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    unit = Column(db.String, nullable=True) # file used for analysys
    data = Column(JSONB, default={}, nullable=False)
    file = Column(db.String, nullable=True) # file used for analysys
    
    def __init__(self, container_name,data={},unit=None,created_at=None,file=None):
        self.container_name 	=	container_name 
        self.unit 	=	unit 
        self.data 	=	data 
        self.file 	=	file 
        self.created_at =created_at or dt.datetime.utcnow()


# Signals Section

from polylogyx.db.signals import receive_after_update, receive_after_delete, receive_after_insert


watch_for = {
    'insert': [Rule, Node, Settings],
    'update': [Rule, Node, Settings],
    'delete': [Rule, Node, Settings]
    }

for kls in watch_for['insert']:
    event.listen(kls, 'after_insert', receive_after_insert)

for kls in watch_for['update']:
    event.listen(kls, 'after_update', receive_after_update)

for kls in watch_for['delete']:
    event.listen(kls, 'after_delete', receive_after_delete)

# Signals Section