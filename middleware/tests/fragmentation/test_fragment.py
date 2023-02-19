import pytest
import random
from middleware.fragmentation.packet import Packet
from middleware.fragmentation.fragment import (
    Fragment,
    MissingFragmentException,
    EffectiveMTUTooLowException,
    PacketTooLarge,
)

random.seed(42069)
SAMPLE_DATA = bytearray([145, 234, 255, 245])


def test_creation():
    f = Fragment(SAMPLE_DATA, is_final=False, packet_id=10, seq=5)

    assert f.get_data() == SAMPLE_DATA
    assert f.get_packet_id() == 10
    assert f.get_fragment_number() == 5
    assert f.is_final_fragment() == False

    f = Fragment(SAMPLE_DATA, is_final=True, packet_id=35000, seq=38948)
    assert f.get_data() == SAMPLE_DATA
    assert f.get_packet_id() == 35000
    assert f.get_fragment_number() == 38948
    assert f.is_final_fragment() == True


def test_constructor_validation():
    with pytest.raises(ValueError):
        Fragment(bytearray(), packet_id=10, seq=5)

    with pytest.raises(ValueError):
        Fragment(SAMPLE_DATA, packet_id=0, seq=0)


def test_fragmentation():
    p = Packet(SAMPLE_DATA)

    fragments = list(Fragment.fragment(p, mtu=67))

    assert len(fragments) == 4
