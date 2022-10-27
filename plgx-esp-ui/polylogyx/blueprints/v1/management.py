import json

from flask_restful import Resource, inputs
from flask import request, abort
from werkzeug.exceptions import NotFound
from polylogyx.blueprints.v1.external_api import api
from polylogyx.models import User, Settings, ThreatIntelCredentials, AuthToken, VirusTotalAvEngines
from polylogyx.extensions import bcrypt
from polylogyx.util.api_validator import ApiValidator
from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import common_dao, settings_dao
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.authorize import admin_required
from polylogyx.utils import is_password_strong

import jwt


api_validator_obj = ApiValidator()


@api.resource('/management/changepw', endpoint='change password')
class ChangePassword(Resource):
    """
        Changes user password
    """
    parser = requestparse(['old_password', 'new_password', 'confirm_new_password'], [str, str, str], ["old password", "new password", "confirm new password"], [True, True, True])

    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        payload = jwt.decode(request.headers.environ.get('HTTP_X_ACCESS_TOKEN'), current_app.config['SECRET_KEY'], algorithms=["HS512"])
        user = User.query.filter_by(id=payload['id']).first()
        if is_password_strong(args['new_password']):
            if bcrypt.check_password_hash(user.password, args['old_password']):
                if not bcrypt.check_password_hash(user.password, args['new_password']):
                    if args['new_password'] == args['confirm_new_password']:
                        current_app.logger.info("%s has changed the password", user.username)
                        user.update(password=bcrypt.generate_password_hash(args['new_password']
                                                                           .encode("utf-8")).decode("utf-8"),
                                    reset_password=False)
                        user_logged_in = AuthToken.query.filter(
                           AuthToken.token == request.headers.environ.get('HTTP_X_ACCESS_TOKEN')).first()

                        for token_object in AuthToken.query.filter(AuthToken.token_expired == False)\
                                .filter(AuthToken.user == user_logged_in.user):
                            token_object.logged_out_at = dt.datetime.utcnow()
                            token_object.token_expired = True
                        db.session.commit()
                        message = "Password is updated successfully"
                        status = "success"
                        current_app.logger.info("User login password is updated successfully")
                    else:
                        message = "New password and confirm new password are not matching for the user"
                        current_app.logger.info("New password and confirm new password are not matching for the user")
                else:
                    message = "New password and old password should not be same!"
                    current_app.logger.info("New password and old password should not be same!")
            else:
                message = "Old password is not matching!"
        else:
            message = "Password should contain 1 uppercase, 1 lowercase, 1 digit, 1 special character and min 8 characters of length!"
        current_app.logger.info(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/management/verifypw', endpoint='verify password')
class VerifyPassword(Resource):
    """
        Verifies user's password
    """
    parser = requestparse(['password'], [str], ["password of the user to verify"], [True])

    def post(self):
        args = self.parser.parse_args()
        payload = jwt.decode(request.headers.environ.get('HTTP_X_ACCESS_TOKEN'), current_app.config['SECRET_KEY'], algorithms=["HS512"])
        user = User.query.filter_by(id=payload['id']).first()
        if bcrypt.check_password_hash(user.password, args['password']):
            message = "Password for the current user is verified successfully"
            status = "success"
            current_app.logger.info("Password for the current user is verified successfully")
        else:
            message = "Password is not matching with the current user"
            status = "failure"
        current_app.logger.info(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/management/settings', endpoint="settings update")
class SettingsUpdate(Resource):
    """
        To change purge data duration and alert aggregation settings
    """
    parser = requestparse(['purge_data_duration', 'alert_aggregation_duration', 'sso_enable',
                           'sso_configuration'],
                          [str, str, str, dict],
                          ["purge duration", "alert aggregation duration", 'sso_enable', 'sso_configuration'],
                          [False, False, False, False], [None, None, ["true", "false"], None],
                          [None, None, None, None])

    def get(self):
        query_set = Settings.query.filter(Settings.name.in_(['data_retention_days', 'alert_aggregation_duration',
                                                             'sso_enable', 'sso_configuration'])).all()
        settings = {}
        for setting in query_set:
            if setting.name == 'sso_configuration':
                settings[setting.name] = json.loads(setting.setting)
            elif setting.name == "data_retention_days":
                settings["purge_data_duration"] = setting.setting
            else:
                settings[setting.name] = setting.setting
        return marshal(prepare_response("Platform settings are fetched successfully", "success", settings),
                       parent_wrappers.common_response_wrapper)

    @admin_required
    def put(self):
        args = self.parser.parse_args()
        if args['purge_data_duration']:
            try:
                if 0 < int(args['purge_data_duration']) < int(current_app.config.get('INI_CONFIG', {}).get('max_data_retention_days')):
                    data_duration = str(int(args['purge_data_duration']))
                else:
                    return marshal(prepare_response(f"Data retention days should be greater than 0 days and less than {current_app.config.get('INI_CONFIG', {}).get('max_data_retention_days')} days!", 'failure'),
                                   parent_wrappers.common_response_wrapper
                                   )
            except ValueError:
                return marshal(prepare_response("Please pass a valid integer for data retention days!", 'failure'), parent_wrappers.common_response_wrapper
                               )
            settings_dao.update_or_create_setting('data_retention_days', data_duration)
            message = "data retention setting is updated successfully"
            current_app.logger.info("Purge data duration is set to {0} days".format(data_duration))
        if args['alert_aggregation_duration']:
            try:
                max_alert_aggr_limit = int(current_app.config.get('INI_CONFIG', {}).get('max_alert_aggregation_in_secs', 86400))
                req_alert_aggr = int(args['alert_aggregation_duration'])
                if not (0 <= req_alert_aggr <= max_alert_aggr_limit):
                    return marshal(prepare_response(f"Alert aggregation duration should be greater than 0 seconds and less than {max_alert_aggr_limit} seconds!", 'failure'),
                                   parent_wrappers.common_response_wrapper
                                   )
            except ValueError:
                return marshal(prepare_response("Please pass a valid integer(seconds) for alert aggregation duration!", 'failure'), parent_wrappers.common_response_wrapper
                               )
            settings_dao.update_or_create_setting('alert_aggregation_duration', req_alert_aggr)
            current_app.logger.info(
                "Alert aggregation duration is set to {0} seconds".format(req_alert_aggr))
            message = "Alert settings is updated successfully"
        if args['sso_enable']:
            settings_dao.update_or_create_setting('sso_enable', args['sso_enable'])
            current_app.logger.info(
                "SSO Authentication enabled/disabled status is set to {0}".format(args['sso_enable']))
        if args['sso_configuration']:
            config = args['sso_configuration']
            if 'idp_metadata_url' not in config or 'app_name' not in config or 'entity_id' not in config:
                message = "Please provide idp_metadata_url, app_name and entity_id!"
                current_app.logger.info(message)
                return marshal(prepare_response(message, 'failure'), parent_wrappers.common_response_wrapper
                               )
            else:
                settings_dao.update_or_create_setting('sso_configuration', json.dumps(config))
                current_app.logger.info(
                    "SSO Configuration is set to {0}".format(args['sso_configuration']))
                message = "sso configurations are updated successfully"
        db.session.commit()
        status = "success"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/management/apikeys', endpoint='add apikey')
class UpdateApiKeys(Resource):
    """
        Resource for Threat Intel API keys management
    """
    parser = requestparse(['vt_key', 'IBMxForceKey', 'IBMxForcePass', 'otx_key'], [str, str, str, str],
                          ['vt key', 'IBMxForceKey', 'IBMxForcePass', 'otx key'], [False, False, False, False])
    parser_get = requestparse([], [], [], [])

    @admin_required
    def post(self):
        """
            Updates Threat Intel API keys
        """
        args = self.parser.parse_args()
        status = "success"
        passed_keys_count = 0
        for arg in args:
            if args[arg]:
                passed_keys_count += 1

        if not args['IBMxForcePass'] and args['IBMxForceKey'] or args['IBMxForcePass'] and not args['IBMxForceKey']:
            return marshal({'status': "failure", 'message': "Both IBMxForceKey and IBMxForcePass are required!",
                            'data': None, 'errors': {'ibmxforce': "Both IBMxForceKey and IBMxForcePass are required!"}},
                           parent_wrappers.common_response_with_errors_wrapper)

        threat_intel_creds = {'ibmxforce': {}, 'virustotal': {}, 'alienvault': {}}
        if args['IBMxForceKey'] and args['IBMxForcePass']:
            threat_intel_creds['ibmxforce'] = {'key': args['IBMxForceKey'], 'pass': args['IBMxForcePass']}
        if args['vt_key']:
            threat_intel_creds['virustotal'] = {'key': args['vt_key']}
        if args['otx_key']:
            threat_intel_creds['alienvault'] = {'key': args['otx_key']}

        errors = {}
        invalid = []
        for intel in threat_intel_creds.keys():
            is_key_valid = True
            existing_creds = None
            if threat_intel_creds[intel]:
                response = api_validator_obj.validate_threat_intel_key(intel, threat_intel_creds[intel])
                if not response[0]:
                    is_key_valid = False
                    invalid.append(intel)
                    errors[intel] = "This threat intel api key is invalid!"
                else:
                    existing_creds = db.session.query(ThreatIntelCredentials).filter(
                        ThreatIntelCredentials.intel_name == intel).first()
                if not response[1] is None:
                    try:
                        body = response[1].json()
                        if 'message' in body:
                            errors[intel] = body['message']
                        elif 'error' in body:
                            errors[intel] = body['error']
                    except:
                        errors[intel] = response[1].text
                if is_key_valid:
                    if existing_creds:
                        existing_creds.credentials = threat_intel_creds[intel]
                        db.session.add(existing_creds)
                    else:
                        ThreatIntelCredentials.create(intel_name=intel, credentials=threat_intel_creds[intel])
        db.session.commit()
        API_KEYS = {}
        threat_intel_credentials = ThreatIntelCredentials.query.all()
        for threat_intel_credential in threat_intel_credentials:
            API_KEYS[threat_intel_credential.intel_name] = threat_intel_credential.credentials
        if not invalid:
            message = "Threat Intel keys are updated successfully"
        else:
            if (passed_keys_count == len(invalid)+1 and 'ibmxforce' not in invalid) or \
                    (passed_keys_count == len(invalid)+2 and 'ibmxforce' in invalid):
                status = 'failure'
            message = "{} api key(s) provided is/are invalid!".format(','.join(invalid))
        current_app.logger.info(message)
        return marshal({'status': status, 'message': message, 'data': API_KEYS, 'errors': errors},
                       parent_wrappers.common_response_with_errors_wrapper)

    def get(self):
        """
            Returns Threat Intel API keys
        """
        API_KEYS = {}
        threat_intel_credentials = ThreatIntelCredentials.query.all()
        for threat_intel_credential in threat_intel_credentials:
            API_KEYS[threat_intel_credential.intel_name] = threat_intel_credential.credentials
        message = "Threat Intel Keys are fetched successfully"
        status = "success"
        return marshal(prepare_response(message, status, API_KEYS), parent_wrappers.common_response_wrapper
                       )


@api.resource('/management/virustotal/av_engine', endpoint="Virus Total AV engine update")
class VirusTotalAvEngineUpdate(Resource):

    """to update av engine status"""
    parser = requestparse(['min_match_count','vt_scan_retention_period','av_engines'], [int,int, dict],
                          ["minimum count for unselected engine match","vt_scan_retention_period","selected av engines"],
                          [False,False,False])

    def get(self):
        status = "failure"
        data = []
        message = "virustotal_min_match_count or av engines are not set"
        virustotal_match_count_obj = Settings.query.filter(Settings.name == 'virustotal_min_match_count').first()
        virustotal_scan_retention_period_obj = Settings.query.filter(Settings.name == 'vt_scan_retention_period').first()
        if virustotal_match_count_obj:
            minimum_count = int(virustotal_match_count_obj.setting)
            vt_scan_retention_period = int(virustotal_scan_retention_period_obj.setting)
            data = common_dao.fetch_virus_total_av_engines()
            if data:
                data = {'min_match_count': minimum_count, 'av_engines': data,
                        'vt_scan_retention_period':vt_scan_retention_period}
                status = "success"
                message = "virus total av engines are fetched successfully"
                current_app.logger.info("virus total av engines are fetched successfully")
        return prepare_response(message, status, data)

    @admin_required
    def post(self):
        from polylogyx.db.signals import create_platform_activity_obj
        from polylogyx.dao.v1.users_dao import get_current_user
        args = self.parser.parse_args()
        av_engines = args['av_engines']
        minimum_count = args['min_match_count']
        vt_scan_retention_period = args['vt_scan_retention_period']
        if not minimum_count and not av_engines and not vt_scan_retention_period :
            abort(400, "Please provide valid payload")

        if minimum_count:
            if minimum_count > 0:
                minimum_count_obj = Settings.query.filter(Settings.name == 'virustotal_min_match_count').first()
                minimum_count_obj.setting = minimum_count
                minimum_count_obj.update(minimum_count_obj)
            else:
                abort(400, "Please provide  minimum_count greater than 0")
        if vt_scan_retention_period:
            if vt_scan_retention_period > 0:
                vt_scan_retention_period_obj = Settings.query.filter(Settings.name == 'vt_scan_retention_period').first()
                vt_scan_retention_period_obj.setting = vt_scan_retention_period
                vt_scan_retention_period_obj.update(vt_scan_retention_period_obj)
            else:
                abort(400, "Please provide  period greater than 0")
        if av_engines:
            for av_engine in av_engines:
                if "status" not in av_engines[av_engine]:
                    abort(400, "Please provide status OR please provide valid payload")
            common_dao.update_av_engine_status(av_engines)  # Update only if its provided
            current_user = get_current_user()
            if current_user:
                user_id = current_user.id
            else:
                user_id = None
            create_platform_activity_obj(db.session, 'updated', VirusTotalAvEngines, user_id)
        db.session.commit()
        status = "success"
        message = "Virus Total AV engines configuration has been changed successfully"
        current_app.logger.info(message)
        return prepare_response(message, status)


from polylogyx.log_setting import update_log_level_setting, get_log_level_setting, set_another_server_log_level
@api.resource('/management/log_setting', endpoint="Log level settings")
class LogSetting(Resource):
    """
        To update log level of the servers
    """
    parser = requestparse(['er_log_level', 'er_ui_log_level'], [str, str],
                          ["ER Log Level", "ER-UI Log Level"],
                          [False, False],
                          [['WARNING', 'INFO', 'DEBUG'], ['WARNING', 'INFO', 'DEBUG']])

    @admin_required
    def get(self):
        server_name = request.args.get("server_name", "ER-UI")
        if server_name == "ER":
            setting = get_log_level_setting("er_log_level")
        else:
            setting = get_log_level_setting('er_ui_log_level')
        if setting:
            level = setting.setting
        else:
            level = "WARNING"
        data = {"log_level": level}
        status = "success"
        message = "Log levels fetched"
        current_app.logger.info("Log levels are fetched successfully")
        return prepare_response(message, status, data)

    @admin_required
    def put(self):
        from polylogyx.cache import refresh_log_level
        args = self.parser.parse_args()
        status = "success"
        message = "Log level has been changed successfully"
        if args['er_log_level']:
            update_log_level_setting('er_log_level', args["er_log_level"])
            set_another_server_log_level('ER', args["er_log_level"])
        if args['er_ui_log_level']:
            update_log_level_setting('er_ui_log_level', args["er_ui_log_level"])
        refresh_log_level()
        current_app.logger.info(message)
        return prepare_response(message, status)


from polylogyx.tasks import purge_old_data
@api.resource('/management/manual_purge', endpoint="Manual Purge Request")
class ManualPurge(Resource):
    """
        On demand data purge
    """
    parser = requestparse(['rentention_days'], [int],
                          ["Data Rentention Days"],
                          [True]
                          )

    @admin_required
    def post(self):
        args = self.parser.parse_args()
        status = "success"
        message = "Manual purge triggered successfully"
        if args['rentention_days'] > 0:
            purge_old_data.apply_async(args=[args['rentention_days']])
        else:
            status = "failure"
            message = "Manual purge failed, Retention days should be greater than 0!"
        current_app.logger.info(message)
        return prepare_response(message, status)


from flask import send_from_directory
import datetime as dt
@api.resource('/management/download_log', endpoint="Download server logs")
class DownloadLog(Resource):
    """
        Download server logs
    """
    parser = requestparse(['server_name', 'filename'], [str, str],
                          ["Server Name", 'file name'],
                          [True, True],
                          [["ER","ER-UI"], None]
                          )
    @admin_required
    def get(self):
        status = "success"
        message = "Logs Downloaded successfully"
        data = []
        filename = None
        dir = None
        server_name = request.args.get("server_name","ER-UI")
        if server_name == "ER":
            dir = '/var/log/er'
            filename = 'er_log'
        elif server_name == "ER-UI":
            dir = current_app.config['POLYLOGYX_LOGGING_DIR']
            filename = current_app.config["POLYLOGYX_LOGGING_FILENAME"]
        else:
            status = "failure"
            message = "No such container found"

        if dir:
            import os
            fdir = os.listdir(dir)
            data = [f for f in fdir if f.startswith(filename) and os.path.isfile(os.path.join(dir,f))]
        return prepare_response(message, status, data)

    @admin_required
    def post(self):
        args = self.parser.parse_args()
        status = "success"
        message = "Logs Downloaded successfully"

        # if args["no"] is not None:
        #     file_suffix = "."+str(args["no"])
        #     filename+=file_suffix
        # # elif "date" in args:
        # #     today = dt.date.today()
        # #     inp_date = dt.datetime.date(args['date'])
        # #     if today != inp_date:
        # #         file_suffix='.'+dt.datetime.strftime(args['date'], "%Y-%m-%d")


        dir=current_app.config['POLYLOGYX_LOGGING_DIR']
        if args['server_name'] == 'ER':
            dir='/var/log/er/'


        try:
            return send_from_directory(dir,args["filename"],as_attachment=True)
        except NotFound:
            status="failure"
            message = "No log file found"

        current_app.logger.info(message)
        return prepare_response(message, status)


from polylogyx.dao.v1.metrics_dao import get_metrics

@api.resource('/management/metrics', endpoint="Server Metrics")
class Metrics(Resource):
    """
        Download server logs
    """
    parser = requestparse(['from_time'], [str],
                          ["From time"],
                          [True],
                          [None]
                          )

    
    def post(self):
        args = self.parser.parse_args()
        status = "success"
        message = "Metrics fetched successfully"
        today = dt.datetime.today()

        try:
            data = {}
            ft = dt.datetime.strptime(args["from_time"],"%Y-%m-%d %H:%M:%S")
            today = today.replace(hour=0, minute=0, second=0, microsecond=0)
            topFiveNodes = hosts_dao.topFiveNodes(today)
            data["TOPHOSTS"]=[]
            import shutil

            total, used, free = shutil.disk_usage("/")
            data["DISKUSAGE"] = {"total":round(total/2**30, 2),"free":round(free/2**30,2),"unit":"GB"}
            for entry in topFiveNodes:
                data['TOPHOSTS'].append({"hostname":entry[1].display_name,"value":entry[0]})
            for cont in ["NGINX","POSTGRES","RABBITMQ"]:
                res = get_metrics(cont,ft)
                res = [{'created_at': dt.datetime.strftime(query.created_at,"%Y-%m-%d %H:%M:%S"), 'unit': query.unit, "value":query.data} for query in res]
                data[cont]=res
        except Exception as e:
            print(e)
            return prepare_response("failure","Invalid inputs")

        return prepare_response(message,status,data)