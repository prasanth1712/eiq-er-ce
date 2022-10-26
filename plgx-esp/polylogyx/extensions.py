# -*- coding: utf-8 -*-
import datetime as dt
import os
import re
import redis

from flask import current_app, _app_ctx_stack
from flask_bcrypt import Bcrypt

from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import asyncio
from polylogyx.ioc_engine import IOCEngine


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
        self.rule_matching = app.config.get("RULE_MATCHING",False)

    def load_alerters(self):
        """Load the alerter plugin(s) specified in the app config."""
        from importlib import import_module

        from polylogyx.plugins import AbstractAlerterPlugin

        alerters = self.app.config.get("POLYLOGYX_ALERTER_PLUGINS", {})

        self.alerters = {}
        for name, plugin_config in alerters.items():
            if isinstance(plugin_config, tuple):
                # In some cases this followed lines thing has been done from intel.py send_alert method, So ignoring
                plugin, config = plugin_config
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

    def load_rules(self):
        """Load rules from the database."""
        from polylogyx.utils.rules import Network
        from polylogyx.utils.cache import get_all_cached_rules

        self.all_rules = get_all_cached_rules()

        if not self.all_rules:
            self.network = Network()
            return
        self.create_network(self.all_rules)

    def create_network(self, all_rules):
        from polylogyx.utils.rules import Network
        from polylogyx.utils.cache import redis_client
        from polylogyx.constants import CacheVariables

        # cached_network = redis_client.get(CacheVariables.rule_network)

        # if cached_network:
        #     self.network = cached_network
        #     return

        self.network = Network()
        for rule_name, rule_dict in all_rules.items():
            for alerter in rule_dict['alerters']:
                if alerter not in self.alerters:
                    current_app.logger.error('No such alerter: "{0}"'.format(alerter))

            try:
                self.network.parse_query(
                    rule_dict['conditions'], alerters=rule_dict['alerters'],
                    rule_id=rule_dict['id'], platform=rule_dict['platform']
                )
            except Exception as e:
                current_app.logger.error(rule_dict['id'])
                
        # redis_client.set(CacheVariables.rule_network, self.network)

    def get_alert_aggr_duration(self):
        from polylogyx.utils.cache import get_a_setting
        aggr_setting = get_a_setting('alert_aggregation_duration')
        if aggr_setting:
            alert_aggr_duration = int(aggr_setting)
        else:
            alert_aggr_duration = 60
        return alert_aggr_duration

    async def handle_log_entry(self, entry, node_dict):
        """The actual entrypoint for handling input log entries."""
        if not self.rule_matching:
            return
        from polylogyx.utils.rules import RuleMatch
        from polylogyx.utils.cache import get_a_setting

        self.load_rules()
        vt_setting = get_a_setting('vt_scan_retention_period')
        all_rules_dict = {}
        for rule_value in self.all_rules.values():
            all_rules_dict[rule_value['id']] = rule_value
        if vt_setting is None:
            self.vt_setting = 0
        else:
            self.vt_setting = int(vt_setting)

        log_rules = {}
        for result in entry:
            alerts = self.network.process(result, node_dict)
            if len(alerts) == 0:
                continue
            # Alerts is a set of (alerter name, rule id) tuples.  We convert
            # these into RuleMatch instances, which is what our alerters are
            # actually expecting.
            
            for rule_id, alerters in alerts.items():
                rule = all_rules_dict[rule_id]
                if rule_id in log_rules:
                    log_rules[rule_id][1].append(RuleMatch(rule=rule, result=result, node=node_dict, alert_id=0))
                else:
                    log_rules[rule_id] = (
                            alerters,
                            [RuleMatch(rule=rule, result=result, node=node_dict, alert_id=0)],
                        )

        # Now that we've collected all results, start triggering them.
        alert_aggr_duration = self.get_alert_aggr_duration()
        if log_rules:
            save_alert_task = asyncio.create_task(self.alert_save_in_db(
                                node_dict,
                                alert_aggr_duration,
                                log_rules,
                                all_rules_dict))
            await save_alert_task

    async def alert_save_in_db(self, node, alert_aggr_duration, log_rules, all_rules_dict={}):
        from polylogyx.db.models import AlertLog, Alerts
        from polylogyx.utils.rules import RuleMatch
        from polylogyx.utils.cache import get_rule_node_latest_alerts, update_rule_node_latest_alert
        existing_alerts = get_rule_node_latest_alerts(node["id"])
        if not existing_alerts:
            existing_alerts = {}
        alert_logs = []
        to_aggregate = []
        created_alerts = {}

        for rule_id, alerter_rule_match in log_rules.items():
            for match in alerter_rule_match[1]:
                rl = match.rule
                res = match.result
                if (not existing_alerts.get(str(rule_id), {}).get('created_at') or
                    (existing_alerts.get(str(rule_id), {}).get('created_at') and
                     (dt.datetime.utcnow() - existing_alerts.get(str(rule_id), {}).get('created_at')) > dt.timedelta(
                            seconds=alert_aggr_duration))) and rule_id not in created_alerts:
                    al = Alerts(
                        message=res["columns"],
                        query_name=res["name"],
                        result_log_uid=res["uuid"],
                        node_id=node["id"],
                        rule_id=rule_id,
                        type=Alerts.RULE,
                        source="rule",
                        source_data={},
                        severity=rl['severity'],
                    )
                    created_alerts[rule_id] = al
                else:
                    to_aggregate.append((rule_id, match))
        db.session.bulk_save_objects(created_alerts.values(), return_defaults=True)

        for rule_id, alert in created_alerts.items():
            existing_alerts[str(rule_id)] = {
                                        'created_at': alert.created_at if alert.created_at else dt.datetime.utcnow(), 
                                        'alert_id': alert.id
                                    }
        for rule_id, rule_match in to_aggregate:
            result = rule_match.result
            al = AlertLog(
                name=result["name"],
                timestamp=result["timestamp"],
                action=result["action"],
                columns=result["columns"],
                alert_id=existing_alerts.get(str(rule_id)).get('alert_id'),
                result_log_uuid=result["uuid"])
            alert_logs.append(al)
        db.session.bulk_save_objects(alert_logs)
        db.session.commit()
        for rule_id, alert in created_alerts.items():
            alerters = log_rules[rule_id][0]
            rule = all_rules_dict[rule_id]
            result = {'columns': alert.message, 'name': alert.query_name, 'action': alert.message.get('action')}
            rule_match = RuleMatch(rule=rule, result=result, node=node, alert_id=alert.id)
            for alerter in alerters:
                self.alerters[alerter].handle_alert(node, rule_match, None)

        update_rule_node_latest_alert(node['id'], existing_alerts)


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
        self.threat_intel_matching = app.config.get("THREAT_INTEL_MATCHING", False)

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
        if not self.threat_intel_matching:
            return
        for key, value_elem in self.intels.items():
            try:
                value_elem.analyse_pending_hashes()
            except Exception as e:
                current_app.logger.error(e)

    def generate_alerts(self):
        """The actual entrypoint for handling input log entries."""
        if not self.threat_intel_matching:
            return
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
        if not self.threat_intel_matching:
            return
        self.load_intels()
        for key, value_elem in self.intels.items():
            value_elem.update_credentials()


