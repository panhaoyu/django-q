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
    def _get_model_instances(obj):
        all_args = ()
        if isinstance(obj, dict) and ('args' in obj or 'kwargs' in obj):
            args, kwargs = obj.get('args', ()), obj.get('kwargs', {})
            if isinstance(args, tuple):
                all_args = (*args,)
            if isinstance(kwargs, dict):
                all_args = (*kwargs.values(),)
        all_args = tuple(arg for arg in all_args if isinstance(arg, models.Model))
        return all_args

    @staticmethod
    def dumps(obj) -> bytes:
        for arg in PickleSerializer._get_model_instances(obj):
            arg.__dict__ = {k: v for k, v in arg.__dict__.items() if k in ('id',)}
        return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def loads(obj) -> any:
        obj = pickle.loads(obj)
        for arg in PickleSerializer._get_model_instances(obj):
            arg.refresh_from_db()
        return obj
