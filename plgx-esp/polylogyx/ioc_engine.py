from polylogyx.constants import TO_CAPTURE_COLUMNS
from flask import current_app
import datetime as dt
import asyncio


class IOCEngine:

    # 1. Application initialization and attaching as a single instance
    def __init__(self,app=None):
        self.config_scan_cols = set(TO_CAPTURE_COLUMNS)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        app.ioc_engine = self
        self.ioc_matching = app.config.get("IOC_MATCHING",False)
        self.threat_intel_matching = app.config.get("THREAT_INTEL_MATCHING",False)

    def get_vt_setting(self):
        from polylogyx.utils.cache import get_a_setting
        vt_setting = get_a_setting('vt_scan_retention_period')
        if vt_setting is None:
            vt_setting = 60
        else:
            vt_setting = int(vt_setting)
        return vt_setting

    # 3. END

    async def process(self, node_id, data):
        from polylogyx.utils.cache import load_cached_iocs
        if not self.ioc_matching and not self.threat_intel_matching:
            return

        if self.ioc_matching:
            iocs = load_cached_iocs()
            ioc_types = iocs.keys()
            ioc_alerts = []
        
        if self.threat_intel_matching:
            vt_setting = self.get_vt_setting()
            ioc_scans = {}
            scan_val_uuid_map = {}
            log_uuids=set()

        for rec in data:
            # IOC processing
            if self.ioc_matching:
                alert = self.match_iocs(rec,node_id, ioc_types, iocs)
                if alert:
                    ioc_alerts.append(alert)

            # scans
            if self.threat_intel_matching:
                check_scans = self.config_scan_cols.intersection(rec["columns"].keys())
                for scan_type in check_scans:
                    val = rec["columns"][scan_type]
                    uuid = rec['uuid']
                    log_uuids.add(uuid)
                    if scan_type in ioc_scans.keys():
                        ioc_scans[scan_type].append(val)
                        if (scan_type,val) in scan_val_uuid_map.keys():
                            scan_val_uuid_map[(scan_type,val)].append(uuid)
                        else:
                            scan_val_uuid_map[(scan_type,val)]=[uuid]
                    else:
                        ioc_scans[scan_type]=[val]
                        scan_val_uuid_map[(scan_type,val)]=[uuid]

        if self.ioc_matching:
            task_save_alert = asyncio.create_task(self.save_ioc_alerts(ioc_alerts))
        
        if self.threat_intel_matching:
            task_save_scans = asyncio.create_task(self.match_save_scans(ioc_scans,vt_setting))
            task_get_rl_map = asyncio.create_task(self.get_rl_map(log_uuids))
            await task_save_scans
            await task_get_rl_map
            self.save_scans_maps(task_get_rl_map.result(),scan_val_uuid_map,task_save_scans.result())
        
        if self.ioc_matching:
            await task_save_alert

    def match_iocs(self, rec, node_id, ioc_types, iocs):
        from polylogyx.db.models import Alerts
        columns = rec["columns"]
        check_iocs = set(columns.keys()).intersection(ioc_types)
        alert = None
        
        for ioc_type in check_iocs:
            if columns[ioc_type] in iocs[ioc_type].keys():
                alert = Alerts(
                    message=columns,
                    query_name=rec["name"],
                    result_log_uid=rec["uuid"],
                    node_id=node_id,
                    rule_id=None,
                    type=Alerts.THREAT_INTEL,
                    source="ioc",
                    source_data={},
                    severity=iocs[ioc_type][columns[ioc_type]],
                )
                break

        return alert
        
    async def save_ioc_alerts(self,ioc_alerts):
        if ioc_alerts:
            from polylogyx.db.models import db
            try:
                db.session.bulk_save_objects(ioc_alerts)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)

    async def match_save_scans(self,ioc_scans,vt_setting):
        from polylogyx.db.models import ResultLogScan,db,ResultLog
        since = dt.datetime.utcnow() - dt.timedelta(hours=24 * int(str(vt_setting)))

        rl_scans = []

        for scan_type,scan_values in ioc_scans.items():
            result_log_scans = ResultLogScan.query.filter(
                                ResultLogScan.scan_type==scan_type,
                                ResultLogScan.scan_value.in_(scan_values)
                                ).all()
            
            db_scans=set()
            for result_log_scan in result_log_scans:
                if result_log_scan.vt_updated_at and result_log_scan.vt_updated_at < since:
                    result_log_scan.reputations={}
                    
                db_scans.add(result_log_scan.scan_value)

            new_scans = set(scan_values).difference(db_scans)

            for new_scan in new_scans:
                result_log_scans.append(ResultLogScan(
                        scan_value=new_scan, 
                        scan_type=scan_type,
                        reputations={}))

            rl_scans+=result_log_scans
        

        db.session.bulk_save_objects(rl_scans,return_defaults=True)
        db.session.commit()


        scan_id_maps ={}
        for rls in rl_scans:
            scan_id_maps[(rls.scan_type,rls.scan_value)]=rls.id

        return scan_id_maps


    async def get_rl_map(self,log_uuids):
        from polylogyx.db.models import ResultLog
        
        rl = ResultLog.query.with_entities(ResultLog.id,ResultLog.uuid
                                            ).filter(ResultLog.uuid.in_(log_uuids)
                                            ).all()
        rl_map = {}
        for r in rl:
            rl_map[r.uuid]=r.id
        
        return rl_map

    def save_scans_maps(self,rl_map,scan_val_uuid_map,scan_id_maps):
        from polylogyx.db.models import db
        from flask import current_app
        rl_maps_values = []
        for key,vals in scan_val_uuid_map.items():
            for val in vals:
                if key in scan_id_maps.keys():
                    rl_maps_values.append((rl_map[val],scan_id_maps[key]))
        current_app.logger.critical(rl_maps_values)
        if rl_maps_values:
            qry = 'insert into result_log_maps (result_log_id,result_log_scan_id) values {0}'.format(",".join([str(i) for i in rl_maps_values]))
            current_app.logger.critical(rl_maps_values)
            db.session.execute(qry)
            db.session.commit() 
                







