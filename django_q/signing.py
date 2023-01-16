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
    def _dump_model_instance(value_or_obj):
        if isinstance(value_or_obj, models.Model):
            return type(value_or_obj), value_or_obj.pk
        else:
            return value_or_obj

    @staticmethod
    def _load_model_instance(value_or_obj):
        if isinstance(value_or_obj, tuple) and len(value_or_obj) == 2:
            cls, pk = value_or_obj
            if issubclass(cls, models.Model):
                obj = cls(pk=pk)
                obj.refresh_from_db()
                return obj
        else:
            return value_or_obj

    @staticmethod
    def dumps(obj) -> bytes:
        if isinstance(obj, dict):
            if isinstance(args := obj.get('args', None), tuple):
                obj['args'] = tuple(PickleSerializer._dump_model_instance(v) for v in args)
            if isinstance(kw := obj.get('kwargs', None), dict):
                obj['kwargs'] = {k: PickleSerializer._dump_model_instance(v) for k, v in kw.items()}
        return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def loads(obj) -> any:
        obj = pickle.loads(obj)
        if isinstance(obj, dict):
            if isinstance(args := obj.get('args', None), tuple):
                obj['args'] = tuple(PickleSerializer._load_model_instance(v) for v in args)
            if isinstance(kw := obj.get('kwargs', None), dict):
                obj['kwargs'] = {k: PickleSerializer._load_model_instance(v) for k, v in kw.items()}
        return obj