def create_distributed_query(node, query_str, alert, query_name, match):
    from polylogyx.db.models import DistributedQuery, DistributedQueryTask

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
            task = DistributedQueryTask(node_id=node["id"], save_results_in_db=True, distributed_query=query)
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


class RedisClient(object):
    def __init__(self, app=None, **kwargs):
        self._redis_client = None
        self.provider_class = redis.Redis
        self.provider_kwargs = kwargs

        if app is not None:
            self.init_app(app)

    @classmethod
    def from_custom_provider(cls, provider, app=None, **kwargs):
        assert provider is not None, "your custom provider is None, come on"

        # We never pass the app parameter here, so we can call init_app
        # ourselves later, after the provider class has been set
        instance = cls(**kwargs)

        instance.provider_class = provider
        if app is not None:
            instance.init_app(app)
        return instance

    def init_app(self, app, **kwargs):
        self.provider_kwargs.update(kwargs)
        self._redis_client = self.provider_class(host=app.config.get('REDIS_HOST'), 
                                                port=app.config.get('REDIS_PORT'), 
                                                password=app.config.get('REDIS_PASSWORD'), 
                                                db=0, 
                                                **self.provider_kwargs
                                            )

    def __getattr__(self, name):
        return getattr(self._redis_client, name)

    def __getitem__(self, name):
        return self._redis_client[name]

    def __setitem__(self, name, value):
        self._redis_client[name] = value

    def __delitem__(self, name):
        del self._redis_client[name]


bcrypt = Bcrypt()
db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
log_tee = LogTee()
rule_manager = RuleManager()
threat_intel = ThreatIntelManager()
ioc_engine = IOCEngine()
redis_client = RedisClient()