# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod, abstractproperty

from polylogyx.utils.compat import with_metaclass


class AbstractLogsPlugin(with_metaclass(ABCMeta)):
    @abstractproperty
    def name(self):  # pragma : no cover
        pass

    @abstractmethod
    def handle_status(self, data, **kwargs):  # pragma : no cover
        pass

    @abstractmethod
    def handle_result(self, data, **kwargs):  # pragma : no cover
        pass

    @abstractmethod
    def handle_recon(self, data, **kwargs):  # pragma : no cover
        pass
