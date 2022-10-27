from json import JSONDecodeError

from flask_restful import Resource
from flask import json
from polylogyx.blueprints.v1.external_api import api
from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import packs_dao, tags_dao
from polylogyx.wrappers.v1 import pack_wrappers, parent_wrappers
from polylogyx.authorize import admin_required


@api.resource('/packs', endpoint='list packs')
class PacksList(Resource):
    """
        List all packs of the Nodes
    """
    parser = requestparse(['start', 'limit', 'searchterm'],
                          [int, int, str],
                          ['start', 'limit', 'searchterm'],
                          [False, False, False], [None, None, None], [None, None, ''])

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


@api.resource('/packs/<int:pack_id>',  endpoint='pack by id')
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


@api.resource('/packs/add',  endpoint='pack add')
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
    def post(self):
        args = self.parser.parse_args()
        args['name'] = args['name'].strip()
        if not args['name']:
            message = "Pack name provided is not acceptable!"
            return marshal(prepare_response(message, "failure"), parent_wrappers.common_response_wrapper)
        if args['tags'] is not None and (not args['tags'] or not tags_dao.are_all_tags_has_correct_length(args['tags'].split(','))):
            message = f"Tag length should be between 0 and {current_app.config.get('INI_CONFIG', {}).get('max_tag_length')}"
            return marshal(prepare_response(message, "failure"), parent_wrappers.common_response_wrapper)
        elif args['tags'] is not None and not tags_dao.are_all_tags_has_valid_strings(args['tags'].split(',')):
                message = "Tags provided are not valid, tags should not contain ',' and space"
                return marshal(prepare_response(message, "failure"), parent_wrappers.common_response_wrapper)
        existing_pack = packs_dao.get_pack_by_name(args['name'])
        pack = add_pack_through_json_data(args)
        if not existing_pack:
            current_app.logger.info("A new pack is added '{0}' with name '{1}'".format(pack, pack.name))
            message = 'Imported query pack and pack is added/uploaded successfully'
        else:
            current_app.logger.info("Existing pack is  updated '{0}' with name '{1}'".format(pack, pack.name))
            message = 'Imported query pack and pack is updated to successfully'
        return marshal({'pack_id': pack.id,'message': message}, pack_wrappers.response_add_pack)


@api.resource('/packs/<string:pack_name>/tags',  endpoint='pack tags list')
@api.resource('/packs/<int:pack_id>/tags',  endpoint='pack tags list by pack id')
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
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)

    @admin_required
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
            if not tag or not valid_string_parser(tag):
                message = "Tag provided is not valid, tag should not be empty or should not contain ',' and space"
            elif not (0 < len(tag) < int(current_app.config.get('INI_CONFIG', {}).get('max_tag_length'))):
                message = f"Tag length should be between 0 and {current_app.config.get('INI_CONFIG', {}).get('max_tag_length')}"
            else:
                tag = tags_dao.create_tag_obj(tag)
                pack.tags.append(tag)
                pack.save()
                current_app.logger.info("New tag '{0}' is added to the pack with name '{1}'".format(tag, pack.name))
                status = "success"
                message = "Successfully created tags to pack"
        else:
            message = "Pack id or pack name passed it not correct"

        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)

    @admin_required
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
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/packs/upload',  endpoint="packs upload")
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
    @validate_file_size
    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        allowed_platforms = ['windows', 'linux', 'darwin', 'all']
        try:
            args_dict = json.loads(args['file'].read())
            args_dict['name'] = args['file'].filename.lower().split('.')[0]
            if args['category']:
                args_dict['category'] = args['category']
            if len(args_dict['name'].strip()) == 0:
                message = "Please upload pack file with name"
            elif 'queries' not in args_dict:
                message = "Queries are compulsory!"
            elif 'tags' in args_dict and args_dict['tags'] is not None and not tags_dao.are_all_tags_has_correct_length(args_dict['tags'].split(',')):
                message = f"Tag length should be between 0 and {current_app.config.get('INI_CONFIG', {}).get('max_tag_length')}"
            elif 'tags' in args_dict and args_dict['tags'] is not None and  not tags_dao.are_all_tags_has_valid_strings(args_dict['tags'].split(',')):
                message = "Tags provided are not valid"
            elif 'platform' in args_dict and args_dict['platform'] and args_dict['platform'].lower() not in allowed_platforms:
                message = 'Invalid platform'
            elif len([args_dict['queries'][query]['platform'] for query in args_dict['queries']
                    if 'platform' in args_dict['queries'][query]
                    if args_dict['queries'][query]['platform'].lower() not in allowed_platforms]) > 0:
                    message = 'Invalid platform'
            else:
                try:
                    existing_pack = packs_dao.get_pack_by_name(args_dict['name'])
                    pack = add_pack_through_json_data(args_dict)
                    current_app.logger.info("A new pack '{0}' has been added with name '{1}'".format(pack, pack.name))
                    if not existing_pack:
                        current_app.logger.info("A new pack is added '{0}' with name '{1}'".format(pack, pack.name))
                        message = 'Imported query pack and pack is added/uploaded successfully'
                    else:
                        current_app.logger.info(
                            "Existing pack is  updated '{0}' with name '{1}'".format(pack, pack.name))
                        message = 'Imported query pack and pack is updated to successfully'
                    return marshal({'pack_id': pack.id, 'message': message}, pack_wrappers.response_add_pack)
                except JSONDecodeError:
                    message = "Json provided is not well formatted/invalid!"
                    current_app.logger.error("Json provided is not well formatted/invalid! - JSONDecodeError")
        except Exception as e:
            message = "Please upload only readable(.json/.conf) formatted files with well json!"
            current_app.logger.error("Please upload only readable(.json/.conf) formatted files with well json! - {}"
                                     .format(str(e)))
        return marshal(prepare_response(message, status, None), parent_wrappers.common_response_wrapper)


@api.resource('/packs/<string:pack_name>/delete', endpoint='pack removed')
@api.resource('/packs/<int:pack_id>/delete', endpoint='pack removed by id')
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
            return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)
