import base64
import json

from flask_restplus import Namespace, Resource, inputs

from polylogyx.blueprints.v1.utils import *
from polylogyx.utils import send_test_mail
from polylogyx.dao.v1 import settings_dao
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.constants import PolyLogyxServerDefaults
from polylogyx.authorize import admin_required

ns = Namespace('email', description='email related operations')


@ns.route('/configure', endpoint='configure_email')
class ConfigureEmailSettings(Resource):
    """
        Configures the email recipient and the sender based on the details given
    """
    parser = requestparse(["email", "smtpPort", "smtpAddress", "password", "emailRecipients", "use_ssl", "use_tls"],
                          [str, str, str, str, str, inputs.boolean, inputs.boolean],
                          ["from email", "smtp port", "smtp address", "password", "email recipients", "ssl", "tls"],
                          [True, True, True, True, True, False, False],
                          [None, None, None, None, None, None, None],
                          [None, None, None, None, None, False, False])

    def get(self):
        existing_setting = settings_dao.get_settings_by_name(PolyLogyxServerDefaults.plgx_config_all_settings)
        if existing_setting:
            setting = json.loads(existing_setting.setting)
            setting['password'] = base64.decodestring(setting['password'].encode('utf-8')).decode('utf-8')
        else:
            setting = {}
        message = "Successfully fetched the email configuration"
        status = "success"
        return marshal(prepare_response(message, status, setting), parent_wrappers.common_response_wrapper, skip_none=True)

    @admin_required
    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation
        args['smtpPort'] = int(args['smtpPort'])
        if args['emailRecipients']:
            args['emailRecipients'] = args['emailRecipients'].split(',')
        else:
            args['emailRecipients'] = []

        if send_test_mail(args):
            args['password'] = base64.encodestring(str.encode(args['password'])).decode('utf-8')
            del args['x-access-token']
            existing_setting = settings_dao.get_settings_by_name(PolyLogyxServerDefaults.plgx_config_all_settings)
            current_app.logger.debug("Requested email settings are:\n{0}".format(args))
            if existing_setting:
                settings = existing_setting.update(setting=json.dumps(args), synchronize_session=False)
            else:
                settings = settings_dao.create_settings(name=PolyLogyxServerDefaults.plgx_config_all_settings,
                                               setting=json.dumps(args))
            data = json.loads(settings.setting)
            message = "Successfully updated the email settings!"
            status = "success"
            current_app.logger.info("Email configuration is updated")
        else:
            message = "Please check the smtp settings and credentials provided and also \
            provider's additional security verifications needed"
            status = "failure"
            data = None
            current_app.logger.error(message)
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@ns.route('/test', endpoint='test_mail_for_existing_settings')
class TestEmailRecipientAndSender(Resource):
    """
        Tests the email recipient and the sender based on the details given
    """

    parser = requestparse(["email", "smtpPort", "smtpAddress", "password", "emailRecipients", "use_ssl", "use_tls"],
                          [str, str, str, str, str, inputs.boolean, inputs.boolean],
                          ["from email", "smtp port", "smtp address", "password", "email recipients", "ssl", "tls"],
                          [True, True, True, True, True, False, False],
                          [None, None, None, None, None, None, None],
                          [None, None, None, None, None, False, False])

    @admin_required
    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        args['smtpPort'] = int(args['smtpPort'])
        current_app.logger.debug("Requested email settings are:\n{0}".format(args))
        if args['emailRecipients']:
            args['emailRecipients'] = args['emailRecipients'].split(',')
        else:
            args['emailRecipients'] = []
        if send_test_mail(args):
            message = "Successfully sent the email to recipients for the existing configuration!"
            status = "success"
        else:
            message = "Please check the smtp settings and credentials provided and also \
            complete the provider's additional security verifications needed"
            status = "failure"
            current_app.logger.error(message)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)
