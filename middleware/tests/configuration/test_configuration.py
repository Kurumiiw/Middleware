import pytest
from middleware.configuration.config import Config

test_config = Config()


def test_illegal_use_before_set():
    with pytest.raises(AssertionError):
        print(test_config.mtu)


def test_load_from_file():
    test_config.load_from_file("tests/configuration/test_config.ini")
    assert test_config.mtu == 512
    assert test_config.fragment_timeout == 5
    assert test_config.congestion_algorithm == "vegas"


def test_set_get():
    test_config.fragment_timeout = 10
    test_config.mtu = 200
    test_config.congestion_algorithm = "reno"

    assert test_config.fragment_timeout == 10
    assert test_config.mtu == 200
    assert test_config.congestion_algorithm == "reno"


def test_save_to_file():
    test_config.save_to_file("tests/configuration/test_config_out.ini")

    expected_content = """[middleware_configuration]
mtu = 200
fragment_timeout = 10
congestion_algorithm = reno
echo_config_path = True

"""

    with open("tests/configuration/test_config_out.ini", "r") as reader:
        assert reader.read(-1) == expected_content
