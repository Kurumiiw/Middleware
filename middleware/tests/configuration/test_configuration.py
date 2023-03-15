import pytest
from middleware.configuration.config import Config

test_config = Config()

def test_illegal_use_before_set():
    with pytest.raises(AssertionError):
        print(test_config.mtu)


def test_load_from_file():
    test_config.load_from_file("tests/configuration/test_config.ini")
    assert test_config.mtu == 512
    assert test_config.fragment_timeout == 60000
    assert test_config.expected_congestion == 128
    assert test_config.expected_bandwidth == 256
    assert test_config.expected_packet_loss == 512
    assert test_config.expected_jitter == 1024
    assert test_config.tcp_frto == 2
    assert test_config.tcp_reflect_tos == 0
    assert test_config.tcp_sack == 1


def test_set_get():
    test_config.expected_bandwidth = 0
    test_config.expected_packet_loss = 1
    test_config.expected_jitter = 2

    assert test_config.expected_bandwidth == 0
    assert test_config.expected_packet_loss == 1
    assert test_config.expected_jitter == 2


def test_save_to_file():
    test_config.save_to_file("tests/configuration/test_config_out.ini")

    expected_content = """[network_properties]
mtu = 512

[middleware_configuration]
fragment_timeout = 60000
expected_congestion = 128
expected_bandwidth = 0
expected_packet_loss = 1
expected_jitter = 2

[system_configuration]
tcp_frto = 2
tcp_reflect_tos = False
tcp_sack = True

"""

    with open("tests/configuration/test_config_out.ini", "r") as reader:
        assert reader.read(-1) == expected_content
