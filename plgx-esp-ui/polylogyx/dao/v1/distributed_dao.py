from polylogyx.models import DistributedQuery, DistributedQueryTask, db
import datetime as dt


def add_distributed_query(sql, description):
    return DistributedQuery.create(sql=sql, description=description)


def create_distributed_task_obj(node, query):
    return DistributedQueryTask(node_id=node.id, distributed_query=query)

