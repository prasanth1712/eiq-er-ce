# -*- coding: utf-8 -*-

import string

import jinja2

# Not super-happy that we're duplicating this both here and in the JS, but I
# couldn't think of a nice way to pass from JS --> Python (or the other
# direction).
PRETTY_OPERATORS = {
    "equal": "equals",
    "not_equal": "doesn't equal",
    "begins_with": "begins with",
    "not_begins_with": "doesn't begins with",
    "contains": "contains",
    "not_contains": "doesn't contain",
    "ends_with": "ends with",
    "not_ends_with": "doesn't end with",
    "is_empty": "is empty",
    "is_not_empty": "is not empty",
    "less": "less than",
    "less_or_equal": "less than or equal",
    "greater": "greater than",
    "greater_or_equal": "greater than or equal",
    "matches_regex": "matches regex",
    "not_matches_regex": "doesn't match regex",
}


def pretty_operator(cond):
    return PRETTY_OPERATORS.get(cond, cond)


PRETTY_FIELDS = {
    "query_name": "Query name",
    "action": "Action",
    "host_identifier": "Host identifier",
    "timestamp": "Timestamp",
}


def pretty_field(field):
    return PRETTY_FIELDS.get(field, field)


_js_escapes = {
    "\\": "\\u005C",
    "'": "\\u0027",
    '"': "\\u0022",
    ">": "\\u003E",
    "<": "\\u003C",
    "&": "\\u0026",
    "=": "\\u003D",
    "-": "\\u002D",
    ";": "\\u003B",
    u"\u2028": "\\u2028",
    u"\u2029": "\\u2029",
}
# Escape every ASCII character with a value less than 32.
_js_escapes.update(("%c" % z, "\\u%04X" % z) for z in range(32))


def jinja2_escapejs_filter(value):
    retval = []
    if not value:
        return ""
    else:
        for letter in value:
            if letter in _js_escapes.keys():
                retval.append(_js_escapes[letter])
            else:
                retval.append(letter)

        return jinja2.Markup("".join(retval))


# Since 'string.printable' includes control characters
PRINTABLE = string.ascii_letters + string.digits + string.punctuation + " "


def quote(s, quote='"'):
    buf = [quote]
    for ch in s:
        if ch == quote or ch == "\\":
            buf.append("\\")
            buf.append(ch)
        elif ch == "\n":
            buf.append("\\n")
        elif ch == "\r":
            buf.append("\\r")
        elif ch == "\t":
            buf.append("\\t")
        elif ch in PRINTABLE:
            buf.append(ch)
        else:
            # Hex escape
            buf.append("\\x")
            buf.append(hex(ord(ch))[2:])

    buf.append(quote)
    return "".join(buf)
