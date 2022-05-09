# -*- coding: utf-8 -*-
import ast, os, copy


# This has to be a global due to `exec` shenanigans :-(
current_spec = {}

# SQL types
SQL_TYPES = [
    'TEXT',
    'DATE',
    'DATETIME',
    'INTEGER',
    'BIGINT',
    'UNSIGNED_BIGINT',
    'DOUBLE',
    'BLOB',
]

# Functions that we don't need
DUMMY_FUNCTIONS = [
    'ForeignKey',
    'attributes',
    'examples',
    'implementation',
    'fuzz_paths',
    'WINDOWS',
    'POSIX',
    'LINUX',
    'DARWIN',
]


RESERVED_KEYWORDS = [
    'table',
    'set',
]


def table_name(name, aliases=None):
    current_spec['name'] = name
    current_spec['aliases'] = aliases


def description(description, *args, **kwargs):
    current_spec['description'] = description


def Column(name, col_type, *args, **kwargs):
    if name in RESERVED_KEYWORDS:
        name = '"%s"' % name
    return (name, col_type)


def ColumnJson(name, col_type, description, *args, **kwargs):
    if name in RESERVED_KEYWORDS:
        name = '"%s"' % name
    return {name: {"type": col_type, "description": description, "is_required": False}}


def merge_schema(columns_array):
    schema = {}
    for column_dict in columns_array:
        for column_name, type in column_dict.items():
            schema[column_name] = type
    return schema


def schema(schema):
    # Filter out 'None' entries (usually from ForeignKeys)
    real_schema = [x for x in schema if x is not None]
    current_spec['schema'] = real_schema


def extended_schema(macro, schema):
    # Filter out 'None' entries (usually from ForeignKeys)
    real_schema = [x for x in schema if x is not None]
    current_spec.setdefault('extended_schema', []).extend(real_schema)


def get_supported_platforms(filename):
    platforms = []
    path_list = filename.split(os.sep)
    ignore_folders = ["freebsd"]
    dir_platform_like_dict = {"windows": ["windows", "linwin", "macwin", "polylogyx"],
                              "linux": ["linux", "linwin", "lldpd", "sleuthkit", "smart", "yara", "posix"],
                              "darwin": ["darwin", "macwin", "sleuthkit", "smart", "yara", "posix"]}
    if path_list[-2] and path_list[-2] not in ignore_folders:
        for platform, like_dirs in dir_platform_like_dict.items():
            if path_list[-2] and path_list[-2] in like_dirs:
                platforms.append(platform)
        if not platforms:
            platforms = ["windows", "linux", "darwin"]
    return platforms


def extract_schema(filename):
    namespace = {
        'Column': Column,
        'schema': schema,
        'table_name': table_name,
        'description': description,
        'extended_schema': extended_schema,
        'current_spec': {},
    }

    for fn in DUMMY_FUNCTIONS:
        namespace[fn] = lambda *args, **kwargs: None

    for ty in SQL_TYPES:
        namespace[ty] = ty

    with open(filename, 'rU') as f:
        tree = ast.parse(f.read())
        exec(compile(tree, '<string>', 'exec'), namespace)

    columns = ', '.join('%s %s' % (x[0], x[1]) for x in current_spec['schema'])
    statements = []
    statements.append('CREATE TABLE %s (%s);' % (current_spec['name'], columns))
    if 'extended_schema' in current_spec:
        statement = 'ALTER TABLE %s ADD %%s %%s;' % (current_spec['name'], )
        for column_name, column_definition in current_spec['extended_schema']:
            statements.append(statement % (column_name, column_definition))
        del current_spec['extended_schema']
    return '\n'.join(statements)


def extract_schema_json(filename):
    namespace = {
        'Column': ColumnJson,
        'schema': schema,
        'table_name': table_name,
        'description': description,
        'extended_schema': extended_schema,
        'current_spec': {},
    }

    for fn in DUMMY_FUNCTIONS:
        namespace[fn] = lambda *args, **kwargs: None

    for ty in SQL_TYPES:
        namespace[ty] = ty

    with open(filename, 'rU') as f:
        tree = ast.parse(f.read())
        exec(compile(tree, '<string>', 'exec'), namespace)

    current_spec['platform'] = get_supported_platforms(filename)
    current_spec['schema'] = merge_schema(current_spec['schema'])

    table = copy.deepcopy(current_spec)
    if 'extended_schema' in table and table['extended_schema']:
        del table['extended_schema']
    return table


if __name__ == '__main__':
    import sys
    print(extract_schema(sys.argv[1]))
