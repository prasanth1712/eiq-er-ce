from flask_restful import  Resource, inputs
from polylogyx.blueprints.v1.external_api import api
from polylogyx.blueprints.v1.utils import *
from polylogyx.dao.v1 import tags_dao
from polylogyx.wrappers.v1 import tag_wrappers, parent_wrappers, query_wrappers
from polylogyx.authorize import admin_required


@api.resource('/tags', endpoint="list tags")
class TagsList(Resource):
    """
        List all tags of the Nodes
    """
    parser = requestparse(['start', 'limit', 'searchterm','order_by'], [inputs.natural, inputs.natural, str,str],
                          ['start', 'limit', "search term",'order_by'], [False, False, False,False],
                          [None, None, None,None], [None, None, "",None])

    def get(self):
        args = self.parser.parse_args()
        order_by=None
        if args['order_by'] in ['ASC','asc','Asc']:
            order_by='asc'
        elif args['order_by'] in ['DESC','desc','Desc']:
            order_by = 'desc'
        base_qs = tags_dao.get_all_tags(args['searchterm'],order_by)
        total_count = tags_dao.get_tags_total_count()
        list_dict_data = [{'value': tag.value,
                           'nodes': [node.host_identifier for node in tag.nodes if node.state != node.REMOVED and
                                     node.state != node.DELETED],
                           'packs':[pack.name for pack in tag.packs],
                           'queries':[query.name for query in tag.queries]} for tag in
                          base_qs.offset(args['start']).limit(args['limit']).all()]
        data = marshal(list_dict_data, tag_wrappers.tag_wrapper)
        return marshal(prepare_response("Successfully fetched the tags info", "success",
                                        {'count': base_qs.count(), 'total_count': total_count, 'results': data}),
                       parent_wrappers.common_response_wrapper)


@api.resource('/tags/add', endpoint="add tags")
class AddTag(Resource):
    """
        Adds a new tag to the Tag model
    """

    parser = requestparse(['tag'], [str], ["tag to add"], [True])

    @admin_required
    def post(self):
        status = "failure"
        tag = self.parser.parse_args()['tag'].strip()
        if not tag:
            message = "Tag provided is invalid!"
        elif not valid_string_parser(tag):
            message = "Tags provided are not valid"
        elif not (0 < len(tag) < int(current_app.config.get('INI_CONFIG', {}).get('max_tag_length'))):
            message = f"Tag length should be between 0 and {current_app.config.get('INI_CONFIG', {}).get('max_tag_length')}"
        elif tags_dao.get_tag_by_value(tag):
            message = "Tag is already present!"
        else:
            tag = tags_dao.create_tag_obj(tag)
            message = "Tag added successfully"
            status = "success"
            current_app.logger.info("A new tag '{}' has been added".format(tag))
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/tags/delete', endpoint="delete tags")
class AddTag(Resource):
    """
        Deletes a tag from the Tag model
    """

    parser = requestparse(['tag'], [str], ["tag to delete"], [True])

    @admin_required
    def post(self):
        args = self.parser.parse_args()
        tag = args['tag']
        message = "Tag is deleted successfully"
        status = "success"
        try:
            tags = tag.split(',')
            if tag:
                current_app.logger.warning("Tag {} is requested for deletion".format(tags))
                tags=[ tags_dao.get_tag_by_value(tag) for tag in tags]
                for tag in tags:
                    tags_dao.delete_tag(tag)
            else:
                message = "Tag does not exists!"
        except Exception as e:
            message = str(e)
            status = "failure"
            current_app.logger.error("Unable to delete tag - {}".format(message))
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)


