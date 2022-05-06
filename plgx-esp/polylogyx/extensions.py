# -*- coding: utf-8 -*-
import datetime as dt
import os
import re

from flask import current_app
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal



class LogTee(object):
    def __init__(self, app=None):
        self.app = app
        self.plugins = []

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        from importlib import import_module

        from polylogyx.plugins import AbstractLogsPlugin

        plugins = []
        all_plugins_obj = app.config.get("POLYLOGYX_LOG_PLUGINS_OBJ", {})

        if (
            os.environ.get("RSYSLOG_FORWARDING")
            and os.environ.get("RSYSLOG_FORWARDING") == "true"
            and "rsyslog" in all_plugins_obj
        ):
            plugins.append(all_plugins_obj["rsyslog"])

        for plugin in plugins:
            package, classname = plugin.rsplit(".", 1)
            module = import_module(package)
            klass = getattr(module, classname, None)

            if klass is None:
                raise ValueError('Could not find a class named "{0}" in package "{1}"'.format(classname, package))

            if not issubclass(klass, AbstractLogsPlugin):
                raise ValueError("{0} is not a subclass of AbstractLogsPlugin".format(klass))
            self.plugins.append(klass(app.config))

    def handle_status(self, data, **kwargs):
        for plugin in self.plugins:
            plugin.handle_status(data, **kwargs)

    def handle_result(self, data, **kwargs):
        for plugin in self.plugins:
            plugin.handle_result(data, **kwargs)

    def handle_recon(self, data, **kwargs):
        for plugin in self.plugins:
            plugin.handle_recon(data, **kwargs)


