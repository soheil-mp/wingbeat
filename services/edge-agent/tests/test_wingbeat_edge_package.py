from importlib import metadata, resources

import wingbeat_edge


def test_version_matches_installed_metadata() -> None:
    assert wingbeat_edge.__version__ == metadata.version("wingbeat-edge-agent")


def test_package_declares_inline_types() -> None:
    assert resources.files("wingbeat_edge").joinpath("py.typed").is_file()
