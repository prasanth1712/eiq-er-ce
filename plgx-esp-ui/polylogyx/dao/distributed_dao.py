from polylogyx.models import DistributedQuery, DistributedQueryTask, db


def add_distributed_query(sql, description):
    return DistributedQuery.create(sql=sql,description=description)

def create_distributed_task_obj(node, query):
    return DistributedQueryTask(node=node, distributed_query=query)

def distributed_by_alertId(alert_id):
    return db.session.query(DistributedQueryTask) \
            .join(DistributedQuery) \
            .filter(
            DistributedQuery.alert_id == alert_id
        )