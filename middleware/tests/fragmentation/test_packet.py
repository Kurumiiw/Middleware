import pytest
import random
from middleware.fragmentation.packet import Packet


def test_packet_creation():
    p = Packet(bytearray([1, 2, 3, 4]))

    assert p.data == bytearray([0, 0, 1, 2, 3, 4])

    p = Packet(bytearray([1, 2, 3, 4]), create_header=False)

    assert p.data == bytearray([1, 2, 3, 4])

    p = Packet(bytearray([1, 2, 3, 4]), seq=5, final=7)

    assert p.data == bytearray([5, 7, 1, 2, 3, 4])


def test_create_empty_packet_exception():
    with pytest.raises(ValueError) as e:
        Packet(bytearray(0))


def test_fragmentation():
    SAMPLE_DATA = [145, 234, 255, 245]

    p = Packet(bytearray(SAMPLE_DATA))

    assert p.data == bytearray([0, 0]) + bytearray(SAMPLE_DATA)

    # MTU chosen to be 61, so the adjusted = 1, i.e 1 byte per packet.
    fragments = tuple(Packet.fragment(p, mtu=63))

    assert len(fragments) == 6

    p2 = Packet.reassemble(fragments)

    assert p.data == p2.data


def test_unordered_packet_reassembly():
    SAMPLE_DATA = [145, 234, 255, 245]

    p = Packet(bytearray(SAMPLE_DATA))

    # Fragment packet to fragments with one byte of data each.
    fragments = list(Packet.fragment(p, mtu=63))
    random.shuffle(fragments)

    p2 = Packet.reassemble(fragments)

    assert p.data == p2.data
