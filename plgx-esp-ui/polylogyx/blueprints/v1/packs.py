from json import JSONDecodeError

from flask_restplus import Namespace, Resource
from flask import json

from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import packs_dao, tags_dao
from polylogyx.wrappers.v1 import pack_wrappers, parent_wrappers
from polylogyx.authorize import admin_required

ns = Namespace('packs', description='packs related operations')


@ns.route('', endpoint='list packs')
class PacksList(Resource):
    """
        List all packs of the Nodes
    """
    parser = requestparse(['start', 'limit', 'searchterm'],
                          [int, int, str],
                          ['start', 'limit', 'searchterm'],
                          [False, False, False], [None, None, None], [None, None, ''])

    @ns.expect(parser)
    @ns.marshal_with(parent_wrappers.common_response_wrapper)
    def post(self):
        args = self.parser.parse_args()
        queryset = packs_dao.get_all_packs(args['searchterm']).offset(args['start']).limit(args['limit']).all()
        data = marshal(queryset, pack_wrappers.pack_wrapper)
        for index in range(len(data)):
            data[index]['tags'] = [tag.to_dict() for tag in queryset[index].tags]
            data[index]['queries'] = marshal(queryset[index].queries, pack_wrappers.query_wrapper)
            for query_index in range(len(queryset[index].queries)):
                data[index]['queries'][query_index]['tags'] = [tag.to_dict() for tag in
                                                               queryset[index].queries[query_index].tags]
                data[index]['queries'][query_index]['packs'] = [pack.name for pack in
                                                                queryset[index].queries[query_index].packs]
        message = "Successfully fetched the packs info"
        status = "success"
        if not data:
            data = []
        data = {'count': packs_dao.get_all_packs(args['searchterm']).count(),
                'total_count': packs_dao.get_total_count(),
                'results': data}
        return prepare_response(message, status, data)


@ns.route('/<int:pack_id>', endpoint='pack by id')
class PackById(Resource):
    """
        List all packs of the Nodes
    """

    def get(self, pack_id):
        if pack_id:
            pack_qs = packs_dao.get_pack_by_id(pack_id)
            if pack_qs:
                pack = marshal(pack_qs, pack_wrappers.pack_wrapper)
                pack['tags'] = [tag.to_dict() for tag in pack_qs.tags]
                pack['queries'] = [query.name for query in pack_qs.queries]
                return marshal(prepare_response("successfully fetched the packs info", "success", pack),
                               parent_wrappers.common_response_wrapper)
            else:
                message = "Pack info with this pack id does not exist"
        else:
            message = "Missing pack id"
        return marshal(prepare_response(message), parent_wrappers.failure_response_parent)


@ns.route('/add', endpoint='pack add')
class AddPack(Resource):
    """
        Adds a new pack to the Pack model
    """

    parser = requestparse(['tags', 'name', 'queries', 'category', 'platform', 'version', 'description', 'shard'],
                          [str, str, dict, str, str, str, str, int],
                          ['list of comma separated tags', 'name of the pack', 'dict of queries', 'category',
                           'platform(windows/linux/darwin)', 'version', 'description', 'shard'],
                          [False, True, True, False, False, False, False, False],
                          [None, None, None, ["Intrusion Detection", "Monitoring", "Compliance and Management",
                                              "Forensics and Incident Response", "General", "Others"],
                           ["windows", "linux", "darwin"], None, None, None])

    @admin_required
    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        pack = add_pack_through_json_data(args)
        current_app.logger.info("A new pack is added '{0}' with name '{1}'".format(pack, pack.name))
        return marshal({'pack_id': pack.id}, pack_wrappers.response_add_pack)


