import os,json
from werkzeug import datastructures
from flask_restful import Resource
from polylogyx.blueprints.v1.external_api import api
from polylogyx.blueprints.v1.utils import *
from polylogyx.wrappers.v1 import parent_wrappers
from polylogyx.authorize import admin_required


@api.resource('/yara', endpoint='list yara')
class ListYara(Resource):
    """
        Lists yara files
    """
    def get(self):
        file_path = os.path.join(current_app.config['RESOURCES_URL'], 'yara', 'list.json')
        if os.path.isfile(file_path) is True:
            with open(file_path, 'r') as jsonfile:
                data = json.load(jsonfile)
                for platform in  ['windows','linux','darwin']:
                    if platform not in data:
                        data[platform] = []
        else:
            data = {'windows':[],'linux':[],'darwin':[]}
        return marshal(prepare_response("Successfully fetched the yara files", 'success', data),
                       parent_wrappers.common_response_wrapper)


@api.resource('/yara/add', endpoint='add yara')
class AddYara(Resource):
    """
        Uploads and adds an yara file to the yara folder
    """
    parser = requestparse(['file','platform'], [datastructures.FileStorage,str], ['Threat file','platform'], [True,True])

    @validate_file_size
    def post(self):
        args = self.parser.parse_args()
        platforms = args['platform'].split(',')
        _file_name, _file_extension = os.path.splitext(args['file'].filename.lower())
        json_file_path = os.path.join(current_app.config['RESOURCES_URL'], 'yara','list.json')
        if _file_extension not in [".yar", ".yara"]:
            message = "Please upload yara(.yara/.yar) files only!"
            status = "failure"
        else:
            file_path = os.path.join(current_app.config['RESOURCES_URL'], 'yara',  args['file'].filename.lower())
            args['file'].seek(0, os.SEEK_END)
            file_length = args['file'].tell()
            args['file'].seek(0)
            if file_length == 0:
                message = "Please upload non empty yara file"
                status = "failure"
            elif os.path.isfile(file_path):
                message = "This file already exists"
                status = "failure"
            else:
                try:
                    args['file'].save(file_path)
                    current_app.logger.info("yara file {} is added".format(args['file'].filename.lower()))
                except FileNotFoundError:
                    os.makedirs(file_path.replace(args['file'].filename.lower(),''))
                    args['file'].save(file_path)
                files = os.listdir(os.path.join(current_app.config['RESOURCES_URL'], 'yara'))
                with open(os.path.join(current_app.config['RESOURCES_URL'], 'yara','list.txt'), 'w') as the_file:
                    for file_name in files:
                        if file_name != 'list.txt' and file_name !='list.json':
                            the_file.write(file_name+'\n')
                if  os.path.os.path.isfile(json_file_path) is True:
                    with open(json_file_path, 'r') as jsonfile:
                        json_object = json.load(jsonfile)
                    for platform in platforms:
                        if platform in json_object.keys():
                            json_object[platform].append(args['file'].filename.lower())
                        else:
                            json_object[platform]=[]
                            json_object[platform].append(args['file'].filename.lower())
                else:
                    json_object = {}
                    for platform in platforms:
                        json_object[platform] = []
                        json_object[platform].append(args['file'].filename.lower())
                with open(json_file_path, 'w') as jsonfile:
                    json.dump(json_object, jsonfile)
                message = "Successfully uploaded the file"
                status = "success"
                current_app.logger.info("A new YARA file '{}' has been uploaded to the server".format(file_name))
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/yara/view', endpoint='view_yara')
class ViewYara(Resource):
    """
        Returns yara file
    """
    parser = requestparse(['file_name'], [str], ['name of the yara file to view the content for'], [True])

    def post(self):
        args = self.parser.parse_args()
        status = "failure"
        message = ""
        data = None
        # clean
        try:
            file_name = args['file_name'].split('/')[-1]
            file_path = os.path.join(current_app.config['RESOURCES_URL'], "yara",file_name.lower())
            if os.path.exists(file_path):
                with open(file_path, 'r') as the_file:
                    data = the_file.read()
                status = "success"
                message = "Successfully fetched the yara file content!"
            else:
                message = "file not found"
        except Exception as e:
            message = str(e)
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)


