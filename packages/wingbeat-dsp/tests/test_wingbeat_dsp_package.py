from importlib import metadata, resources

import wingbeat_dsp


def test_version_matches_installed_metadata() -> None:
    assert wingbeat_dsp.__version__ == metadata.version("wingbeat-dsp")


def test_package_declares_inline_types() -> None:
    assert resources.files("wingbeat_dsp").joinpath("py.typed").is_file()
