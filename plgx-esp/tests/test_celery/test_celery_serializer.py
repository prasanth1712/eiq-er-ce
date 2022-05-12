from polylogyx.celery.celery_serializer import DJSONEncoder,djson_loads
import pytest

class TestCelerySerializer:

    def test_djsonencoder(self):
        obj = DJSONEncoder()
        with pytest.raises(TypeError):
            obj.default("Test")

    

