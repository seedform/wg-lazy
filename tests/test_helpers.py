"""Test helper functions."""

import logging

from freezegun import freeze_time
from pytest import mark, raises

from wg_lazy.utils import (
    mask,
    raise_as,
    seconds_to_date_time,
    to_pascal_case,
    warn_experimental,
)


@mark.parametrize(
    ("msg", "match"),
    [
        # show custom message
        ("preconfigured", "preconfigured"),
        # show original exception message
        (None, "exception argument"),
    ],
)
def test_raise_as(msg, match):
    """Test @raise_as decorator."""

    class RaisedError(Exception):
        pass

    class CaughtError(Exception):
        pass

    @raise_as(RaisedError, catch=CaughtError, msg=msg)
    def decorated():
        raise CaughtError("exception argument")

    with raises(RaisedError, match=match):
        decorated()


def test_warn_experimental(caplog):
    """Test @warm_experimental decorator."""

    @warn_experimental("unit test")
    def decorated():
        pass

    with caplog.at_level(logging.WARNING):
        decorated()
        assert "unit test" in caplog.text


def test_mask():
    """Test string mask function."""
    assert mask("SHOWNHIDDEN", show=5) == "SHOWN******"


@freeze_time("2077-12-31 00:00:00", tz_offset=-5)  # EST
def test_seconds_to_date_time():
    """Test converting seconds to a friendly date-time format."""
    date_time = seconds_to_date_time(498718800)
    assert date_time == "1985-10-21 at 00:00:00"


@mark.parametrize(
    ("snake", "expected"),
    [
        ("_keep_leading_underscore", "_KeepLeadingUnderscore"),
        ("drop_trailing_underscore_", "DropTrailingUnderscore"),
        ("ignore__repeating__underscores", "IgnoreRepeatingUnderscores"),
    ],
)
def test_to_pascal_case(snake, expected):
    """Test conversion from snake case to pascal case."""
    assert to_pascal_case(snake) == expected
