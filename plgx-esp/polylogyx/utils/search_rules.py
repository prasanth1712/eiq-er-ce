# from operator import and_, or_

import six
from sqlalchemy import and_, or_

from polylogyx.db.models import ResultLog
from polylogyx.utils.rules import logger


class BaseCondition(object):
    """
    Base class for conditions.  Contains the logic for adding a dependency to a
    condition and pretty-printing one.
    """

    def __init__(self):
        self.evaluated = False
        self.cached_value = None
        self.network = None
        self.type = None

    def init_network(self, network):
        self.network = network

    def run(self, input, filter, type):
        """
        Runs this condition if it hasn't been evaluated.
        """
        self.type = type

        logger.debug("Evaluating condition %r on input: %r", self, input)
        if self.evaluated:
            logger.debug("Returning cached value: %r", self.cached_value)
            return self.cached_value

        ret = self.local_run(input, filter, type)
        logger.debug("Condition %r returned value: %r", self, ret)
        self.cached_value = ret
        self.evaluated = True
        return ret

    def local_run(self, input, filter, type):
        """
        Subclasses should implement this in order to run the condition's logic.
        """
        raise NotImplementedError()

    def __repr__(self):
        return "<{0} (evaluated={1})>".format(self.__class__.__name__, self.evaluated)


class AndCondition(BaseCondition):
    def __init__(self, upstream):
        super(AndCondition, self).__init__()
        self.upstream = upstream

    def local_run(self, query, filter, type):
        filter_and = []
        for u in self.upstream:
            filter_and = u.run(input, filter_and, type)
        filter.append(and_(*filter_and))
        return filter


class OrCondition(BaseCondition):
    def __init__(self, upstream):
        super(OrCondition, self).__init__()
        self.upstream = upstream

    def local_run(self, input, filter, type):
        filter_or = []
        for u in self.upstream:
            filter_or = u.run(input, filter_or, type)
        filter.append(or_(*filter_or))
        return filter


class LogicCondition(BaseCondition):
    def __init__(self, key, expected, column_name=None):
        super(LogicCondition, self).__init__()
        self.key = key
        self.expected = self.maybe_make_number(expected)
        self.column_name = column_name
        self.filters = ()
        self.current_filter = ()

    def maybe_make_number(self, value):
        if not isinstance(value, six.string_types):
            return value

        if value.isdigit():
            return int(value)
        elif "." in value and value.replace(".", "", 1).isdigit():
            return float(value)

        return value

    def local_run(self, input, filter, type):
        # If we have a 'column_name', we should use that to extract the value
        # from the input's columns.  Otherwise, we have a whitelist of what we
        # can get from the input.
        print(self.column_name)

        value = "abc"
        # Pass to the actual logic function
        logger.debug("Running logic condition %r: %r | %r", self, self.expected, value)
        try:
            return self.compare(value, filter, type)
        except Exception:
            return False

    def compare(self, value, filter, type):
        """
        Subclasses should implement this to run the actual comparison.
        """
        raise NotImplementedError()


class EqualCondition(LogicCondition):
    def compare(self, value, filter, type):
        filter.append(ResultLog.columns[self.column_name].astext == self.expected.lower())
        return filter


class NotEqualCondition(LogicCondition):
    def compare(self, value):
        return value.lower() != self.expected.lower()


class BeginsWithCondition(LogicCondition):
    def compare(self, value):
        return value.lower().startswith(self.expected.lower())


class NotBeginsWithCondition(LogicCondition):
    def compare(self, value):
        return not value.lower().startswith(self.expected.lower())


class ContainsCondition(LogicCondition):
    def compare(self, value, filter, type):
        filter.append(ResultLog.columns[self.column_name].astext.ilike("%" + self.expected.lower() + "%"))
        return filter


class NotContainsCondition(LogicCondition):
    def compare(self, value):
        return self.expected.lower() not in value.lower()


class EndsWithCondition(LogicCondition):
    def compare(self, value):
        return value.lower().endswith(self.expected.lower())


class NotEndsWithCondition(LogicCondition):
    def compare(self, value):
        return not value.lower().endswith(self.expected.lower())


class IsEmptyCondition(LogicCondition):
    def compare(self, value):
        return value == ""


class IsNotEmptyCondition(LogicCondition):
    def compare(self, value):
        return value != ""


class LessCondition(LogicCondition):
    def compare(self, value):
        return value < self.expected


class LessEqualCondition(LogicCondition):
    def compare(self, value):
        return value <= self.expected


class GreaterCondition(LogicCondition):
    def compare(self, value):
        return value > self.expected


class GreaterEqualCondition(LogicCondition):
    def compare(self, value):
        return value >= self.expected


class IsAsciiCondition(LogicCondition):
    def compare(self, value):
        return not all(ord(c) < 128 for c in value)


# Needs to go at the end
OPERATOR_MAP = {
    "equal": EqualCondition,
    "not_equal": NotEqualCondition,
    "begins_with": BeginsWithCondition,
    "not_begins_with": NotBeginsWithCondition,
    "contains": ContainsCondition,
    "not_contains": NotContainsCondition,
    "ends_with": EndsWithCondition,
    "not_ends_with": NotEndsWithCondition,
    "is_empty": IsEmptyCondition,
    "is_not_empty": IsNotEmptyCondition,
    "less": LessCondition,
    "less_or_equal": LessEqualCondition,
    "greater": GreaterCondition,
    "greater_or_equal": GreaterEqualCondition,
}
