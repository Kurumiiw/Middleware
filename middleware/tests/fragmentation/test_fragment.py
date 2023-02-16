import pytest
import random
from middleware.fragmentation.packet import Packet
from middleware.fragmentation.fragment import (
    Fragment,
    MissingFragmentException,
    EffectiveMTUTooLowException,
    PacketTooLarge,
)

SAMPLE_DATA = bytearray([145, 234, 255, 245])


def test_creation():
    f = Fragment(SAMPLE_DATA, packet_id=10, seq=5, final=7)

    assert f.get_data() == SAMPLE_DATA
    assert f.get_packet_id() == 10
    assert f.get_fragment_number() == 5
    assert f.get_last_fragment_number() == 7


def test_constructor_validation():
    with pytest.raises(ValueError):
        Fragment(bytearray(), 10, 5, 7)

    with pytest.raises(ValueError):
        Fragment(SAMPLE_DATA, 10, 7, 6)

    with pytest.raises(ValueError):
        Fragment(SAMPLE_DATA, 0, 0, 0)


def test_ordered_fragmentation():
    p = Packet(SAMPLE_DATA)

    fragments = tuple(Fragment.fragment(p, mtu=69))

    assert len(fragments) == 4

    p2 = Fragment.reassemble(fragments)

    assert p.get_data() == p2.get_data()


def test_unordered_fragmentation():
    p = Packet(SAMPLE_DATA)

    fragments = list(Fragment.fragment(p, mtu=69))

    random.shuffle(fragments)

    p2 = Fragment.reassemble(fragments)

    assert p.get_data() == p2.get_data()


def test_missing_fragment():
    p = Packet(SAMPLE_DATA)

    fragments = list(Fragment.fragment(p, mtu=69))
    fragments.remove(fragments[3])

    with pytest.raises(MissingFragmentException):
        Fragment.reassemble(fragments)


def test_low_mtu_exception():
    p = Packet(SAMPLE_DATA)

    with pytest.raises(EffectiveMTUTooLowException):
        list(Fragment.fragment(p, mtu=0))


def test_packet_too_big_exception():
    data = bytearray(65536)

    p = Packet(data)

    with pytest.raises(PacketTooLarge):
        list(Fragment.fragment(p, mtu=69))
