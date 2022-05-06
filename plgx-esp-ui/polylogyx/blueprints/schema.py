from flask_restplus import Namespace, Resource, marshal

from polylogyx.wrappers import parent_wrappers as parentwrapper
from polylogyx.utils import require_api_key
from polylogyx.constants import PolyLogyxServerDefaults



ns = Namespace('schema', description='schema related operations')
from .utils import *

@require_api_key
@ns.route('/', endpoint = "get_schema")
@ns.doc(params = {})
class GetSchema(Resource):
    """return the response of schema"""

    def get(self):
        schema_json = PolyLogyxServerDefaults.POLYLOGYX_OSQUERY_SCHEMA_JSON
        return marshal(prepare_response('Successfully fetched the schema',"success",schema_json), parentwrapper.common_response_wrapper,skip_none=True)


@require_api_key
@ns.route('/<string:table>', endpoint = "get_table_schema")
@ns.doc(params = {'table':"table"})
class GetTableSchema(Resource):
    """return the response of schema of the table given"""

    def get(self, table):
        schema_json = PolyLogyxServerDefaults.POLYLOGYX_OSQUERY_SCHEMA_JSON
        if table:
            try:
                table_schema = schema_json[table]
                return marshal(prepare_response('Successfully fetched the table schema',"success",table_schema), parentwrapper.common_response_wrapper,skip_none=True)
            except:
                message = 'Table with this name does not exist'
        else:
            message = "please provide a table name"
        return marshal(prepare_response(message,"failure"), parentwrapper.failure_response_parent)

