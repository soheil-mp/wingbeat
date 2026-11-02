from importlib import metadata, resources

import wingbeat_common


def test_version_matches_installed_metadata() -> None:
    assert wingbeat_common.__version__ == metadata.version("wingbeat-common")


def test_package_declares_inline_types() -> None:
    assert resources.files("wingbeat_common").joinpath("py.typed").is_file()
