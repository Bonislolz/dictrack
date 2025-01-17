# -*- coding: utf-8 -*-

import operator
import sys
from os.path import abspath, dirname, join

import pytest

sys.path.insert(0, abspath(join(dirname(__file__), "..")))
from dictrack.conditions.keys import (
    KeyExists,
    KeyNotExists,
    KeyValueComparison,
    KeyValueContained,
    KeyValueEQ,
    KeyValueGE,
    KeyValueGT,
    KeyValueLE,
    KeyValueLT,
    KeyValueNE,
    KeyValueNotContained,
)


def test_key_exists():
    condition1 = KeyExists("name")
    assert condition1.__repr__() == "<KeyExists (key=name)>"

    data1 = {"name": "tim"}
    data2 = {"nickname": "t"}
    assert condition1.check(data1) is True
    assert condition1.check(data2) is False

    condition2 = KeyExists("name")
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_not_exists():
    condition1 = KeyNotExists("name")
    assert condition1.__repr__() == "<KeyNotExists (key=name)>"

    data1 = {"name": "tim"}
    data2 = {"nickname": "t"}
    assert condition1.check(data1) is False
    assert condition1.check(data2) is True

    condition2 = KeyNotExists("name")
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_value_comparison():
    condition_eq = KeyValueComparison("age", 10)
    assert (
        condition_eq.__repr__() == "<KeyValueComparison (key=age operator=eq value=10)>"
    )

    data1 = {"age": 10}
    data2 = {"age": 11}
    data3 = {"name": "tim"}
    assert condition_eq.check(data1) is True
    assert condition_eq.check(data2) is False
    assert condition_eq.check(data3) is False

    condition_eq2 = KeyValueComparison("age", 10)
    assert condition_eq == condition_eq2

    set_conditions = set([condition_eq, condition_eq2])
    assert len(set_conditions) == 1

    condition_gt = KeyValueComparison("age", 10, op=operator.gt)
    assert condition_gt.check(data1) is False
    assert condition_gt.check(data2) is True
    assert condition_gt.check(data3) is False

    condition_ge = KeyValueComparison("age", 10, op=operator.ge)
    assert condition_ge.check(data1) is True
    assert condition_ge.check(data2) is True
    assert condition_ge.check(data3) is False

    condition_lt = KeyValueComparison("age", 10, op=operator.lt)
    data4 = {"age": 9}
    assert condition_lt.check(data1) is False
    assert condition_lt.check(data4) is True
    assert condition_lt.check(data3) is False

    condition_le = KeyValueComparison("age", 10, op=operator.le)
    assert condition_le.check(data1) is True
    assert condition_le.check(data4) is True
    assert condition_le.check(data3) is False

    condition_ne = KeyValueComparison("age", 10, op=operator.ne)
    assert condition_ne.check(data1) is False
    assert condition_ne.check(data2) is True
    assert condition_ne.check(data3) is False

    with pytest.raises(ValueError):
        KeyValueComparison("age", 10, op="eq")


def test_key_value_eq():
    condition1 = KeyValueEQ("age", 10)
    assert condition1.__repr__() == "<KeyValueEQ (key=age operator=eq value=10)>"

    data1 = {"age": 10}
    data2 = {"age": 11}
    data3 = {"name": "tim"}
    assert condition1.check(data1) is True
    assert condition1.check(data2) is False
    assert condition1.check(data3) is False

    condition2 = KeyValueEQ("age", 10)
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_value_ne():
    condition1 = KeyValueNE("age", 10)
    assert condition1.__repr__() == "<KeyValueNE (key=age operator=ne value=10)>"

    data1 = {"age": 10}
    data2 = {"age": 11}
    data3 = {"name": "tim"}
    assert condition1.check(data1) is False
    assert condition1.check(data2) is True
    assert condition1.check(data3) is False

    condition2 = KeyValueNE("age", 10)
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_value_gt():
    condition1 = KeyValueGT("age", 10)
    assert condition1.__repr__() == "<KeyValueGT (key=age operator=gt value=10)>"

    data1 = {"age": 10}
    data2 = {"age": 11}
    data3 = {"name": "tim"}
    assert condition1.check(data1) is False
    assert condition1.check(data2) is True
    assert condition1.check(data3) is False

    condition2 = KeyValueGT("age", 10)
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_value_ge():
    condition1 = KeyValueGE("age", 10)
    assert condition1.__repr__() == "<KeyValueGE (key=age operator=ge value=10)>"

    data1 = {"age": 10}
    data2 = {"age": 11}
    data3 = {"name": "tim"}
    assert condition1.check(data1) is True
    assert condition1.check(data2) is True
    assert condition1.check(data3) is False

    condition2 = KeyValueGE("age", 10)
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_value_lt():
    condition1 = KeyValueLT("age", 10)
    assert condition1.__repr__() == "<KeyValueLT (key=age operator=lt value=10)>"

    data1 = {"age": 10}
    data2 = {"age": 9}
    data3 = {"name": "tim"}
    assert condition1.check(data1) is False
    assert condition1.check(data2) is True
    assert condition1.check(data3) is False

    condition2 = KeyValueLT("age", 10)
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_value_le():
    condition1 = KeyValueLE("age", 10)
    assert condition1.__repr__() == "<KeyValueLE (key=age operator=le value=10)>"

    data1 = {"age": 10}
    data2 = {"age": 9}
    data3 = {"name": "tim"}
    assert condition1.check(data1) is True
    assert condition1.check(data2) is True
    assert condition1.check(data3) is False

    condition2 = KeyValueLE("age", 10)
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1


