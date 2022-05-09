import json

from flask import request
from flask_restplus import Namespace, Resource, marshal

from .utils import *
from polylogyx.utils import require_api_key, create_tags
from polylogyx.dao import tags_dao as dao
from polylogyx.wrappers import tag_wrappers as wrapper
from polylogyx.wrappers import parent_wrappers as parentwrapper



ns = Namespace('tags', description='tags related operations')

@require_api_key
@ns.route('/', endpoint = "list_tags")
@ns.doc(params = {})
class TagsList(Resource):
    """List all tags of the Nodes"""

    @ns.marshal_with(wrapper.response_taglist)
    def get(self):
        """returns API response of list of tags info"""
        list_dict_data = [{'value':tag.value,'nodes':[node.host_identifier for node in tag.nodes],'packs':[pack.name for pack in tag.packs],'queries':[query.name for query in tag.queries],'file_paths':tag.file_paths} for tag in dao.get_all_tags()]

        data = marshal(list_dict_data,wrapper.tag_wrapper, envelope='data')
        return data


@require_api_key
@ns.route('/add', endpoint = "add_tags")
@ns.doc(params={'tags': "tags to add"})
class AddTag(Resource):
    """adds a new tag to the Tag model"""

    parser = requestparse(['tags'], [str], ["list of comma separated tags to add"], [True])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation
        add_tags = args['tags'].split(',')
        add_tags = create_tags(*add_tags)
        message = "Tags are added successfully"
        status = "success"
        return marshal(prepare_response(message,status), parentwrapper.failure_response_parent)