import json, base64

from flask import request
from flask_restplus import Namespace, Resource, marshal

from .utils import *
from polylogyx.utils import require_api_key, send_test_mail
from polylogyx.dao import settings_dao as dao
from polylogyx.wrappers import parent_wrappers as parentwrapper
from polylogyx.constants import PolyLogyxServerDefaults

ns = Namespace('email', description='email related operations')


@require_api_key
@ns.route('/configure', endpoint = 'configure_email')
@ns.doc(params={"email":"from email", "smtpPort":"smtp port", "smtpAddress":"smtp address", "password": "password of the from mail", "emailRecipients":"list of to-email addresses"})
class ConfigureEmailRecipientAndSender(Resource):
    """configures the email recipient and the sender based on the details given"""

    parser = requestparse(["email", "smtpPort", "smtpAddress", "password", "emailRecipients"],[str,str,str,str,list],["from email","smtp port","smtp address", "password of the from mail","list of to-email addresses"],[True,True,True,True,True])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation
        result_data = configure_email_recipient_and_sender(request)
        data = result_data['data']
        message = result_data['message']
        status = result_data['status']
        return marshal(prepare_response(message,status,data), parentwrapper.common_response_wrapper)


def configure_email_recipient_and_sender(request):
    senderInvalid = False
    status = "failure"
    message = None
    response_json = {}
    request_json = get_body_data(request)


    existing_setting = dao.get_settings_by_name(PolyLogyxServerDefaults.plgx_config_all_settings)

    requestedEmail = None
    requestedEmails = None
    requestedPort = None
    requestedAddress = None
    requestedPassword = None

    requestedEmailSetting = None
    requestedEmailsSetting = None
    requestedPortSetting = None
    requestedAddressSetting = None
    requestedPasswordSetting = None

    requestedEmails = None
    if existing_setting:
        existingSettingObj = json.loads(existing_setting.setting)
    else:
        existingSettingObj = {}

    from flask import current_app
    for k, v in request_json.items():
        setting = dao.get_settings_by_name(k)
        if k == 'email':
            requestedEmail = v
            requestedEmailSetting = setting
        elif k == 'smtpPort':
            requestedPortSetting = setting
            requestedPort = v
        elif k == 'smtpAddress':
            requestedAddress = v
            requestedAddressSetting = setting
        elif k == 'password':
            requestedPasswordSetting = setting
            v = base64.encodestring(str.encode(v))
            requestedPassword = v
        elif k == 'emailRecipients':
            requestedEmails = v
            requestedEmailsSetting = setting
            existingSettingObj['emailRecipients'] = requestedEmails

    if requestedEmail:
        if not requestedPassword:
            senderInvalid = True
            message = 'Please provide the sender email password'
        elif not requestedAddress:
            senderInvalid = True
            message = 'Please provide the  smtp address'
        elif not requestedPort:
            senderInvalid = True
            message = 'Please provide the  smtp port'
        else:
            existingSettingObj['email'] = requestedEmail
            existingSettingObj['smtpPort'] = requestedPort
            existingSettingObj['smtpAddress'] = requestedAddress
            existingSettingObj['password'] = requestedPassword.decode('utf-8')
            existingSettingObj['emailRecipients'] = requestedEmails

            current_app.config['MAIL_USERNAME'] = requestedEmail

            current_app.config['MAIL_PASSWORD'] = base64.b64decode(requestedPassword)
            current_app.config['MAIL_SERVER'] = requestedAddress
            current_app.config['MAIL_PORT'] = int(requestedPort)
            current_app.config['MAIL_RECIPIENTS'] = requestedEmails

            save_or_update_setting(requestedEmailSetting, requestedEmail, 'email')
            save_or_update_setting(requestedPortSetting, requestedPort, 'smtpPort')

            save_or_update_setting(requestedAddressSetting, requestedAddress, 'smtpAddress')
            save_or_update_setting(requestedPasswordSetting, requestedPassword, 'password')
            save_or_update_setting(requestedEmailsSetting, requestedEmails, 'emailRecipients')

            if existing_setting:
                existing_setting.setting = json.dumps(existingSettingObj)
                existing_setting.save()
            else:
                dao.create_settings(name=PolyLogyxServerDefaults.plgx_config_all_settings, setting=json.dumps(existingSettingObj))

            status = 'success'
            message = 'Successfully updated the details'
    else:
        if requestedEmails:
            save_email_recipients(requestedEmails)
            existingSettingObj['emailRecipients'] = ",".join(requestedEmails)
        if existing_setting:
            existing_setting.setting = json.dumps(existingSettingObj)
            existing_setting.update(existing_setting)
        else:
            dao.create_settings(name=PolyLogyxServerDefaults.plgx_config_all_settings, setting=json.dumps(existingSettingObj))
        status = 'success'
        message = 'Successfully updated the details'

    response_json['data'] = json.loads(dao.get_settings_by_name(PolyLogyxServerDefaults.plgx_config_all_settings).setting)
    response_json['message']= message
    response_json['status'] = status
    return response_json


@require_api_key
@ns.route('/test', endpoint='test_send_email')
@ns.doc(params={"username": "username", "smtp": "smtp", "recipients": "recipients", "password": "password"})
class TestMailSend(Resource):
    """tests email config by sending a test mail"""

    parser = requestparse(["username", "smtp", "password", "recipients"],
                          [str, str, str, str],
                          ["username to send mail from", "smtp", "password of the username", "recipients with comma separated"], [True, True, True, True])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        args['email'] = args['username']
        if args['recipients']:
            args['recipients'] = args['recipients'].split(',')
        else:
            args['recipients'] = []
        if send_test_mail(args):
            status = 'success'
            message = 'A Test mail is sent to the recipients successfully'
        else:
            status = 'failure'
            message = 'Could not validate credentials. Please enable less secure apps if using gmail and verify security alert prompt on your mail. '
        return marshal(prepare_response(message,status), parentwrapper.common_response_wrapper, skip_none=True)
