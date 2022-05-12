# -*- coding: utf-8 -*-
import base64
import os
import datetime as dt
import sqlalchemy
from sqlalchemy import or_, text, desc, and_, cast, not_
from celery import Celery
from flask import current_app, json
from kombu import Exchange, Queue

from polylogyx.models import Settings, AlertEmail, Node, ResultLog, StatusLog, db, Alerts, CarveSession, \
    DistributedQueryTask, NodeQueryCount, AlertLog
from polylogyx.constants import PolyLogyxServerDefaults

celery = Celery(__name__)

celery.conf.update(
    worker_pool_restarts=True,
)
celery.conf.beat_schedule = {
    "send-alert-emails": {
        "task": "polylogyx.tasks.send_alert_emails",
        "schedule": 85451.0 #86400 old - 949 sec
    }, "purge_old_data": {
        "task": "polylogyx.tasks.purge_old_data",
        "schedule": 87121.0   #86400 old + 12 min 3 sec
    },
    "purge_status_log": {
        "task": "polylogyx.tasks.purge_status_log",
        "schedule": 21757.0
    },
    "collect_metrics": {
        "task": "polylogyx.tasks.collect_metrics",
        "schedule": 3600.0 
    },
    "purge_metrics": {
        "task": "polylogyx.tasks.purge_metrics",
        "schedule": 88321.0  #86400 old + 31 min 
    }
}


def update_sender_email(db):
    email_sender_obj = db.session.query(Settings).filter(
        Settings.name == PolyLogyxServerDefaults.plgx_config_all_settings).first()
    if not email_sender_obj:
        current_app.logger.info("Email credentials are not set..")
        return False
    try:
        settings = json.loads(email_sender_obj.setting)
        current_app.config['EMAIL_RECIPIENTS'] = settings['emailRecipients']
        current_app.config['MAIL_USERNAME'] = settings['email']
        current_app.config['MAIL_PASSWORD'] = base64.decodestring(settings['password'].encode('utf-8')).decode('utf-8')
        current_app.config['MAIL_SERVER'] = settings['smtpAddress']
        current_app.config['MAIL_PORT'] = int(settings['smtpPort'])
        current_app.config['MAIL_USE_SSL'] = settings['use_ssl']
        current_app.config['MAIL_USE_TLS'] = settings['use_tls']
        return True
    except Exception as e:
        current_app.logger.info("Incomplete email credentials")
        current_app.logger.error(e)
        return False


@celery.task()
def send_alert_emails():
    from polylogyx.models import db
    current_app.logger.info("Task is started to send the pending emails of the alerts reported")
    email_credentials_valid = update_sender_email(db)
    if email_credentials_valid:
        nodes = Node.query.all()
        for node in nodes:
            try:
                send_pending_node_emails(node, db)
                current_app.logger.info("Pending emails of the alerts reported are sent")
            except Exception as e:
                current_app.logger.error(str(e))
    current_app.logger.info("Task is completed in sending the pending emails of the alerts reported")


@celery.task()
def purge_old_data(days=None):
    from polylogyx import db
    import time, datetime
    from time import strptime

    current_app.logger.info("Task to purge older data is started")
    try:
        deleted_hosts = Node.query.filter(Node.state == Node.DELETED).all()
        node_ids_to_delete = [node.id for node in deleted_hosts if
                              not node.result_logs.count() and not node.status_logs.count()]
        if node_ids_to_delete:
            permanent_host_deletion.apply_async(args=[node_ids_to_delete])

        delete_setting = Settings.query.filter(Settings.name == 'data_retention_days').first()
        current_app.logger.info("Purging the data for the duration {}".format(int(delete_setting.setting)))

        if (delete_setting and int(delete_setting.setting) > 0) or days:
            if days:
                since = dt.datetime.now() - dt.timedelta(hours=24 * (int(days)))  #PFM-3203 Manual - Purge data basis of retention
                drop_date = datetime.date.today() - dt.timedelta(hours=24 * (int(days)))
            else:
                #since = datetime.date.today() - dt.timedelta(hours=24 * int(int(delete_setting.setting)))
                since = dt.datetime.now() - dt.timedelta(hours=24 * int(delete_setting.setting))
                drop_date = datetime.date.today() - dt.timedelta(hours=24 * (int(delete_setting.setting)))
                   
            try:
                partition_query = db.session.execute("""SELECT
                        child.relname       AS partition_name
                    FROM pg_inherits
                        JOIN pg_class parent            ON pg_inherits.inhparent = parent.oid
                        JOIN pg_class child             ON pg_inherits.inhrelid   = child.oid
                        JOIN pg_namespace nmsp_parent   ON nmsp_parent.oid  = parent.relnamespace
                        JOIN pg_namespace nmsp_child    ON nmsp_child.oid   = child.relnamespace
                    WHERE parent.relname='result_log';""")
                partitions = [row[0] for row in partition_query]
                for partition in partitions:
                    partition_date_string = partition.split("result_log_")[1].split("_")
                    month = strptime(partition_date_string[0], '%b').tm_mon
                    date = partition_date_string[1]
                    year = partition_date_string[2]
                    d = datetime.datetime(int(year), month, int(date))
                    partition_date = d.date()
                    if partition_date < drop_date:
                        db.session.execute("drop table " + partition + ";")
                        NodeQueryCount.query.filter(NodeQueryCount.date == partition_date).delete()
                        db.session.commit()
                        current_app.logger.info("Purged table {0}".format(partition))
                        time.sleep(2)
            except Exception as e:
                db.session.commit()
                current_app.logger.error("Error in Purge : {0}".format(e))
                # No more older data needs to be purged
            current_app.logger.info("Purging the Status Logs beyond the purge duration")
            StatusLog.query.filter(StatusLog.created < since).delete()
            db.session.commit()
            current_app.logger.info("Purging the Alerts beyond the purge duration")
            Alerts.query.filter(Alerts.created_at < since).delete()
            AlertLog.query.filter(AlertLog.timestamp < since).delete()
            db.session.commit()
            current_app.logger.info("Purging the Response actions  beyond the purge duration")
            db.session.commit()
            hosts = db.session.query(Node.host_identifier, Node.id).filter(Node.state == Node.DELETED).filter(
                Node.updated_at < since).all()
            node_ids = [item[1] for item in hosts]
            permanent_host_deletion.apply_async(args=[node_ids])
        else:
            current_app.logger.info("Deleting limit not set, skipping ")
        db.session.commit()
    except Exception as e:
        db.session.commit()
        current_app.logger.error(e)
    current_app.logger.info("Task to purge older data is completed")


