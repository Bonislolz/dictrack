# -*- coding: utf-8 -*-

import operator
from functools import wraps

import six


def valid_type(obj, expected_types, allow_empty=False):
    """
    Validate if the object matches the expected types.

    :param `object` obj: The object to be validated.
    :param `type` | `tuple` | `list` expected_types: A `type` or a `tuple`/`list` of types the object is expected to match.
    :param `bool` allow_empty: If set to `True`, allows the object to be `None`. Defaults to `False`.
    :raises `TypeError`: If the object is not an instance of the expected types.
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


def valid_obj(obj, expected_objs):
    """
    Validate if the given object is one of the expected objects.

    :param `object` obj: The object to be validated.
    :param `tuple` | `list` expected_objs: A single object or a `tuple`/`list` of expected objects.
    :raises `ValueError`: If the object is not found in the expected objects.
    """
    if not isinstance(expected_objs, (tuple, list)):
        expected_objs = (expected_objs,)

    if obj not in expected_objs:
        raise ValueError(
            "{} is not in the expected objects: {}".format(
                obj, ", ".join([str(o) for o in expected_objs])
            )
        )


def valid_callable(obj):
    """
    Validate if the given object is callable.

    :param `object` obj: The object to be validated.
    :raises `TypeError`: If the object is not callable.
    """
    if not callable(obj):
        raise TypeError("{} is not callable".format(type(obj).__name__))


GLOBAL_DEFINES = {"group_id": six.string_types, "name": six.string_types, "data": dict}


def typecheck(type_definitions=GLOBAL_DEFINES, allow_empty=False):
    """
    Decorator that checks and validates the types of method arguments based on a type definition table.

    If no `type_definitions` are provided, it uses the global default `GLOBAL_DEFINES`.

    :param `dict` type_definitions: A dictionary mapping argument names to their expected types (can be a `type` or a `tuple`/`list` of types).
                                   Defaults to `GLOBAL_DEFINES` if not provided.
    :param `bool` allow_empty: If set to `True`, allows arguments to be `None` even if their type is defined in `type_definitions`. Defaults to `False`.
    :return: A decorated function that checks argument types before execution.
    :rtype: `callable`
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Wrapper function that checks the types of positional and keyword arguments.

            :param args: Positional arguments passed to the decorated function.
            :param kwargs: Keyword arguments passed to the decorated function.
            :raises `TypeError`: If any argument does not match the expected types defined in `type_definitions`.
            """
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

    :param `object` value: The value to be coerced.
    :param `bool` allow_empty: Flag indicating whether `None` is allowed as a valid value.
    :raises `EmptyValueError`: If the value is `None` and `allow_empty` is `False`.
    :raises `CoerceError`: If the value cannot be coerced into a numeric form or is not a valid numeric type.
    :return: The coerced numeric value.
    :rtype: `int` | `float`
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


def get_callable_name(func):
    """
    Returns the best available display name for the given function/callable.

    :param `callable` func: The function or callable to get the name for.
    :raises `TypeError`: If the name cannot be determined for the callable.
    :return: The best display name for the callable.
    :rtype: `str`
    """

    # the easy case (on Python 3.3+)
    if hasattr(func, "__qualname__"):
        return func.__qualname__

    # class methods, bound and unbound methods
    f_self = getattr(func, "__self__", None) or getattr(func, "im_self", None)
    if f_self and hasattr(func, "__name__"):
        f_class = f_self if isinstance(f_self, type) else f_self.__class__
    else:
        f_class = getattr(func, "im_class", None)

    if f_class and hasattr(func, "__name__"):
        return "%s.%s" % (f_class.__name__, func.__name__)

    # class or class instance
    if hasattr(func, "__call__"):
        # class
        if hasattr(func, "__name__"):
            return func.__name__

        # instance of a class with a __call__ method
        return func.__class__.__name__

    raise TypeError(
        "Unable to determine a name for %r -- maybe it is not a callable?" % func
    )


def obj_to_ref(obj):
    """
    Returns the path to the given object.

    :param `object` obj: The object to obtain the reference for.
    :raises `ValueError`: If the reference cannot be determined for the object.
    :return `str`: The reference string of the object.
    :rtype: `str`
    """

    try:
        ref = "%s:%s" % (obj.__module__, get_callable_name(obj))
        print(ref)
        obj2 = ref_to_obj(ref)
        print(obj)
        print(obj2)
        if obj != obj2:
            raise ValueError
    except Exception:
        raise ValueError("Cannot determine the reference to %r" % obj)

    return ref


def ref_to_obj(ref):
    """
    Returns the object pointed to by `ref`.

    :param `str` ref: The reference string pointing to the object.
    :raises `TypeError`: If the reference is not a string.
    :raises `ValueError`: If the reference string is invalid.
    :raises `LookupError`: If the module cannot be imported or the object cannot be found.
    :return: The object corresponding to the reference.
    :rtype: `object`
    """

    if not isinstance(ref, six.string_types):
        raise TypeError("References must be strings")
    if ":" not in ref:
        raise ValueError("Invalid reference")

    modulename, rest = ref.split(":", 1)
    try:
        obj = __import__(modulename)
    except ImportError:
        raise LookupError("Error resolving reference %s: could not import module" % ref)

    try:
        for name in modulename.split(".")[1:] + rest.split("."):
            obj = getattr(obj, name)
        return obj
    except Exception:
        raise LookupError("Error resolving reference %s: error looking up object" % ref)


STR_TO_OP_MAPPING = {}
for op in (operator.eq, operator.lt, operator.le, operator.gt, operator.ge):
    STR_TO_OP_MAPPING[op.__str__()] = op


def str_to_operator(ref):
    valid_type(ref, six.string_types)

    obj = STR_TO_OP_MAPPING.get(ref, None)
    if obj is None:
        raise ValueError("ref ({}) is invalid".format(ref))

    return obj
