# -*- coding: utf-8 -*-

import operator
from functools import wraps

import six


def valid_type(obj, expected_types, allow_empty=False):
    """
    Validate if the object matches the expected types.

    Parameters
    ----------
    obj : object
        The object to be validated.
    expected_types : type or tuple or list of types
        A type or a tuple/list of types that `obj` is expected to match.
    allow_empty : bool, optional
        If set to `True`, allows `obj` to be `None`. Defaults to `False`.

    Raises
    ------
    TypeError
        If `obj` is not an instance of `expected_types`.
    """
    if not isinstance(expected_types, (tuple, list)):
        expected_types = (expected_types,)

    if allow_empty and obj is None:
        return

    if not isinstance(obj, expected_types):
        raise TypeError(
            "{} is not in the expected types: {}".format(
                type(obj).__name__, ", ".join([t.__name__ for t in expected_types])
            )
        )


def valid_obj(obj, expected_objs, allow_empty=False):
    """
    Validate if the given object is one of the expected objects.

    Parameters
    ----------
    obj : object
        The object to be validated.
    expected_objs : tuple or list
        A single object or a tuple/list of expected objects that `obj` should match.
    allow_empty : bool, optional
        If set to `True`, allows `obj` to be `None`. Defaults to `False`.

    Raises
    ------
    ValueError
        If `obj` is not in `expected_objs`.
    """
    if not isinstance(expected_objs, (tuple, list)):
        expected_objs = (expected_objs,)

    if allow_empty and obj is None:
        return

    if obj not in expected_objs:
        raise ValueError(
            "{} is not in the expected objects: {}".format(
                obj, ", ".join([str(o) for o in expected_objs])
            )
        )


def valid_callable(obj):
    """
    Validate if the given object is callable.

    Parameters
    ----------
    obj : object
        The object to be validated.

    Raises
    ------
    TypeError
        If `obj` is not callable.
    """
    if not callable(obj):
        raise TypeError("{} is not callable".format(type(obj).__name__))


def valid_elements_type(obj, expected_types, allow_empty=False):
    """
    Validate if all elements in an iterable match the expected types.

    Parameters
    ----------
    obj : list or set or tuple
        An iterable whose elements will be validated.
    expected_types : type or tuple of types
        The expected type(s) that each element in `obj` should match.
    allow_empty : bool, optional
        If set to `True`, allows elements in `obj` to be `None`. Defaults to `False`.

    Raises
    ------
    TypeError
        If `obj` is not a list, set, or tuple, or if any element does not match `expected_types`.
    """
    valid_type(obj, (list, set, tuple), allow_empty=allow_empty)

    if obj is None:
        return

    for element in obj:
        valid_type(element, expected_types, allow_empty=allow_empty)


def valid_elements_obj(obj, expected_objs, allow_empty=False):
    """
    Validate if all elements in an iterable match the expected objects.

    Parameters
    ----------
    obj : list or set or tuple
        An iterable whose elements will be validated.
    expected_objs : object or tuple or list of objects
        The expected object(s) that each element in `obj` should match.
    allow_empty : bool, optional
        If set to `True`, allows elements in `obj` to be `None`. Defaults to `False`.

    Raises
    ------
    TypeError
        If `obj` is not a list, set, or tuple.
    ValueError
        If any element in `obj` does not match `expected_objs`.
    """
    valid_type(obj, (list, set, tuple), allow_empty=allow_empty)

    if obj is None:
        return

    for element in obj:
        valid_obj(element, expected_objs, allow_empty=allow_empty)


GLOBAL_DEFINES = {
    "group_id": six.string_types,
    "data": dict,
    "b_tracker": six.binary_type,
}


def typecheck(type_definitions=GLOBAL_DEFINES, allow_empty=False):
    """
    Decorator that checks and validates the types of method arguments based on a type definition table.

    Parameters
    ----------
    type_definitions : dict, optional
        A dictionary mapping argument names to their expected types, which can be a type or a tuple/list of types.
        Defaults to `GLOBAL_DEFINES` if not provided.
    allow_empty : bool, optional
        If `True`, allows arguments to be `None` even if their type is defined in `type_definitions`.
        Defaults to `False`.

    Returns
    -------
    callable
        A decorated function that checks argument types before execution.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the argument names of the function
            arg_names = func.__code__.co_varnames[: func.__code__.co_argcount]

            # Check positional arguments
            for i, arg in enumerate(args):
                if i < len(arg_names) and arg_names[i] in type_definitions:
                    expected_types = type_definitions[arg_names[i]]
                    valid_type(arg, expected_types, allow_empty)

            # Check keyword arguments
            for kwarg, value in kwargs.items():
                if kwarg in type_definitions:
                    expected_types = type_definitions[kwarg]
                    valid_type(value, expected_types, allow_empty)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def numeric(value, allow_empty=False):
    """
    Coerce the value to a numeric form, or raise an error if the coercion fails.

    Parameters
    ----------
    value : object
        The value to be coerced.
    allow_empty : bool, optional
        Flag indicating whether `None` is allowed as a valid value. Defaults to `False`.

    Raises
    ------
    ValueError
        If the value is `None` and `allow_empty` is `False`, or if it cannot be coerced into a numeric form,
        or if it is not a valid numeric type.

    Returns
    -------
    int or float
        The coerced numeric value.
    """
    if value is None and not allow_empty:
        raise ValueError("Value ({}) is empty".format(value))
    elif value is not None:
        if isinstance(value, str):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(
                    "Value ({}) cannot be coerced to numeric form".format(value)
                )
        elif not isinstance(value, six.integer_types + (float,)):
            raise ValueError(
                "Value ({}) is not a numeric type, was {}".format(
                    value, type(value).__name__
                )
            )

    return value


STR_TO_OP_MAPPING = {}
for op in (
    operator.eq,
    operator.ne,
    operator.lt,
    operator.le,
    operator.gt,
    operator.ge,
):
    STR_TO_OP_MAPPING[op.__str__()] = op


def str_to_operator(ref):
    """
    Return the operator corresponding to the given string reference.

    Parameters
    ----------
    ref : str
        The string reference of an operator.

    Raises
    ------
    TypeError
        If `ref` is not a string.
    ValueError
        If `ref` does not correspond to a valid operator.

    Returns
    -------
    callable
        The operator corresponding to `ref`.
    """
    valid_type(ref, six.string_types)

    obj = STR_TO_OP_MAPPING.get(ref, None)
    if obj is None:
        raise ValueError("`ref` ({}) is invalid".format(ref))

    return obj
