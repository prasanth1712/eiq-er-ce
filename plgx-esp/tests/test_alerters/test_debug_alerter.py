from polylogyx.plugins.alerters.debug import DebugAlerter

class TestDebugAlerter:

    def test_init(self):
        da = DebugAlerter(config={"level":"critical"})
        assert da.level == DebugAlerter.LEVEL_MAPPINGS["critical"]

    def test_handle_alert(self):
        da = DebugAlerter(config={"level":"critical"})
        da.handle_alert(None,None,None)
        assert True