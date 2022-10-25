import functools
import logging
import time
from typing import Union, Type, Iterable


def retry(wait_ms: int = 0, limit: int = 0, logger: logging.Logger = None,
          ex_types: Union[Type[BaseException], Iterable[Type[BaseException]]] = Exception):
    """
    Author: Anton Kolobov
    Description: retry decorator with which one can rerun any function
    """
    ex_types_ = tuple(ex_types) if isinstance(ex_types, Iterable) else (ex_types,)

    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except ex_types_ as exc:
                    if 0 < limit <= attempt:
                        if logger:
                            logger.warning(f'{func.__name__}: NO MORE ATTEMPTS (LIMIT = {limit} HAS BEEN ACHIEVED)')
                        raise exc
                    if logger:
                        logger.error(f'{func.__name__}: FAILED EXECUTION ATTEMPT {attempt} '
                                     f'WITH EXCEPTION TYPE \'{type(exc)}\'')

                    attempt += 1
                    if logger:
                        logger.info(f'{func.__name__}: WAITING {wait_ms} ms BEFORE ATTEMPT {attempt}')
                    time.sleep(wait_ms / 1000)

        return wrapper

    return decorate
