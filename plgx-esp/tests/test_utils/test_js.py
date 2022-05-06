from polylogyx.utils import js


class Testjs:
    def test_pretty_operator(self):
        assert js.pretty_operator("equal") == "equals"

    def test_pretty_field(self):
        assert js.pretty_field("action")=="Action"

    def test_jinja2_esacpejs_filter_no_input(self):
        assert js.jinja2_escapejs_filter(None) == ""

    def test_jinja2_esacpejs_filter(self):
        assert js.jinja2_escapejs_filter("test") == "test"
        assert js.jinja2_escapejs_filter("=") == "\\u003D"