@api.resource('/tags/tagged', endpoint='objects tagged')
class TaggedList(Resource):
    """
        List Nodes, Queries, Packs Details of a Tag
    """
    parser = requestparse(['tags'], [str], ["tags names separated by a comma"], [True])
    
    def post(self):
        from polylogyx.dao.v1 import queries_dao, hosts_dao, packs_dao
        from polylogyx.wrappers.v1 import pack_wrappers
        args = self.parser.parse_args()
        tag_names = args['tags'].split(',')
        tags = tags_dao.get_tags_by_names(tag_names)
        if tags:
            hosts = [node.get_dict() for node in hosts_dao.get_tagged_nodes(tag_names) if node.state != node.DELETED and node.state != node.REMOVED]

            packs_queryset = packs_dao.get_tagged_packs(tag_names)
            packs = marshal(packs_queryset, pack_wrappers.pack_wrapper)
            for index in range(len(packs)):
                packs[index]['tags'] = [tag.to_dict() for tag in packs_queryset[index].tags]
                packs[index]['queries'] = marshal(packs_queryset[index].queries, query_wrappers.query_wrapper)
                for query_index in range(len(packs_queryset[index].queries)):
                    packs[index]['queries'][query_index]['tags'] = \
                        [tag.to_dict() for tag in packs_queryset[index].queries[query_index].tags]
                    packs[index]['queries'][query_index]['packs'] = \
                        [pack.name for pack in packs_queryset[index].queries[query_index].packs]

            queries_qs = queries_dao.get_tagged_queries(tag_names)
            queries = marshal(queries_qs, query_wrappers.query_wrapper)
            for i in range(len(queries)):
                queries[i]['tags'] = [tag.to_dict() for tag in queries_qs[i].tags]
                queries[i]['packs'] = [pack.name for pack in queries_qs[i].packs]

            message = "All hosts, queries, packs for the tag provided!"
            status = "success"
            return marshal(prepare_response(message, status, {"hosts": hosts, "packs": packs, "queries": queries}),
                           parent_wrappers.common_response_wrapper)
        else:
            return marshal(prepare_response("Tag(s) doesn't exists for the value(s) provided", "failure"),
                           parent_wrappers.common_response_wrapper)


@api.resource('/tags/<string:tag>',  endpoint='tag resource')
class Tag(Resource):
    """
        Tags nodes, packs, queries
    """
    parser = requestparse(['queries', 'packs', 'hosts', 'os_names'],
                          [list, list, list, list],
                          ['queries', 'packs', 'hosts', 'os_names'],
                          [False, False, False, False])

    @admin_required
    def put(self, tag):
        from polylogyx.dao.v1 import queries_dao, packs_dao, hosts_dao
        tag = tags_dao.get_tag_by_value(tag)
        status = 'failure'
        entity_exists = False
        if tag:
            args = self.parser.parse_args()
            if not (args['queries'] or args['packs'] or args['hosts'] or args['os_names']):
                message = 'One of queries/packs/hosts/os_names is required at least!'
            else:
                if args['queries']:
                    queries = queries_dao.get_all_queries_by_names(args['queries'])
                    if queries:
                        tag.queries.extend(queries)
                        entity_exists = True
                        current_app.logger.info("Tag '{0}' is assigned to the queries: {1}".format(tag, queries))
                if args['packs']:
                    packs = packs_dao.get_all_packs_by_names(args['packs'])
                    if packs:
                        tag.packs.extend(packs)
                        entity_exists = True
                        current_app.logger.info("Tag '{0}' is assigned to the packs: {1}".format(tag, packs))
                if args['hosts']:
                    hosts = hosts_dao.get_nodes_by_host_ids(args['hosts'])
                    if hosts:
                        tag.nodes.extend(hosts)
                        entity_exists = True
                        current_app.logger.info("Tag '{0}' is assigned to the hosts: {1}".format(tag, hosts))
                if args['os_names']:
                    hosts = hosts_dao.get_hosts_from_os_names(args['os_names'])
                    if hosts:
                        tag.nodes.extend(hosts)
                        entity_exists = True
                        current_app.logger.info("Tag '{0}' is assigned to the hosts: {1}".format(tag, hosts))
                db.session.add(tag)
                db.session.commit()
                if entity_exists:
                    message = 'Successfully assigned to the tag'
                    status = 'success'
                else:
                    message = 'Provided entity does not exists to tag it!'
        else:
            message = 'Tag name provided does not exists!'
        return marshal(prepare_response(message, status), parent_wrappers.common_response_wrapper)

