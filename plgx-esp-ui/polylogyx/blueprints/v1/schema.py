from flask_restful import  Resource
from polylogyx.blueprints.v1.external_api import api
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.blueprints.v1.utils import *





@api.resource ('/schema', endpoint="get schema")
class GetSchema(Resource):
    """
        Returns the response of schema
    """
    parser = requestparse(['export_type'], [str], ['export_type(json/sql schema)'], [False], [['sql', 'json']], ['sql'])

    
    def get(self):
        from polylogyx.dao.v1.common_dao import get_osquery_agent_schema
        args = self.parser.parse_args()
        if args['export_type'] == 'sql':
            schema = PolyLogyxServerDefaults.POLYLOGYX_OSQUERY_SCHEMA_JSON
        elif args['export_type'] == 'json':
            schema = [table.to_dict() for table in get_osquery_agent_schema()]
        message = "PolyLogyx agent schema is fetched successfully"
        status = "success"
        return marshal(prepare_response(message, status, schema),
                       parent_wrappers.common_response_wrapper)


@api.resource ('/schema/<string:table>', endpoint="get table schema")
class GetTableSchema(Resource):
    """
        Returns the response of schema of the table given
    """

    def get(self, table):
        schema_json = PolyLogyxServerDefaults.POLYLOGYX_OSQUERY_SCHEMA_JSON
        if table:
            try:
                table_schema = schema_json[table]
                return marshal(prepare_response('Successfully fetched the table schema', "success", table_schema),
                               parent_wrappers.common_response_wrapper)
            except:
                message = 'Table with this name does not exist'
        else:
            message = "Please provide a table name"
        return marshal(prepare_response(message, "failure"), parent_wrappers.failure_response_parent)

