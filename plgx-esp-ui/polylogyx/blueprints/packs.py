from flask import jsonify, request, current_app
from flask_restplus import reqparse, Namespace, Resource, marshal

from .utils import *
from polylogyx.utils import require_api_key, create_tags, validate_osquery_query, get_tags
from polylogyx.dao import packs_dao as dao
from polylogyx.dao import queries_dao as query_dao
from polylogyx.wrappers import pack_wrappers as wrapper
from polylogyx.wrappers import parent_wrappers as parentwrapper


ns = Namespace('packs', description='packs related operations')


@require_api_key
@ns.route('/', endpoint = 'list_packs')
@ns.doc(params={})
class PacksList(Resource):
    """List all packs of the Nodes"""

    @ns.marshal_with(parentwrapper.common_response_wrapper)
    def get(self):
        """returns API response of list of packs info"""
        queryset=dao.get_all_packs()
        data = marshal(queryset, wrapper.pack_wrapper)
        for i in range(len(data)):
            data[i]['tags'] = [tag.to_dict() for tag in queryset[i].tags]
            data[i]['queries'] = [query.name for query in queryset[i].queries]
        message = "successfully fetched the packs info"
        if not data: message = "there is no data to show"
        return prepare_response(message,"success",data)


@require_api_key
@ns.route('/<int:pack_id>', endpoint = 'pack_by_id')
@ns.doc(params={'pack_id': 'id of the pack'})
class PackById(Resource):
    """List all packs of the Nodes"""

    def get(self, pack_id):
        """returns API response of list of packs info"""
        status = "failure"
        if pack_id:
            pack_qs = dao.get_pack_by_id(pack_id)
            if pack_qs:
                pack = marshal(pack_qs, wrapper.pack_wrapper)
                pack['tags'] = [tag.to_dict() for tag in pack_qs.tags]
                pack['queries'] = [query.name for query in pack_qs.queries]
                return marshal(prepare_response("successfully fetched the packs info","success",pack),parentwrapper.common_response_wrapper)
            else:
                message = "Pack info with this pack_id does not exist"
        else:
            message = "Missing pack_id"
        return marshal(prepare_response(message), parentwrapper.failure_response_parent)


@require_api_key
@ns.route('/add', endpoint = 'pack_add')
@ns.doc(params={'tags': 'list of tags', 'name':'name of the pack', 'queries':'list of queries', 'category':'category name'})
class AddPack(Resource):
    """adds a new pack to the Pack model"""

    parser = requestparse(['tags','name','queries','category','platform','version','description','shard'],[str, str, dict, str, str, str, str, int],['list of comma separated tags', 'name of the pack', 'dict of queries', 'category', 'platform', 'version', 'description', 'shard'],[False, True, True, False, False, False, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation
        pack = add_pack_through_json_data(args)
        return marshal({'pack_id': pack.id}, wrapper.response_add_pack)


@require_api_key
@ns.route('/tag/edit', endpoint = 'add_tag_to_pack')
@ns.doc(params={'pack_id': 'id of the pack', 'add_tags':'list of tags to add', 'remove_tags':'list of tags to remove'})
class EditTagsToPack(Resource):
    """adds tag to pack"""
    parser = requestparse(['pack_id', 'add_tags', 'remove_tags'], [int, str, str],
                          ["id of the pack", "list of comma separated tags to add", "list of comma separated tags to remove"], [True, False, False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation
        pack_id = args['pack_id']
        status = 'failure'
        message = None

        add_tags = args['add_tags'].split(',')
        remove_tags = args['remove_tags'].split(',')

        pack = dao.get_pack_by_id(pack_id)
        if not pack:
            message = 'Invalid pack id. Pack with this id does not exist'
        else:
            if add_tags:
                add_tags = create_tags(*add_tags)
                for add_tag in add_tags:
                    if not add_tag in pack.tags:
                        pack.tags.append(add_tag)

            if remove_tags:
                remove_tags = get_tags(*remove_tags)
                for remove_tag in remove_tags:
                    if remove_tag in pack.tags:
                        pack.tags.remove(remove_tag)

            pack.save()
            status = 'success'
            message = 'Successfully modified the tag(s)'

        return marshal(prepare_response(message,status), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/<string:pack_name>/tags', endpoint='pack_tags_list')
@ns.doc(params={'pack_name': 'pack name'})
class ListTagsOfPack(Resource):
    """list tags of a pack by its pack_name"""
    parser = requestparse(['tags'], [str], ["list of comma separated tags to be created to the pack"])

    def get(self, pack_name):
        status = 'failure'
        pack = dao.get_pack_by_name(pack_name)
        if not pack:
            message = 'Invalid pack name. This pack does not exist'
            data = None
        else:
            data = tag_name_format(pack.tags)
            status = 'success'
            message = 'Successfully fetched the tag(s)'
        return marshal(prepare_response(message,status,data), parentwrapper.common_response_wrapper)

    @ns.expect(parser)
    def post(self, pack_name):
        args = self.parser.parse_args()  # need to exists for input payload validation
        tags = args['tags'].split(',')
        pack = dao.get_pack_by_name(pack_name)
        if pack:
            obj_list = get_tags_list_to_add(tags)
            pack.tags.extend(obj_list)
            pack.save()
            return marshal(prepare_response('Successfully created the tag(s) to packs', 'success'), parentwrapper.common_response_wrapper, skip_none=True)
        return marshal(prepare_response('No pack present for the name given!', 'failure'), parentwrapper.common_response_wrapper, skip_none=True)


@require_api_key
@ns.route('/upload', endpoint="packs_upload")
@ns.doc(params = {})
class UploadPack(Resource):
    """packs will be added through the uploaded file"""

    from werkzeug import datastructures
    parser = requestparse(['file', 'category'],[datastructures.FileStorage, str],['packs file', 'pack category'],[True,False])

    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()  # need to exists for input payload validation
        args_dict = json.loads(args['file'].read())
        args_dict['name'] = args['file'].filename.lower().split('.')[0]
        if args['category']:
            args_dict['category'] = args['category']
        pack = add_pack_through_json_data(args_dict)
        return marshal(prepare_response("pack uploaded successfully","success",pack.id),parentwrapper.common_response_wrapper)

