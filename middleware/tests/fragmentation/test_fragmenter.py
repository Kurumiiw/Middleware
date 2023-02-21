import pytest
import random
from middleware.fragmentation.fragmenter import Fragmenter
from middleware.fragmentation.fragment import Fragment
from middleware.fragmentation.packet import Packet

random.seed(69420)

SAMPLE_DATA = bytearray(random.randbytes(7919))


def test_no_fragmentation():
    """
    Tests processing of a packet that doesn't require fragmentation
    """
    p = Packet(bytearray(random.randbytes(20)))

    fragments = Fragmenter.fragment(p)
    received = Fragmenter.process_packets(fragments)

    assert len(received) == 1
    assert p.get_header() == received[0].get_header()
    assert p.get_data() == received[0].get_data()


def test_simple_reassembly():
    """
    Tests reassembly of a single packet, with fragments in order.
    """
    p = Packet(SAMPLE_DATA)

    fragments = Fragmenter.fragment(p)
    received = Fragmenter.process_packets(fragments)

    assert len(received) == 1
    assert p.get_header() == received[0].get_header()
    assert p.get_data() == received[0].get_data()


def test_shuffled_reassembly():
    """
    Tests reassembly of a single packet, with fragments shuffled.
    """

    p = Packet(SAMPLE_DATA)

    fragments = Fragmenter.fragment(p)
    random.shuffle(fragments)

    received = Fragmenter.process_packets(fragments)

    assert len(received) == 1
    assert p.get_header() == received[0].get_header()
    assert p.get_data() == received[0].get_data()


def test_interrupted_reassembly():
    """
    Tests reassembly of a single packet, where fragments are shuffled, and
    the fragments are processed in two calls to process_fragments().
    """

    p = Packet(SAMPLE_DATA)

    fragments = Fragmenter.fragment(p)
    random.shuffle(fragments)

    received = Fragmenter.process_packets(fragments[:10])

    assert len(received) == 0

    received.extend(Fragmenter.process_packets(fragments[10:]))

    assert len(received) == 1
    assert p.get_header() == received[0].get_header()
    assert p.get_data() == received[0].get_data()


def test_multiple_packets():
    """
    Tests that two fragmented packets are properly reassembled.
    """

    p = [
        Packet(bytearray(random.randbytes(100))),
        Packet(bytearray(random.randbytes(200))),
    ]

    fragments = []
    for x in p:
        fragments.extend(Fragmenter.fragment(x))

    random.shuffle(fragments)

    received = Fragmenter.process_packets(fragments)

    assert len(received) == len(p)

    p = sorted(p, key=lambda p: p.get_identification())
    received = sorted(p, key=lambda p: p.get_identification())

    for (a, b) in zip(p, received):
        assert a.data == b.data


@pytest.mark.slow
def test_multiple_packets_2():
    """
    Tests with many packets where some do not get fragmented. Fragments are processed in
    several batches. Should constitute a realistic scenario.
    """
    p: list[Packet] = []
    for i in range(1, 100000, 50):
        p.append(Packet(bytearray(random.randbytes(i))))

    fragments = []
    for x in p:
        fragments.extend(Fragmenter.fragment(x))

    received: list[Packet] = []

    offset = 0
    while offset < len(fragments):
        received.extend(Fragmenter.process_packets(fragments[offset : (offset + 20)]))
        offset = offset + 20

    received = sorted(received, key=lambda p: len(p.data))

    assert len(received) == len(p)

    for (a, b) in zip(p, received):
        assert a.data == b.data