class RuleManager(object):
    def __init__(self, app=None):
        self.network = None
        self.last_update = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.load_alerters()
        # Save this instance on the app, so we have a way to get at it.
        app.rule_manager = self
        
    def load_alerters(self):
        """Load the alerter plugin(s) specified in the app config."""
        from importlib import import_module

        from polylogyx.plugins import AbstractAlerterPlugin

        alerters = self.app.config.get("POLYLOGYX_ALERTER_PLUGINS", {})

        self.alerters = {}
        for name, (plugin, config) in alerters.items():
            package, classname = plugin.rsplit(".", 1)
            module = import_module(package)
            klass = getattr(module, classname, None)

            if klass is None:
                raise ValueError('Could not find a class named "{0}" in package "{1}"'.format(classname, package))

            if not issubclass(klass, AbstractAlerterPlugin):
                raise ValueError("{0} is not a subclass of AbstractAlerterPlugin".format(name))
            self.alerters[name] = klass(config)

    def should_reload_rules(self):
        """Checks if we need to reload the set of rules."""
        from polylogyx.db.models import Rule

        if self.last_update is None:
            return True

        newest_rule = Rule.query.order_by(Rule.updated_at.desc()).limit(1).first()
        if newest_rule and self.last_update < newest_rule.updated_at:
            return True

        return False

    def load_ioc_intels(self):
        from polylogyx.db.models import IOCIntel

        self.all_ioc_intels = list(IOCIntel.query.all())
        if not self.all_ioc_intels:
            return

    def load_rules(self):
        """Load rules from the database."""
        from polylogyx.db.models import Rule
        from polylogyx.utils.rules import Network

        if not self.should_reload_rules():
            return
        print("before getting rules")
        all_rules = list(Rule.query.filter(Rule.status != "INACTIVE").all())
        print("after getting rules")
        print("all rules - ", all_rules)
        self.network = Network()

        if not all_rules:
            return

        for rule in all_rules:
            # Verify the alerters
            for alerter in rule.alerters:
                if alerter not in self.alerters:
                    current_app.logger.error('No such alerter: "{0}"'.format(alerter))
                    # raise ValueError('No such alerter: "{0}"'.format(alerter))

            # Create the rule.
            try:
                self.network.parse_query(
                    rule.conditions, alerters=rule.alerters, rule_id=rule.id, platform=rule.platform
                )
            except Exception as e:
                current_app.logger.error(rule.id)
        # Save the last updated date
        # Note: we do this here, and not in should_reload_rules, because it's
        # possible that we've reloaded a rule in between the two functions, and
        # thus we accidentally don't reload when we should.
        self.last_update = max(r.updated_at for r in all_rules)

    def check_for_ioc_matching(self, name, columns, node, uuid, capture_column):
        flag = False
        for intel in self.all_ioc_intels:
            if capture_column == intel.type and columns[capture_column].lower() == intel.value.lower():
                from polylogyx.utils.intel import save_intel_alert
                flag = True
                save_intel_alert(
                    data={},
                    source="ioc",
                    query_name=name,
                    severity=intel.severity,
                    uuid=uuid,
                    columns=columns,
                    node_id=node["id"],
                )
                current_app.logger.info(
                    "Found an event with existing indicator with type '{0}', value '{1}' from the node '{2}'".format(
                        capture_column, columns[capture_column], node
                    )
                )
                break
        return flag



    def check_for_ioc_matching_opt(self, name, columns, node, uuid, capture_column):
        from polylogyx.db.models import IOCIntel
        from sqlalchemy import func
        from polylogyx.utils.intel import save_intel_alert
        
        intel=IOCIntel.query.with_entities(IOCIntel.severity)\
            .filter(IOCIntel.type==capture_column)\
            .filter(func.lower(IOCIntel.value)==columns[capture_column].lower())\
            .first()
        
        if intel:
            save_intel_alert(
                    data={},
                    source="ioc",
                    query_name=name,
                    severity=intel[0],
                    uuid=uuid,
                    columns=columns,
                    node_id=node["id"],
                )
            current_app.logger.info(
                "Found an event with existing indicator with type '{0}', value '{1}' from the node '{2}'".format(
                    capture_column, columns[capture_column], node
                ))
            return True
        return False

    def check_for_iocs(self, name, columns, node, uuid,vt_setting=None):
        current_app.logger.debug("Scanning for IOCs of Node '{0}' from the results: \n{1}".format(node, columns))
        try:
            from polylogyx.constants import IOC_COLUMNS, TO_CAPTURE_COLUMNS
            from polylogyx.db.models import ResultLog, ResultLogScan,Settings
            self.ioc_match_opt = current_app.config.get('HIGH_INTEL_VOLUME', False)
        
        
            for capture_column in IOC_COLUMNS:
                if capture_column in columns and columns[capture_column]:
                    if self.ioc_match_opt:
                        ioc_match=self.check_for_ioc_matching_opt(name, columns, node, uuid, capture_column)
                    else:
                        ioc_match=self.check_for_ioc_matching(name, columns, node, uuid, capture_column)
                    current_app.logger.info(
                        "columns captured".format(
                            capture_column, node, columns[capture_column]
                        )
                    )
                    if capture_column in TO_CAPTURE_COLUMNS:
                        result_log_scan = ResultLogScan.query.filter(
                            ResultLogScan.scan_value == columns[capture_column]
                        ).first()
                        if result_log_scan:
                            if vt_setting:
                                since = dt.datetime.utcnow() - dt.timedelta(hours=24 * int(vt_setting.setting))
                                if result_log_scan.vt_updated_at and result_log_scan.vt_updated_at < since:
                                    newReputations = {}
                                    result_log_scan.update(reputations=newReputations)
                        if not result_log_scan:
                            from polylogyx.db.models import ResultLogScan
                            current_app.logger.info(
                                "Found a new '{0}' indicator on Node '{1}' to be scanned with value '{2}'".format(
                                    capture_column, node, columns[capture_column]
                                )
                            )
                            result_log_scan = ResultLogScan.create(
                            scan_value=columns[capture_column], scan_type=capture_column, reputations={}
                        )
                        #result_log = ResultLog.query.filter(ResultLog.uuid == uuid).first()
                        #result_log_scan.result_logs.append(result_log)
                        result_log = db.session.execute("select id from result_log where uuid='{0}'".format(uuid)).first()
                        r_id = result_log[0]
                        db.session.execute('insert into result_log_maps (result_log_id,result_log_scan_id) values ({0},{1})'.format(r_id,result_log_scan.id))
                        db.session.commit()
                    if ioc_match:
                        break
                    
        except Exception as e:
            current_app.logger.error("Unable to scan for IOCs - {}".format(e))

    def handle_log_entry(self, entry, node):
        """The actual entrypoint for handling input log entries."""
        from polylogyx.db.models import Rule, Settings
        from polylogyx.utils.rules import RuleMatch

        current_app.logger.debug("Loading Rules and IOCs if not loaded yet...")
        self.load_rules()
        self.ioc_match_opt = current_app.config.get('HIGH_INTEL_VOLUME', False)
        
        if not self.ioc_match_opt:
            self.load_ioc_intels()

        to_trigger = []
        vt_setting = Settings.query.filter(Settings.name == 'vt_scan_retention_period').first()
        for result in entry:
            self.check_for_iocs(result["name"], result["columns"], node, result["uuid"],vt_setting)
            alerts = self.network.process(result, node)
            if len(alerts) == 0:
                continue

            # Alerts is a set of (alerter name, rule id) tuples.  We convert
            # these into RuleMatch instances, which is what our alerters are
            # actually expecting.
            for rule_id, alerters in alerts.items():
                rule = Rule.get_by_id(rule_id)

                to_trigger.append(
                    (
                        alerters,
                        RuleMatch(rule=rule, result=result, node=node, alert_id=0),
                    )
                )

        # Now that we've collected all results, start triggering them.
        alert_aggr_duration_setting = Settings.query.filter(Settings.name == "alert_aggregation_duration").first()
        if alert_aggr_duration_setting:
            alert_aggr_duration = int(alert_aggr_duration_setting.setting)
        else:
            alert_aggr_duration = 60
        for alerters, match in to_trigger:
            alert = self.save_in_db(match.result, match.node, match.rule, alert_aggr_duration)
            node["alert"] = alert
            for alerter in alerters:
                match = match._replace(alert_id=alert.id)
                self.alerters[alerter].handle_alert(node, match, None)

    def save_in_db(self, result_log_dict, node, rule, alert_aggr_duration):
        from polylogyx.db.models import AlertLog, Alerts

        existing_alert = (
            Alerts.query.filter(Alerts.node_id == node["id"])
            .filter(Alerts.rule_id == rule.id)
            .filter((dt.datetime.utcnow() - Alerts.created_at) <= dt.timedelta(seconds=alert_aggr_duration))
            .first()
        )
        if existing_alert:
            AlertLog.create(
                name=result_log_dict["name"],
                timestamp=result_log_dict["timestamp"],
                action=result_log_dict["action"],
                columns=result_log_dict["columns"],
                alert_id=existing_alert.id,
                result_log_uuid=result_log_dict["uuid"],
            )
            db.session.commit()
            current_app.logger.debug("Aggregating the Alert with ID {0}..".format(existing_alert.id))
            return existing_alert
        else:
            alerts_obj = Alerts(
                message=result_log_dict["columns"],
                query_name=result_log_dict["name"],
                result_log_uid=result_log_dict["uuid"],
                node_id=node["id"],
                rule_id=rule.id,
                type=Alerts.RULE,
                source="rule",
                source_data={},
                recon_queries=rule.recon_queries,
                severity=rule.severity,
            )
            alerts_obj = alerts_obj.save(alerts_obj)
            AlertLog.create(
                name=result_log_dict["name"],
                timestamp=result_log_dict["timestamp"],
                action=result_log_dict["action"],
                columns=result_log_dict["columns"],
                alert_id=alerts_obj.id,
                result_log_uuid=result_log_dict["uuid"],
            )
            db.session.commit()
            current_app.logger.debug("Creating a new Alert with ID {0}..".format(alerts_obj.id))
            return alerts_obj