@api.resource('/yara/delete', endpoint='delete_yara')
class DeleteYara(Resource):
    """
        Deletes yara file from the yara base path
    """
    parser = requestparse(['file_name','platform'], [str,str], ['name of the yara file to delete','platform'], [True,True])

    @admin_required
    def post(self):
        from os import walk
        args = self.parser.parse_args()
        is_delete = True
        platforms = [platform for platform in args['platform'].split(',') if platform in ['darwin','linux','windows']]
        if not platforms or len(platforms) == 0:
            return abort(400, 'please provide valid platforms(windows/linux/darwin)')
        file_name = args['file_name'].split('/')[-1]
        file_path = os.path.join(current_app.config['RESOURCES_URL'], "yara", file_name.lower())
        if not os.path.exists(file_path):
            message = 'File not found'
            return marshal(prepare_response(message, 'failure'), parent_wrappers.common_response_wrapper)
        try:
            with open(os.path.join(current_app.config['RESOURCES_URL'], 'yara', 'list.json'), 'r') as jsonfile:
                data = json.load(jsonfile)
                for platform in platforms:
                    if platform in data and args['file_name'] in data[platform]:
                        data[platform].remove(args['file_name'])
            for platform in data:
                if args['file_name'] in data[platform]:
                    is_delete = False
            with open(os.path.join(current_app.config['RESOURCES_URL'], 'yara', 'list.json'), 'w') as jsonfile:
                json.dump(data, jsonfile)
        except Exception as e:
            is_delete = False
        try:
            current_app.logger.info("yara file {} is requested to delete".format(args['file_name']))
            if is_delete is True:
                os.remove(os.path.join(current_app.config['RESOURCES_URL'], "yara", args['file_name']))
            file_list = []
            for (dirpath, dirnames, filenames) in walk(os.path.join(current_app.config['RESOURCES_URL'], "yara")):
                file_list.extend(filenames)
                break
            files = [file_name+'\n' for file_name in file_list if file_name != 'list.txt' and file_name!='list.json']

            with open(os.path.join(current_app.config['RESOURCES_URL'], 'yara', 'list.txt'), "w") as fi:
                fi.writelines(files)

            return marshal(prepare_response("File with the given file name is deleted successfully", "success"),
                           parent_wrappers.common_response_wrapper)
        except Exception as e:
            current_app.logger.error("Unable to delete YARA file '{0}' - {1}".format(args['file_name'], str(e)))
            return marshal(prepare_response("File with the given file name does not exists", "failure"),
                           parent_wrappers.common_response_wrapper)


@api.resource('/yara/update', endpoint='edit yara ')
class ViewYara(Resource):
    """
        Returns yara file
    """
    parser = requestparse(['file_name','platform'], [str,str], ['name of the yara file to view the content for','platforms'], [True,True])

    def put(self):
        args = self.parser.parse_args()
        if args['platform']:
            mapping_platforms=args['platform'].split(',')
        status = "failure"
        message = None
        data = None
        file_path = os.path.join(current_app.config['RESOURCES_URL'], "yara", args['file_name'].lower())
        if os.path.isfile(file_path) is True:
            yara_file = os.path.join(current_app.config['RESOURCES_URL'], 'yara', 'list.json')
            if os.path.isfile(yara_file) is True:
                with open(yara_file, 'r') as jsonfile:
                    data = json.load(jsonfile)
                    for platform in ['windows','linux','darwin']:
                        if platform in data:
                            if args['file_name'] not in data[platform]:
                                if platform in mapping_platforms:
                                    data[platform].append(args['file_name'])
                        elif platform in mapping_platforms:
                            data[platform]=[]
                            data[platform].append(args['file_name'])
        else:
            return marshal(prepare_response("No such file found", "failure"), parent_wrappers.common_response_wrapper)
        yara_file = os.path.join(current_app.config['RESOURCES_URL'], 'yara', 'list.json')
        if os.path.isfile(yara_file) is True:
            with open(yara_file, 'w') as jsonfile:
                json.dump(data, jsonfile)
        status='success'
        message='successfully mapped to platform {0}'.format(args['platform'])
        return marshal(prepare_response(message, status, data), parent_wrappers.common_response_wrapper)