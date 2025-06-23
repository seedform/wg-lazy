"""Development helpers."""

import logging
import re
from datetime import datetime
from functools import wraps


def raise_as(
    exception_cls: type[Exception],
    catch: tuple[type[Exception], ...] | type[Exception] = (Exception,),
    msg: str | None = None,
):
    """Decorator factory to convert exception type.

    Wraps a function with a try-except block where caught exceptions
    are cast to a string and passed as an argument to the target
    exception to be raised. Set the msg parameter to raise with a
    preconfigured message instead of the caught exception.

    Args:
        exception_cls: Exception class to be raised instead.
        catch: Exception classes to catch.
        msg: Message to pass to the exception class.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except catch as ce:
                raise exception_cls(msg if msg else str(ce))

        return wrapped

    return decorator


def warn_experimental(feature_name: str):
    """Decorator factory to warn about using an experimental feature.

    Args:
        feature_name: Feature name to show in the warning message.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            log = logging.getLogger(wrapped.__qualname__)
            log.warning("using experimental feature: %s", feature_name)
            return f(*args, **kwargs)

        return wrapped

    return decorator


def mask(sensitive_text: str, show: int = 4) -> str:
    """Mask a part of a string.

    Args:
        sensitive_text: text to mask
        show: number of characters show at the beginning

    Returns:
        String where hidden characters are replaced with an asterisk.
    """
    show = show if len(sensitive_text) > show else 0
    shown = sensitive_text[:show]
    hidden = len(sensitive_text[show:]) * "*"
    return shown + hidden


def seconds_to_date_time(seconds: int) -> str:
    """Convert seconds since Epoch to YYYY-mm-dd at HH:MM:SS.

    Args:
        seconds: Seconds since Epoch (UTC).

    Returns:
        Date and time in the machine's local timezone.
    """
    ts = datetime.fromtimestamp(seconds)
    return ts.strftime("%Y-%m-%d at %H:%M:%S")


def to_pascal_case(snake: str) -> str:
    """Convert a snake_case string to PascalCase.

    Leading underscores are kept to indicate so that internal-use
    field names are not exposed (e.g. by Pydantic serialization).

    Args:
        snake: snake_case field name.

    Returns:
        Field name converted to PascalCase.
    """
    snake = re.sub("_+", "_", snake).strip()
    words = [word.capitalize() for word in snake.split("_")]
    words[0] = "_" if words[0] == "" else words[0]
    return "".join(words)


def to_camel_case(snake: str) -> str:
    """Convert a snake_case string to camelCase.

    Leading underscores are not modified. Repeating underscores are
    treated as one. No input validation is done.

    Args:
        snake: snake_case field name.

    Returns:
        Field name converted to camelCase.
    """
    parts = re.split("_+", snake.strip())
    if parts[0] == "":  # leading underscore
        parts[1] = parts[0] + parts[1]
        parts = parts[1:]
    words = [word.capitalize() for word in parts[1:]]
    words[0] = "_" if words[0] == "" else words[0]
    return "".join(words)
