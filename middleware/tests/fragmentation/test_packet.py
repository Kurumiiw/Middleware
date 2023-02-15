import pytest
import random
from middleware.fragmentation.packet import (
    Packet,
    MissingFragmentException,
    EffectiveMTUTooLowException,
)

SAMPLE_DATA = [145, 234, 255, 245]


def test_packet_creation():
    """
    Tests combinations of packet creation options.
    """
    p = Packet(bytearray([1, 2, 3, 4]))

    assert p.data == bytearray([0, 0, 1, 2, 3, 4])

    p = Packet(bytearray([1, 2, 3, 4]), create_header=False)

    assert p.data == bytearray([1, 2, 3, 4])

    p = Packet(bytearray([1, 2, 3, 4]), seq=5, final=7)

    assert p.data == bytearray([5, 7, 1, 2, 3, 4])


def test_create_empty_packet_exception():
    """
    Tests that creating empty packet raises an exception.
    """
    with pytest.raises(ValueError) as e:
        Packet(bytearray(0))


def test_fragmentation():
    """
    Tests whether fragmentation and reassembly of ordered fragments works.
    """
    p = Packet(bytearray(SAMPLE_DATA))

    assert p.data == bytearray([0, 0]) + bytearray(SAMPLE_DATA)

    # MTU chosen to be 63, so the adjusted mtu = 1, i.e 1 byte of data per packet.
    fragments = tuple(Packet.fragment(p, mtu=63))

    assert len(fragments) == 6

    p2 = Packet.reassemble(fragments)

    assert p.data == p2.data


def test_unordered_packet_reassembly():
    """
    Tests whether assembling an out-of-order list of fragments works.
    """
    p = Packet(bytearray(SAMPLE_DATA))

    # Fragment packet to fragments with one byte of data each.
    fragments = list(Packet.fragment(p, mtu=63))

    random.shuffle(fragments)

    p2 = Packet.reassemble(fragments)

    assert p.data == p2.data


def test_missing_fragment_exception():
    """
    Tests whether reassembling packets with missing packets results in an Exception being raised.
    """
    # Test with a packet in the middle missing.
    p = Packet(bytearray(SAMPLE_DATA))

    fragments = list(Packet.fragment(p, mtu=63))

    fragments.remove(fragments[3])

    with pytest.raises(MissingFragmentException):
        Packet.reassemble(fragments)

    # Test with an end packet missing.
    p2 = Packet(bytearray(SAMPLE_DATA))

    fragments = list(Packet.fragment(p2, mtu=63))[:2]

    with pytest.raises(MissingFragmentException):
        Packet.reassemble(fragments)


def test_small_adjusted_mtu_exception():
    """
    Test that setting MTU too low, (i.e. fragmentation is impossible due to overhead), results in an exception being raised.
    """
    p = Packet(bytearray(SAMPLE_DATA))

    with pytest.raises(EffectiveMTUTooLowException):
        fragments = list(Packet.fragment(p, mtu=0))
