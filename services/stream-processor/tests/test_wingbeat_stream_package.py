from importlib import metadata, resources

import wingbeat_stream


def test_version_matches_installed_metadata() -> None:
    assert wingbeat_stream.__version__ == metadata.version("wingbeat-stream-processor")


def test_package_declares_inline_types() -> None:
    assert resources.files("wingbeat_stream").joinpath("py.typed").is_file()
