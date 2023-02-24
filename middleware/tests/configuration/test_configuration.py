import pytest
from middleware.configuration.config import *

def test_illegal_use_before_set():
    with pytest.raises(AssertionError):
        print(config.mtu)

def test_load_from_file():
    config.load_from_file("tests/configuration/test_config.ini")
    assert config.mtu == 512
    assert config.fragment_timeout == 60000
    assert config.expected_congestion == 128
    assert config.expected_bandwidth == 256
    assert config.expected_packet_loss == 512
    assert config.expected_jitter == 1024
    assert config.tcp_frto == 2
    assert config.tcp_reflect_tos == 0
    assert config.tcp_sack == 1

def test_set_get():
    config.expected_bandwidth = 0
    config.expected_packet_loss = 1
    config.expected_jitter = 2

    assert config.expected_bandwidth == 0
    assert config.expected_packet_loss == 1
    assert config.expected_jitter == 2

def test_save_to_file():
    config.save_to_file("tests/configuration/test_config_out.ini")
    
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
