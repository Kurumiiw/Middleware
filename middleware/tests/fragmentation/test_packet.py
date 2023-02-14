import pytest
from middleware.fragmentation.packet import Packet


def test_create_empty_packet_exception():
    with pytest.raises(ValueError) as e:
        Packet(bytearray(0))


def test_fragmentation():
    SAMPLE_DATA = [145, 234, 255, 245]

    p = Packet(bytearray(SAMPLE_DATA))

    assert p.data == bytearray(SAMPLE_DATA)

    # MTU chosen to be 61, so the adjusted = 1, i.e 1 byte per packet.
    fragments = tuple(Packet.fragment(p, mtu=61))

    assert len(fragments) == 4

    p2 = Packet.reassemble(fragments)

    assert p2.data == bytearray(SAMPLE_DATA)