class ThreatIntelManager(object):
    def __init__(self, app=None):
        self.network = None
        self.last_update = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        self.load_intels()

        # Save this instance on the app, so we have a way to get at it.
        app.threat_intel = self

    def load_intels(self):
        """Load the alerter plugin(s) specified in the app config."""
        from importlib import import_module

        from polylogyx.plugins import AbstractIntelPlugin

        intels = self.app.config.get("POLYLOGYX_THREAT_INTEL_PLUGINS", {})

        self.intels = {}
        for name, (plugin, config) in intels.items():
            package, classname = plugin.rsplit(".", 1)
            module = import_module(package)
            klass = getattr(module, classname, None)

            if klass is None:
                raise ValueError('Could not find a class named "{0}" in package "{1}"'.format(classname, package))

            if not issubclass(klass, AbstractIntelPlugin):
                raise ValueError("{0} is not a subclass of AbstractAlerterPlugin".format(name))
            self.intels[name] = klass(config)

    def analyse_hash(self, value, type, node):
        """The actual entrypoint for handling input log entries."""

        for key, value_elem in self.intels.items():
            try:
                value_elem.analyse_hash(value, type, node)
            except Exception as e:
                current_app.logger.error(e)

    def analyse_pending_hashes(self):
        """The actual entrypoint for handling input log entries."""

        for key, value_elem in self.intels.items():
            try:
                value_elem.analyse_pending_hashes()
            except Exception as e:
                current_app.logger.error(e)

    def generate_alerts(self):
        """The actual entrypoint for handling input log entries."""

        for key, value_elem in self.intels.items():
            try:
                value_elem.generate_alerts()
            except Exception as e:
                current_app.logger.error(e)

    def analyse_domain(self, value, type, node):
        """The actual entrypoint for handling input log entries."""

        for key, value_elem in self.intels.items():
            value_elem.analyse_hash(value, type, node)

    def update_credentials(self):
        """The actual entrypoint for handling input log entries."""

        self.load_intels()
        for key, value_elem in self.intels.items():
            value_elem.update_credentials()


