"""Version is exposed and looks like a sane semver string."""
import re

from app import __version__
from app.version import __version__ as v2


def test_version_is_string():
    assert isinstance(__version__, str)
    assert isinstance(v2, str)
    assert __version__ == v2  # re-exported from package init


def test_version_semver_shape():
    # 1.2.3 (optionally with -rc / +meta suffix)
    assert re.match(r"^\d+\.\d+\.\d+([\-+][\w.]+)?$", __version__)
