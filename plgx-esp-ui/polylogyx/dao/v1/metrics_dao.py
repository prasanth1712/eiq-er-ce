import sqlalchemy

from polylogyx.dao import nodes_dao
from polylogyx.dao.v1 import hosts_dao
from polylogyx.models import ContainerMetrics,db,Node
from flask import current_app
import requests
from requests.auth import HTTPBasicAuth
from sqlalchemy import and_
import datetime as dt
import pandas as pd
import os


def get_files_for_analysis(container_name="NGINX"):
    log_file = current_app.config["POLYLOGYX_NGINX_METRIC_COLLECTION_LOGFILE"]
    current_time = dt.datetime.now()
    last_metric = ContainerMetrics.query.\
                    filter(ContainerMetrics.container_name==container_name)\
                    .order_by(ContainerMetrics.created_at.desc()).first()
    analysis_files = []

    # error.log-20220118
    if last_metric:
        last_analysed_datetime = str(last_metric.file).split(".log_")[1]
    else:
        last_analysed_datetime = dt.datetime.strftime(current_time,"%Y%m%d-%H")
    print(last_analysed_datetime)
    last_analysed_datetime = dt.datetime.strptime(last_analysed_datetime,"%Y%m%d-%H")
    while current_time >= last_analysed_datetime:
        
        temp = dt.datetime.strftime(last_analysed_datetime,"%Y%m%d-%H")
        temp = log_file+"_"+temp
        print(temp)
        if os.path.isfile(temp):
            analysis_files.append((temp,last_analysed_datetime))
        else:
            current_app.logger.info("dummy")
        last_analysed_datetime = last_analysed_datetime+dt.timedelta(hours=1)
    if not analysis_files:
        print("No files to analyse")


    return analysis_files
            

def collect_nginx_metrics():
    for v in get_files_for_analysis():
        f = v[0]
        t = v[1]
        try:
            res = {}
            df=pd.read_csv(f,delimiter="|",
                names=['remote_addr','remote_user','time_local','request','status','body_bytes_sent','http_referer','http_user_agent'])

            
            df=df[df["request"].astype(str).str.contains("/esp/")]
            res["total_count"]=int(df.shape[0])
            print("doing analysis")
            if res["total_count"]>0:
                res["success_count"] = int(df[df["status"]==200]["status"].count())
                res["failure_count"] = int(res["total_count"]-res["success_count"])
                res["total_size"]=int(df["body_bytes_sent"].sum())
                res["hour_avg"] = int(res["total_size"]/res["total_count"])
                g1 = df[["remote_addr","body_bytes_sent"]].groupby("remote_addr")
                gdf=g1.sum().sort_values('body_bytes_sent',ascending=False)[:5] # top 5 end points 
                gdf = gdf.to_dict()["body_bytes_sent"]
                top_5 = {}
                for k,v in gdf.items():
                    node=Node.query.with_entities(Node.host_identifier).filter(Node.last_ip==str(k).strip()).first()
                    if node:
                        top_5[node[0]]=int(v)
                    else:
                        top_5[str(k).strip()]=int(v)
                res["top_5_endpoints"]=top_5
                cm = ContainerMetrics("NGINX",res,None,t,f)
                cm.save()
            else:
                print("Size is 0")
            print("nginx analysis done")
        except Exception as e:
            print(e)
        finally:
            db.session.rollback()
    

def collect_postgres_metrics():
    try:
        query = "SELECT pg_size_pretty(pg_database_size('polylogyx'))"
        db_size = db.session.execute(query).first()[0]
        if db_size:
            val,unit = str(db_size).split(" ")
            cm = ContainerMetrics("POSTGRES",int(val),unit)
            cm.save()
    except Exception as e:
        current_app.logger.error(e)
    finally:
        db.session.rollback()

def collect_rabbitmq_metrics():
    try:
        rabbitmq_url = "http://{0}:{1}/api/".format(current_app.config["RABBITMQ_HOST"],current_app.config["RABBITMQ_MGMT_PORT"])
        overview_api_url = rabbitmq_url+'overview'
        resp = requests.get(url=overview_api_url,auth = HTTPBasicAuth(current_app.config["RABBITMQ_USERNAME"], current_app.config["RABBITMQ_PASSWORD"]))
        if resp.status_code==200:
            data = resp.json()
            filter_resp = ['message_stats', 'queue_totals', 'object_totals']
            data = {k:v for (k,v) in data.items() if k in filter_resp}
            cm = ContainerMetrics("RABBITMQ",data)
            cm.save()
    except Exception as e:
        current_app.logger.error(e)
    finally:
        db.session.rollback()


def get_metrics(container_name,from_time):
    try:
        cm = ContainerMetrics.query.filter(
            and_(ContainerMetrics.container_name==container_name,
            ContainerMetrics.created_at>=from_time)).order_by(sqlalchemy.desc(ContainerMetrics.created_at)).all()
    except Exception as e:
        print(e)

        pass
    finally:
        db.session.rollback()
    return cm

