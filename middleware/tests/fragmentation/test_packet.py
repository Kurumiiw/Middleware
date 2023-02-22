import pytest
import random
from middleware.fragmentation.packet import Packet


SAMPLE_DATA = bytearray([145, 234, 255, 245])


def test_packet_creation():
    """
    Tests combinations of packet creation options.
    """
    p = Packet(SAMPLE_DATA, source=("a", 1))

    assert p.get_data() == SAMPLE_DATA
    assert p.get_header() == bytearray([0, 0, 0])
    assert p.source == ("a", 1)


def test_create_empty_packet_exception():
    """
    Tests that creating empty packet raises an exception.
    """
    with pytest.raises(ValueError) as e:
        Packet(bytearray(0), source=("a", 1))
