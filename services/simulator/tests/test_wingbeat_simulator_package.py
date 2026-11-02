from importlib import metadata, resources

import wingbeat_simulator


def test_version_matches_installed_metadata() -> None:
    assert wingbeat_simulator.__version__ == metadata.version("wingbeat-simulator")


def test_package_declares_inline_types() -> None:
    assert resources.files("wingbeat_simulator").joinpath("py.typed").is_file()
