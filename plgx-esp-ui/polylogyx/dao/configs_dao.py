from polylogyx.models import DefaultQuery, DefaultFilters, db, Config


def get_all_configs():
    from polylogyx.models import DefaultQuery, DefaultFilters, Config
    platforms = ["windows", "linux", "darwin"]
    type_mapping = {0:'default', 1:'shallow', 2:'deep'}
    config_data = {}
    default_queries = DefaultQuery.query.filter(DefaultQuery.platform.in_(platforms)) \
        .filter(DefaultQuery.arch.in_([DefaultQuery.ARCH_x86, DefaultQuery.ARCH_x64])) \
        .filter(Config.type.in_([Config.TYPE_DEEP, Config.TYPE_SHALLOW,
                                 Config.TYPE_DEFAULT])).all()

    for query in default_queries:
        if not query.config:
            type=Config.TYPE_DEEP
            query_status=False
        else:
            type = query.config.type
            query_status = query.config.is_default
        if not query.platform in config_data:
            config_data[query.platform] = {}
        if not query.arch in config_data[query.platform]:
            config_data[query.platform][query.arch] = {}
        if not type in config_data[query.platform][query.arch]:
            config_data[query.platform][query.arch][type] = {"queries": {}}

        config_data[query.platform][query.arch][type]['status'] = query_status
        config_data[query.platform][query.arch][type]["queries"][query.name] = query.to_dict()

    default_filters = DefaultFilters.query.filter(DefaultFilters.platform.in_(platforms)) \
        .filter(DefaultFilters.arch.in_([DefaultFilters.ARCH_x86, DefaultFilters.ARCH_x64])) \
        .filter(Config.type.in_([Config.TYPE_DEEP, Config.TYPE_SHALLOW,
                                 Config.TYPE_DEFAULT])).all()

    for filter in default_filters:
        if not filter.config:
            type=Config.TYPE_DEEP
            filter_status=False
        else:
            type = filter.config.type
            filter_status = filter.config.is_default

        if not filter.platform in config_data:
            config_data[filter.platform] = {}
        if not filter.arch in config_data[filter.platform]:
            config_data[filter.platform][filter.arch] = {}
        if not type in config_data[filter.platform][filter.arch]:
            config_data[filter.platform][filter.arch][type] = {"filters": {}}
        config_data[filter.platform][filter.arch][type]["filters"] = filter.filters
        config_data[filter.platform][filter.arch][type]['status'] = filter_status
    return config_data


def get_config_by_platform(platform, arch, type):
    return db.session.query(Config).filter(Config.arch == arch).filter(Config.platform == platform).filter(
        Config.type == type).first()


def edit_config_by_platform(config, filters, queries):
    arch = config.arch
    platform = config.platform
    type = config.type
    # fetching the filters data to insert to the config dict
    if arch and arch == DefaultFilters.ARCH_x86:
        default_filters_obj = DefaultFilters.query.filter(DefaultFilters.platform == platform.lower()).filter(
            DefaultFilters.arch == DefaultFilters.ARCH_x86).filter(DefaultFilters.config_id == config.id).first()
    else:
        default_filters_obj = DefaultFilters.query.filter(DefaultFilters.platform == platform.lower()).filter(
            DefaultFilters.arch != DefaultFilters.ARCH_x86).filter(DefaultFilters.config_id == config.id).first()
    if default_filters_obj:
        default_filters_obj.update(filters=filters)

    for key in list(queries.keys()):
        if arch and arch == DefaultQuery.ARCH_x86:
            query = DefaultQuery.query.filter(DefaultQuery.name == key).filter(
                DefaultQuery.arch == DefaultQuery.ARCH_x86).filter(
                DefaultQuery.platform == platform.lower()).filter(DefaultQuery.config_id == config.id).first()
        else:
            query = DefaultQuery.query.filter(DefaultQuery.name == key).filter(
                DefaultQuery.arch != DefaultQuery.ARCH_x86).filter(
                DefaultQuery.platform == platform.lower()).filter(DefaultQuery.config_id == config.id).first()
        if query:
            query = query.update(status=queries[key]['status'],
                                 interval=queries[key]['interval'])
    if arch and arch == DefaultQuery.ARCH_x86:
        queries = {query.name: {'status': query.status, 'interval': query.interval} for query in DefaultQuery.query.filter(
                DefaultQuery.arch == DefaultQuery.ARCH_x86).filter(
                DefaultQuery.platform == platform.lower()).filter(DefaultQuery.config_id == config.id).all()}
        filters = DefaultFilters.query.filter(DefaultFilters.platform == platform.lower()).filter(
            DefaultFilters.arch == DefaultFilters.ARCH_x86).filter(DefaultFilters.config_id == config.id).first()
    else:
        queries = {query.name: {'status': query.status, 'interval': query.interval} for query in
                   DefaultQuery.query.filter(
                       DefaultQuery.arch != DefaultQuery.ARCH_x86).filter(
                       DefaultQuery.platform == platform.lower()).filter(DefaultQuery.config_id == config.id).all()}
        filters = DefaultFilters.query.filter(DefaultFilters.platform == platform.lower()).filter(
            DefaultFilters.arch != DefaultFilters.ARCH_x86).filter(DefaultFilters.config_id == config.id).first()
    if filters:
        filters = filters.filters
    else:
        filters = {}
    config_data = {"queries": queries, "filters": filters}
    return config_data