def create_distributed_query(node, query_str, alert, query_name, match):
    from polylogyx.db.models import DistributedQuery, DistributedQueryTask, Node

    try:
        data = match.result["columns"]
        results = re.findall("#!([^\s]+)!#", query_str, re.MULTILINE)
        query_valid = True
        for result in results:
            if result not in data:
                query_valid = False
                break
            else:
                value = data[result]
                query_str = query_str.replace("#!" + result + "!#", value)
        if query_valid:
            query = DistributedQuery.create(sql=query_str, alert_id=alert.id, description=query_name)
            node_obj = Node.query.filter_by(id=node["id"]).first_or_404()
            task = DistributedQueryTask(node=node_obj, save_results_in_db=True, distributed_query=query)
            db.session.add(task)
            db.session.commit()
    except Exception as e:
        current_app.logger.error(e)

    return


def make_celery(app, celery):
    """From http://flask.pocoo.org/docs/0.10/patterns/celery/"""
    # Register our custom serializer type before updating the configuration.
    from kombu.serialization import register

    from polylogyx.celery.celery_serializer import djson_dumps, djson_loads

    register(
        "djson",
        djson_dumps,
        djson_loads,
        content_type="application/x-djson",
        content_encoding="utf-8",
    )

    # Actually update the config
    celery.config_from_object(app.config)


    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


bcrypt = Bcrypt()
csrf = CsrfProtect()
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
log_tee = LogTee()
rule_manager = RuleManager()
threat_intel = ThreatIntelManager()
#cache = Cache(config={"CACHE_TYPE": "filesystem",'CACHE_DIR': '/src/cache'})
cache = Cache()