"""Package signing."""
import pickle

from django.db import models

from django_q import core_signing as signing
from django_q.conf import Conf

BadSignature = signing.BadSignature


class SignedPackage:
    """Wraps Django's signing module with custom Pickle serializer."""

    @staticmethod
    def dumps(obj, compressed: bool = Conf.COMPRESSED) -> str:
        return signing.dumps(
            obj,
            key=Conf.SECRET_KEY,
            salt=Conf.PREFIX,
            compress=compressed,
            serializer=PickleSerializer,
        )

    @staticmethod
    def loads(obj) -> any:
        return signing.loads(
            obj, key=Conf.SECRET_KEY, salt=Conf.PREFIX, serializer=PickleSerializer
        )


class PickleSerializer:
    """Simple wrapper around Pickle for signing.dumps and signing.loads."""

    @staticmethod
    def dumps(obj) -> bytes:
        if isinstance(obj, dict):
            if isinstance(args := obj.get('args', None), tuple):
                obj['args'] = tuple(type(v)(pk=v.pk) if isinstance(v, models.Model) else v for v in args)
            if isinstance(kw := obj.get('kwargs', None), dict):
                obj['kwargs'] = {k: type(v)(pk=v.pk) if isinstance(v, models.Model) else v for k, v in kw.items()}
        return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def loads(obj) -> any:
        obj = pickle.loads(obj)
        if isinstance(obj, dict):
            if isinstance(args := obj.get('args', None), tuple):
                [v.refresh_from_db() for v in args if isinstance(v, models.Model)]
            if isinstance(kw := obj.get('kwargs', None), dict):
                [v.refresh_from_db() for v in kw.values() if isinstance(v, models.Model)]
        return obj
