from __future__ import annotations
from middleware.fragmentation.packet import Packet
from typing import Iterator, List, Union


MAX_TCP_HEADER_BYTES = 60


class MissingFragmentException(ValueError):
    """
    Raised when a fragment is missing during attempted reassembly.
    """

    pass


class EffectiveMTUTooLowException(ValueError):
    """
    Raised when adjusting provided MTU for TCP/header overhead results in a value lower than or equal to 0.
    """

    pass


class PacketTooLarge(ValueError):
    """
    Raised when a packet being fragmented is too large to be fragmented.
    """

    pass


class Fragment(Packet):
    # Static variable for keeping track of global package id counter.
    # TODO: Should probably keep a separate counter per service to reduce chance
    # of collision, or do it in a better way.
    packet_id_counter: int = 0

    def __init__(self, data: bytearray, /, packet_id: int, seq: int, final: int):
        if packet_id == 0:
            raise ValueError("Packet ID of 0 is reserved for unfragmented packets.")
        if len(data) == 0:
            raise ValueError(
                "Unexpected data length. Data must be greater than 0 in length."
            )

        if seq > final:
            raise ValueError("Fragment ID is greater than final fragment ID.")

        self.data = bytearray()
        self.data.extend(packet_id.to_bytes(4, byteorder="little"))
        self.data.extend(seq.to_bytes(2, byteorder="little"))
        self.data.extend(final.to_bytes(2, byteorder="little"))

        self.data.extend(data)

    def get_header(self):
        return self.data[0:8]

    def get_data(self):
        return self.data[8:]

    def get_fragment_number(self) -> int:
        """
        Returns the fragment id portion of the header.
        """
        return int.from_bytes(self.get_header()[4:6], byteorder="little", signed=False)

    def get_last_fragment_number(self) -> int:
        """
        Returns the final fragment id in this sequence.
        """
        return int.from_bytes(self.get_header()[6:8], byteorder="little", signed=False)

    @staticmethod
    def fragment(
        packet: Packet, /, mtu: int = 500
    ) -> Iterator[Union[Fragment, Packet]]:
        """
        Fragments the packet appropriately for the chosen MTU.
        """
        # TODO: Finding a better way to determine TCP header size would avoid some overhead.
        # Perhaps we can assume that our Middleware makes no packets with additional TCP header options?
        effective_mtu = mtu - MAX_TCP_HEADER_BYTES - 8

        if effective_mtu <= 0:
            raise EffectiveMTUTooLowException(
                "Adjusting mtu for TCP and header overhead resulted in a negative MTU. Please choose a larger MTU."
            )

        # No need to fragment if size is already < effective_mtu
        if packet.get_size() <= effective_mtu:
            return iter(packet)

        offset = 0
        counter = 0
        final = int(packet.get_data_size() / effective_mtu)

        if final > 65535:  # 2byte unsigned integer max.
            raise PacketTooLarge("Packet is too large to be fragmented properly.")

        pid = Fragment.get_next_packet_id()
        while offset < packet.get_data_size():
            yield Fragment(
                packet.get_data()[offset : (offset + effective_mtu)],
                packet_id=pid,
                seq=counter,
                final=final,
            )

            offset = offset + effective_mtu
            counter = counter + 1

        return

    @staticmethod
    def reorder(fragments: List[Fragment]) -> List[Fragment]:
        """
        Reorders a list of fragments according to their sequence numbers.
        """
        return sorted(list(fragments), key=lambda p: p.get_fragment_number())

    @staticmethod
    def reassemble(fragments: Iterator[Fragment]) -> Packet:
        """
        Reassembles a collection of fragments into the original packet. Fragments should
        contain only fragments from the original packet, but can be unordered.
        """
        # Check for missing packets.
        if len(fragments) != fragments[0].get_last_fragment_number():
            raise MissingFragmentException(
                "A packet was missing during attempt at reassembly."
            )

        result = bytearray()

        for x in Fragment.reorder(list(fragments)):
            result.extend(x.get_data())

        return Packet(result)

    @staticmethod
    def get_next_packet_id() -> int:
        """
        Increments the global packet id counter and returns the new value.
        """
        Fragment.packet_id_counter = Fragment.packet_id_counter + 1
        if Fragment.packet_id_counter > 4294967295:  # 4 byte unsigned int max.
            Fragment.packet_id_counter = 1
        return Fragment.packet_id_counter
