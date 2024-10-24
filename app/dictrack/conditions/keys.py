# -*- coding: UTF-8 -*-

import operator

from dictor import dictor

from dictrack.conditions.base import BaseCondition
from dictrack.utils.utils import str_to_operator, typecheck, valid_obj


class KeyExists(BaseCondition):
    def __init__(self, key, *args, **kwargs):
        self._key = key

    def __eq__(self, other):
        return self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return "<KeyExists (key={})>".format(self.key)

    def __getstate__(self):
        return {"cls": self.__class__, "key": self.key}

    def __setstate__(self, state):
        self._key = state["key"]

    @property
    def key(self):
        return self._key

    @typecheck()
    def check(self, data, *args, **kwargs):
        result = dictor(data, self.key, default=BaseCondition.DEFAULT)

        return result != BaseCondition.DEFAULT


class KeyValueComparison(KeyExists):
    def __init__(self, key, value, op=operator.eq, *args, **kwargs):
        super(KeyValueComparison, self).__init__(key, *args, **kwargs)

        valid_obj(op, (operator.eq, operator.lt, operator.le, operator.gt, operator.ge))
        self._op = op
        self._value = value

    def __eq__(self, other):
        return (
            self.key == other.key and self.value == other.value and self.op == other.op
        )

    def __hash__(self):
        key_hash = hash(self.key)
        value_hash = hash(self.value)
        op_hash = hash(self.op)

        return hash(str(key_hash) + str(value_hash) + str(op_hash))

    def __repr__(self):
        return "<KeyValueComparison (key={} operator={} value={})>".format(
            self.key, self.op.__name__, self.value
        )

    def __getstate__(self):
        state = super(KeyValueComparison, self).__getstate__()
        state["op"] = self._op.__str__()
        state["value"] = self.value

        return state

    def __setstate__(self, state):
        super(KeyValueComparison, self).__setstate__(state)

        self._op = str_to_operator(state["op"])
        self._value = state["value"]

    @property
    def op(self):
        return self._op

    @property
    def value(self):
        return self._value

    @typecheck()
    def check(self, data, *args, **kwargs):
        if not super(KeyValueComparison, self).check(data, *args, **kwargs):
            return False

        result = dictor(data, self.key)

        return self.op(result, self.value)


class KeyValueEQ(KeyValueComparison):
    def __init__(self, key, value, *args, **kwargs):
        super(KeyValueEQ, self).__init__(key, value, operator.eq, *args, **kwargs)

    def __repr__(self):
        base_repr = super(KeyValueEQ, self).__repr__()
        return base_repr.replace("KeyValueComparison", self.__class__.__name__)


class KeyValueLT(KeyValueEQ):
    def __init__(self, key, value, *args, **kwargs):
        super(KeyValueLT, self).__init__(key, value, *args, **kwargs)
        self._op = operator.lt


class KeyValueLE(KeyValueEQ):
    def __init__(self, key, value, *args, **kwargs):
        super(KeyValueLE, self).__init__(key, value, *args, **kwargs)
        self._op = operator.le


class KeyValueGT(KeyValueEQ):
    def __init__(self, key, value, *args, **kwargs):
        super(KeyValueGT, self).__init__(key, value, *args, **kwargs)
        self._op = operator.gt


class KeyValueGE(KeyValueEQ):
    def __init__(self, key, value, *args, **kwargs):
        super(KeyValueGE, self).__init__(key, value, *args, **kwargs)
        self._op = operator.ge
