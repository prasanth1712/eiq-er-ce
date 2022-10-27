# -*- coding: utf-8 -*-
from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from polylogyx.db.database import db
from polylogyx.db.models import (Alerts, DistributedQuery,
                                 DistributedQueryTask,
                                 Node, Pack, Query, ResultLog, Rule,
                                 StatusLog, Tag, ResultLogScan)


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db.session


class NodeFactory(BaseFactory):
    class Meta:
        model = Node


class AlertFactory(BaseFactory):
    class Meta:
        model = Alerts


class PackFactory(BaseFactory):
    class Meta:
        model = Pack


class QueryFactory(BaseFactory):
    class Meta:
        model = Query


class TagFactory(BaseFactory):
    class Meta:
        model = Tag


class DistributedQueryFactory(BaseFactory):
    class Meta:
        model = DistributedQuery


class DistributedQueryTaskFactory(BaseFactory):
    class Meta:
        model = DistributedQueryTask


class ResultLogFactory(BaseFactory):
    class Meta:
        model = ResultLog


class ResultLogScanFactory(BaseFactory):
    class Meta:
        model = ResultLogScan


class StatusLogFactory(BaseFactory):
    class Meta:
        model = StatusLog


class RuleFactory(BaseFactory):
    class Meta:
        model = Rule
