from importlib.resources import files

import vigicrues_client


def test_package_is_marked_as_typed() -> None:
    assert files(vigicrues_client).joinpath("py.typed").is_file()
