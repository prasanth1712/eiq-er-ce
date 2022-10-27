from flask_restful import Resource
from polylogyx.blueprints.v1.external_api import api
from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import iocs_dao
from polylogyx.models import IOCIntel
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.authorize import admin_required




@api.resource('/iocs', endpoint='get ioc data')
class IndicatorsOfCompromise(Resource):
    """
        lists ioc json data
    """

    def get(self):
        ioc_full_data = {}
        for ioc in iocs_dao.get_intel_data('self'):
            if ioc.threat_name not in ioc_full_data:
                ioc_full_data[ioc.threat_name] = {'type': ioc.type, 'severity': ioc.severity,
                                                  'intel_type': ioc.intel_type, 'values': ioc.value}
            else:
                ioc_full_data[ioc.threat_name]['values'] = ioc_full_data[ioc.threat_name]['values'] + ',' + str(ioc.value)
        if not ioc_full_data:
            ioc_full_data = {
                "test-intel_ipv4": {
                    "type": "remote_address",
                    "values": "3.30.1.15,3.30.1.16",
                    "severity": "MEDIUM"
                },
                "test-intel_domain_name": {
                    "type": "domain_name",
                    "values":"unknown.com,slackabc.com",
                    "severity": "MEDIUM"
                },
                "test-intel_md5": {
                    "type": "md5",
                    "values": "3h8dk0sksm0,9sd772ndd80",
                    "severity": "INFO"
                }
            }
        status = "success"
        message = "Successfully fetched the IOCs"
        return marshal(prepare_response(message, status, ioc_full_data), parent_wrappers.common_response_wrapper
                       )


@api.resource('/iocs/add', endpoint='add ioc')
class AddIOC(Resource):
    """
        Uploads and adds an ioc file to the iocs folder
    """
    parser = requestparse(['data'], [dict], ['Threat Intel Data Json'], [True])

    @admin_required
    def post(self):
        from polylogyx.cache import refresh_cached_iocs
        from polylogyx.db.signals import create_platform_activity_obj
        from polylogyx.dao.v1.users_dao import get_current_user
        args = self.parser.parse_args()
        data = args['data']
        iocs_dao.del_manual_threat_intel('self')
        dictionary_list = []
        try:
            for intel_name, values in data.items():
                if ('severity' in values and 'type' in values) and isinstance(values['values'], str):
                    for value in values['values'].split(','):
                        severity = str(values.get('severity', 'MEDIUM')).upper()
                        if severity == 'WARNING':
                            severity = 'MEDIUM'
                        if severity not in [IOCIntel.MEDIUM, IOCIntel.CRITICAL, IOCIntel.INFO,IOCIntel.HIGH,IOCIntel.LOW]:
                            severity = IOCIntel.MEDIUM
                        dictionary_list.append({'intel_type': 'self', 'type': values['type'],
                                                'value': value.strip(), 'severity': severity,
                                                'threat_name': intel_name})
            
            db.session.bulk_insert_mappings(IOCIntel, dictionary_list)
            current_user = get_current_user()
            if current_user:
                user_id = current_user.id
            else:
                user_id = None
            create_platform_activity_obj(db.session, 'updated', IOCIntel, user_id)
            db.session.commit()
            refresh_cached_iocs()
            current_app.logger.info("IOCs(Indicators of compromise) are updated")
            message = "Successfully updated the intel data"
            status = "success"
        except Exception as e:
            current_app.logger.error("Unable to update IOCs - {}".format(str(e)))
            message = str(e)
            status = "failure"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