@ns.route('/<string:pack_name>/tags', endpoint='pack tags list')
@ns.route('/<int:pack_id>/tags', endpoint='pack tags list by pack id')
class ListOrEditsTagsOfPack(Resource):
    """
        Resource for tags of a Pack
    """
    parser = requestparse(['tag'], [str],
                          ["tag to add/remove for the pack"], [True])

    def get(self, pack_name=None, pack_id=None):
        """
            Lists tags of a Pack by its id or name
        """
        status = 'failure'
        if pack_name:
            pack = packs_dao.get_pack_by_name(pack_name)
        elif pack_id:
            pack = packs_dao.get_pack_by_id(pack_id)
        else:
            pack = None
        if not pack:
            message = "Pack id or pack name passed it not correct"
            data = None
        else:
            data = [tag.value for tag in pack.tags]
            status = "success"
            message = "Successfully fetched the tags of pack"
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper, skip_none=True)

    @admin_required
    @ns.expect(parser)
    def post(self, pack_name=None, pack_id=None):
        """
            Creates tags of a Pack by its id
        """
        args = self.parser.parse_args()
        status = 'failure'

        if pack_name:
            pack = packs_dao.get_pack_by_name(pack_name)
        elif pack_id:
            pack = packs_dao.get_pack_by_id(pack_id)
        else:
            pack = None
        if pack:
            tag = args['tag'].strip()
            if not tag:
                message = "Tag provided is invalid!"
            else:
                tag = tags_dao.create_tag_obj(tag)
                pack.tags.append(tag)
                pack.save()
                current_app.logger.info("New tag '{0}' is added to the pack with name '{1}'".format(tag, pack.name))
                status = "success"
                message = "Successfully created tags to pack"
        else:
            message = "Pack id or pack name passed it not correct"

        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)

    @admin_required
    @ns.expect(parser)
    def delete(self, pack_name=None, pack_id=None):
        """
            Remove tags of a Pack by its id
        """
        args = self.parser.parse_args()
        status = 'failure'

        if pack_name:
            pack = packs_dao.get_pack_by_name(pack_name)
        elif pack_id:
            pack = packs_dao.get_pack_by_id(pack_id)
        else:
            pack = None
        if pack:
            tag = args['tag'].strip()
            tag = tags_dao.get_tag_by_value(tag)
            if tag:
                if packs_dao.is_tag_of_pack(pack, tag):
                    pack.tags.remove(tag)
                    pack.save()
                    current_app.logger.info("Tag '{0}' is removed from the pack '{1}'".format(tag, pack.name))
                    message = "Successfully removed tags from pack"
                    status = "success"
                else:
                    message = "Tag provided is not in pack's tag list, Please check tag once again"
            else:
                message = "Tag provided doesn't exists"
        else:
            message = "Pack id or pack name passed it not correct"
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/upload', endpoint="packs upload")
class UploadPack(Resource):
    """
        Packs will be added through the uploaded file
    """

    from werkzeug import datastructures
    parser = requestparse(['file', 'category'], [datastructures.FileStorage, str], ['packs file', 'pack category'],
                          [True, False], [None, ["Intrusion Detection", "Monitoring", "Compliance and Management",
                                                 "Forensics and Incident Response", "General", "Others"],
                                          [None, "General"]])

    @admin_required
    @ns.expect(parser)
    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        try:
            args_dict = json.loads(args['file'].read())
            args_dict['name'] = args['file'].filename.lower().split('.')[0]
            if args['category']:
                args_dict['category'] = args['category']
            if 'queries' not in args_dict:
                message = "Queries are compulsory!"
            else:
                try:
                    pack = add_pack_through_json_data(args_dict)
                    current_app.logger.info("A new pack '{0}' has been added with name '{1}'".format(pack, pack.name))
                    return marshal({'pack_id': pack.id}, pack_wrappers.response_add_pack)
                except JSONDecodeError:
                    message = "Json provided is not well formatted/invalid!"
                    current_app.logger.error("Json provided is not well formatted/invalid! - JSONDecodeError")
        except Exception as e:
            message = "Please upload only readable(.json/.conf) formatted files with well json!"
            current_app.logger.error("Please upload only readable(.json/.conf) formatted files with well json! - {}"
                                     .format(str(e)))
        return marshal(prepare_response(message, status, None), parent_wrappers.common_response_wrapper, skip_none=True)


@ns.route('/<string:pack_name>/delete', endpoint='pack removed')
@ns.route('/<int:pack_id>/delete', endpoint='pack removed by id')
class PackRemoved(Resource):
    """
        Delete Pack
    """

    @admin_required
    def delete(self, pack_name=None, pack_id=None):
        status = "failure"
        message = "Pack is not available with this pack name or pack id"
        pack = None
        if pack_id:
            pack = packs_dao.get_pack_by_id(pack_id)

        if pack_name:
            pack = packs_dao.get_pack_by_name(pack_name)

        if pack:
            pack_tags = pack.tags
            db.session.delete(pack)
            db.session.commit()
            message = "Successfully removed the Pack"
            status = "Success"
            current_app.logger.warning("Pack {} is requested for deletion".format(pack))
            return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper, skip_none=True)
