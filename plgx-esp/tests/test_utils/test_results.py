from polylogyx.utils import results
from flask import current_app

class TestResults:

    def test_learn_from_results_no_data(self):
        assert results.learn_from_result({"data":None},None) is None

    def test_learn_from_results_no_capture_columns(self,app):
        current_app.config["POLYLOGYX_CAPTURE_NODE_INFO"]=[]
        assert results.learn_from_result({"data":"Test"},None) is None