from flask_restplus import Namespace, Resource

from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import iocs_dao
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.authorize import admin_required

ns = Namespace('iocs', description='iocs related operations')


@ns.route('', endpoint='get ioc data')
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
                    "severity": "WARNING"
                },
                "test-intel_domain_name": {
                    "type": "domain_name",
                    "values":"unknown.com,slackabc.com",
                    "severity": "WARNING"
                },
                "test-intel_md5": {
                    "type": "md5",
                    "values": "3h8dk0sksm0,9sd772ndd80",
                    "severity": "INFO"
                }
            }
        status = "success"
        message = "Successfully fetched the IOCs"
        return marshal(prepare_response(message, status, ioc_full_data), parent_wrappers.common_response_wrapper,
                       skip_none=True)


@ns.route('/add', endpoint='add ioc')
class AddIOC(Resource):
    """
        Uploads and adds an ioc file to the iocs folder
    """
    parser = requestparse(['data'], [dict], ['Threat Intel Data Json'], [True])

    @admin_required
    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        data = args['data']
        iocs_dao.del_manual_threat_intel('self')
        try:
            for intel_name, values in data.items():
                if ('severity' in values and 'type' in values) and isinstance(values['values'], str):
                    for value in values['values'].split(','):
                        iocs_dao.create_manual_threat_intel(intel_type='self', type=values['type'], value=value,
                                                            severity=values['severity'], threat_name=intel_name)
            current_app.logger.info("IOCs(Indicators of compromise) are updated")
            message = "Successfully updated the intel data"
            status = "success"
        except Exception as e:
            current_app.logger.error("Unable to update IOCs - {}".format(str(e)))
            message = str(e)
            status = "failure"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)
