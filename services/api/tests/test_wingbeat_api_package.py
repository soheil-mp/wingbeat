from importlib import metadata, resources

import wingbeat_api


def test_version_matches_installed_metadata() -> None:
    assert wingbeat_api.__version__ == metadata.version("wingbeat-api")


def test_package_declares_inline_types() -> None:
    assert resources.files("wingbeat_api").joinpath("py.typed").is_file()
