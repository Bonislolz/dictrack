# -*- coding: utf-8 -*-

from logging import DEBUG, Formatter, StreamHandler, getLogger

LOGGER_FORMAT = "%(name)s[%(process)d] %(asctime)s - %(levelname)s - [%(filename)s] %(funcName)s in %(lineno)d, %(message)s"

logger = getLogger("dictrack")

try:
    from chromalog import ColorizingFormatter, ColorizingStreamHandler

    handler = ColorizingStreamHandler()
    handler.setFormatter(ColorizingFormatter(LOGGER_FORMAT))
except ImportError:
    handler = StreamHandler()
    handler.setFormatter(Formatter(LOGGER_FORMAT))

logger.addHandler(handler)
logger.setLevel(DEBUG)
logger.disabled = True
