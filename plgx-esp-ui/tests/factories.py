# -*- coding: utf-8 -*-
from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory

from polylogyx.database import db
from polylogyx.models import (
    Node, Pack, Query, Tag, FilePath,
    DistributedQuery, DistributedQueryTask, DistributedQueryResult,
    ResultLog, StatusLog, Rule, User, Alerts, DashboardData,
    CarveSession
)


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db.session


class NodeFactory(BaseFactory):

    class Meta:
        model = Node


class PackFactory(BaseFactory):

    class Meta:
        model = Pack


class QueryFactory(BaseFactory):

    class Meta:
        model = Query


class TagFactory(BaseFactory):

    class Meta:
        model = Tag


class FilePathFactory(BaseFactory):

    class Meta:
        model = FilePath


class DistributedQueryFactory(BaseFactory):

    class Meta:
        model = DistributedQuery


class DistributedQueryTaskFactory(BaseFactory):

    class Meta:
        model = DistributedQueryTask


class DistributedQueryResultFactory(BaseFactory):

    class Meta:
        model = DistributedQueryResult


class ResultLogFactory(BaseFactory):

    class Meta:
        model = ResultLog


class StatusLogFactory(BaseFactory):

    class Meta:
        model = StatusLog


class RuleFactory(BaseFactory):

    class Meta:
        model = Rule


class UserFactory(BaseFactory):

    class Meta:
        model = User


class AlertsFactory(BaseFactory):

    class Meta:
        model = Alerts


class DashboardDataFactory(BaseFactory):

    class Meta:
        model = DashboardData


class CarveSessionFactory(BaseFactory):

    class Meta:
        model = CarveSession