@celery.task()
def purge_status_log():
    current_app.logger.info("Removing the Status Logs files beyond the 6 hours")
    since = dt.datetime.now() - dt.timedelta(hours=6)
    status_log_file_deletion(since)


@celery.task()
def permanent_host_deletion(node_ids):
    if node_ids:
        current_app.logger.info("Hosts with ids {} are requested to delete permanently".format(node_ids))
        try:
            nodes = db.session.query(Node).filter(Node.id.in_(node_ids)).all()
            for node in nodes:
                node.tags = []
            db.session.commit()

            deleted_count = Node.query.filter(Node.state == Node.DELETED).filter(Node.id.in_(node_ids)).delete(
                synchronize_session=False)
            current_app.logger.info("{} hosts are deleted permanently".format(deleted_count))
        except Exception as e:
            current_app.logger.error(
                "Unable to delete tags/result_log/status_log/alert_email/alerts from the node! " + str(e))
    else:
        current_app.logger.info("No host is requested to delete")
    db.session.commit()


def status_log_file_deletion(duration):
    from os import walk
    file_list = []
    for (dirpath, dirnames, filenames) in walk(current_app.config['BASE_URL'] + "/status_log/"):
        file_list.extend(filenames)
        break
    for file in file_list:
        created_at = dt.datetime.fromtimestamp(os.stat(current_app.config['BASE_URL'] + "/status_log/" + file).st_ctime)
        if created_at < duration:
            os.remove(current_app.config['BASE_URL'] + "/status_log/" + file)


def format_records(results):
    result_list = []
    keys = results.keys()

    data_list = results.fetchall()
    for data in data_list:
        result = {}
        for index, key in enumerate(keys):
            result[key] = data[index]
        result_list.append(result)
    return result_list


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        import decimal
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def send_pending_node_emails(node, db):
    from polylogyx.utils import send_mail
    alert_emails = AlertEmail.query.filter(AlertEmail.node == node).filter(AlertEmail.status == None).all()
    body = ''
    is_mail_sent = False
    for alert_email in alert_emails:
        body = body + alert_email.body
    if body:
        db.session.query(AlertEmail).filter(AlertEmail.status == None).filter(AlertEmail.node == node).update(
            {'status': 'PENDING'})
        db.session.commit()
        try:
            is_mail_sent = send_mail(app=current_app, content=body, subject=node.display_name + ' Alerts Today')
        except Exception as e:
            current_app.logger.error(str(e))
        if is_mail_sent:
            db.session.query(AlertEmail).filter(AlertEmail.status == 'PENDING').filter(
                AlertEmail.node == node).update(
                {'status': 'COMPLETED'})
        else:
            db.session.query(AlertEmail).filter(AlertEmail.status == 'PENDING').filter(
                AlertEmail.node == node).update(
                {'status': None})
        db.session.commit()


from polylogyx.dao.v1.metrics_dao import collect_rabbitmq_metrics,collect_postgres_metrics,collect_nginx_metrics

@celery.task()
def collect_metrics():
    collect_rabbitmq_metrics()
    collect_postgres_metrics()
    collect_nginx_metrics()

from polylogyx.models import ContainerMetrics
@celery.task()
def purge_metrics():
    current_app.logger.info("Removing the metrics data")
    since = dt.datetime.now() - dt.timedelta(hours=24)
    try:
        ContainerMetrics.filter(ContainerMetrics.created_at<since).delete()
        db.session.commit()
    except:
        db.session.rollback()
