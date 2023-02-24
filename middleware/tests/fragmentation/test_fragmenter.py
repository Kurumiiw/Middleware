from typing import List, Union
from middleware.fragmentation.fragment import Fragment
import pytest
import random
from middleware.fragmentation.fragmenter import Fragmenter
from middleware.fragmentation.packet import Packet

random.seed(69420)

SAMPLE_DATA = bytearray(random.randbytes(7919))


def test_no_fragmentation():
    """
    Tests processing of a packet that doesn't require fragmentation
    """
    p = Packet(bytearray(random.randbytes(20)), source=("test", 1234))

    fragments = Fragmenter.fragment(p)
    received = Fragmenter.process_packets(fragments)

    assert len(received) == 1
    assert p.get_header() == received[0].get_header()
    assert p.get_data() == received[0].get_data()


def test_simple_reassembly():
    """
    Tests reassembly of a single packet, with fragments in order.
    """
    p = Packet(SAMPLE_DATA, source=("test", 1234))

    fragments = Fragmenter.fragment(p)
    received = Fragmenter.process_packets(fragments)

    assert len(received) == 1
    assert p.get_header() == received[0].get_header()
    assert p.get_data() == received[0].get_data()


def test_shuffled_reassembly():
    """
    Tests reassembly of a single packet, with fragments shuffled.
    """

    p = Packet(SAMPLE_DATA, source=("test", 1234))

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

    p = Packet(SAMPLE_DATA, source=("test", 1234))

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
        Packet(bytearray(random.randbytes(100)), source=("test", 1234)),
        Packet(bytearray(random.randbytes(200)), source=("test", 1234)),
    ]

    fragments = []
    for x in p:
        fragments.extend(Fragmenter.fragment(x))

    random.shuffle(fragments)

    received = Fragmenter.process_packets(fragments)

    assert len(received) == len(p)

    p = sorted(p, key=lambda p: p.get_identification())
    received = sorted(p, key=lambda p: p.get_identification())

    for a, b in zip(p, received):
        assert a.data == b.data


@pytest.mark.slow
def test_multiple_packets_2():
    """
    Tests the entire packet pipeline: packet->fragments->bytestream->fragments->
    packet, in a scenario that should be realistic to real world usage of the
    Middleware:
    - Multiple packtes of various sizes.
    - Fragments are shuffled to simulate unordered receival.
    """
    # Sender side
    ## Create packets from data.
    p: list[Packet] = []
    for i in range(1, 5000, 50):  # 100000
        p.append(
            Packet(
                bytearray(random.randbytes(i)),
                source=("test", 0),
            )
        )

    ## Fragment packets.
    fragments: list[Union[Fragment, Packet]] = []
    for x in p:
        fragments.extend(Fragmenter.fragment(x))

    ## Transfer reordering.
    random.shuffle(fragments)

    # Receiver
    ## Receive bytestream.
    bytestream = bytearray()
    for f in fragments:
        bytestream.extend(f.data)

    received: list[Packet] = []

    ## Defragment packets/fragments from bytestream.
    while len(bytestream) > 0:
        length = int.from_bytes(bytestream[2:4], byteorder="big", signed=False)

        dat = bytestream[:length]
        bytestream = bytestream[length:]

        received.append(Fragmenter.create_from_raw_data(dat, source=("test", 0)))

    ## Reassemble packets.
    rec_pack: list[Packet] = []
    for f in received:
        rec_pack.extend(Fragmenter.process_packet(f))

    rec_pack = sorted(rec_pack, key=lambda p: len(p.data))

    # Assert received packets == sent packets.
    assert len(rec_pack) == len(p)

    for a, b in zip(p, rec_pack):
        assert a.data == b.data
