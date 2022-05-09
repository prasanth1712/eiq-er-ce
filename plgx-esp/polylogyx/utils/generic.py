# -*- coding: utf-8 -*-

import json
from datetime import datetime as dt1

from flask import current_app
from jinja2 import Markup, Template

from polylogyx.db.models import Tag


def merge_two_dicts(x, y):
    if not x:
        x = {}
    if not y:
        y = {}
    z = x.copy()  # start with x's keys and values
    z.update(y)  # modifies z with y's keys and values & returns None
    return z


def flatten_json(input):
    output = dict(input)
    if "columns" in output:
        for key, value in output["columns"].items():
            output[key] = value
            output.pop("columns", None)

    return output


class Serializer(object):
    @staticmethod
    def serialize(object):
        return json.dumps(object, default=lambda o: o.__dict__.values()[0])


def is_wildcard_match(raw_string, pattern):
    string_length = len(raw_string)
    pattern_length = len(pattern)
    dp = [[False for i in range(pattern_length + 1)] for j in range(string_length + 1)]
    raw_string = " " + raw_string
    pattern = " " + pattern
    dp[0][0] = True
    for i in range(1, pattern_length + 1):
        if pattern[i] == "*":
            dp[0][i] = dp[0][i - 1]
    for i in range(1, string_length + 1):
        for j in range(1, pattern_length + 1):
            if raw_string[i] == pattern[j] or pattern[j] == "?":
                dp[i][j] = dp[i - 1][j - 1]
            elif pattern[j] == "*":
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[string_length][pattern_length]


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, dt1):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)
