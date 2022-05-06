# # -*- coding: utf-8 -*-
from polylogyx.celery.tasks import example_task


class TestCelery:
    def test_celery_simple(self,celery_worker):
        res = example_task.delay(1, 2)
        assert res.get() == 3