def test_key_value_contained():
    condition1 = KeyValueContained("name", "tim")
    assert (
        condition1.__repr__()
        == "<KeyValueContained (key=name value=tim case_sensitive=True)>"
    )

    data1 = {"name": "tim liao"}
    data2 = {"name": "tom liao"}
    data3 = {"nickname": "t"}
    data4 = {"name": "Tim Liao"}
    data5 = {"name": "timmy Liao"}
    assert condition1.check(data1) is True
    assert condition1.check(data2) is False
    assert condition1.check(data3) is False
    assert condition1.check(data4) is False
    assert condition1.check(data5) is True

    condition2 = KeyValueContained("name", "tim")
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1

    condition_non_case_sensitive = KeyValueContained(
        "name", "tim", case_sensitive=False
    )
    assert (
        condition_non_case_sensitive.__repr__()
        == "<KeyValueContained (key=name value=tim case_sensitive=False)>"
    )

    data1 = {"name": "tim liao"}
    data2 = {"name": "tom liao"}
    data3 = {"nickname": "t"}
    data4 = {"name": "Tim Liao"}
    data5 = {"name": "timmy Liao"}
    assert condition_non_case_sensitive.check(data1) is True
    assert condition_non_case_sensitive.check(data2) is False
    assert condition_non_case_sensitive.check(data3) is False
    assert condition_non_case_sensitive.check(data4) is True
    assert condition_non_case_sensitive.check(data5) is True


def test_key_value_not_contained():
    condition1 = KeyValueNotContained("name", "tim")
    assert (
        condition1.__repr__()
        == "<KeyValueNotContained (key=name value=tim case_sensitive=True)>"
    )

    data1 = {"name": "tim liao"}
    data2 = {"name": "tom liao"}
    data3 = {"nickname": "t"}
    data4 = {"name": "Tim Liao"}
    data5 = {"name": "timmy Liao"}
    assert condition1.check(data1) is False
    assert condition1.check(data2) is True
    assert condition1.check(data3) is False
    assert condition1.check(data4) is True
    assert condition1.check(data5) is False

    condition2 = KeyValueNotContained("name", "tim")
    assert condition1 == condition2

    set_conditions = set([condition1, condition2])
    assert len(set_conditions) == 1

    condition_non_case_sensitive = KeyValueNotContained(
        "name", "tim", case_sensitive=False
    )
    assert (
        condition_non_case_sensitive.__repr__()
        == "<KeyValueNotContained (key=name value=tim case_sensitive=False)>"
    )

    data1 = {"name": "tim liao"}
    data2 = {"name": "tom liao"}
    data3 = {"nickname": "t"}
    data4 = {"name": "Tim Liao"}
    data5 = {"name": "timmy Liao"}
    assert condition_non_case_sensitive.check(data1) is False
    assert condition_non_case_sensitive.check(data2) is True
    assert condition_non_case_sensitive.check(data3) is False
    assert condition_non_case_sensitive.check(data4) is False
    assert condition_non_case_sensitive.check(data5) is False
