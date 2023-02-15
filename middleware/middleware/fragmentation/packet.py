from __future__ import annotations
from typing import Iterator, List
import sys

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


class Packet:
    """
    Represents a base instance of a packet.
    """

    # Static variable for keeping track of global package id counter.
    # TODO: Should probably keep a separate counter per service to reduce chance
    # of collision, or do it in a better way.
    packet_id_counter: int = 0

    # Current header format:
    # Byte 1-4: Packet ID. Used for distinguishing
    # Byte 5-6: Fragment ID.
    # Byte 7-8: Max fragment ID. If 0, packet is not fragmented.
    def __init__(
        self,
        data: bytearray,
        /,
        packet_counter: int = None,
        create_header: bool = True,
        seq: int = 0,
        final: int = 0,
    ):
        if len(data) == 0:
            raise ValueError(
                "Unexpected data length. Data must be greater than 0 in length."
            )

        self.data = bytearray()
        if create_header:
            if packet_counter is None:
                packet_counter = Packet.get_next_packet_id()

            self.data.extend(packet_counter.to_bytes(4, byteorder=sys.byteorder))
            self.data.extend(seq.to_bytes(2, byteorder=sys.byteorder))
            self.data.extend(final.to_bytes(2, byteorder=sys.byteorder))

        self.data.extend(data)

    def get_size(self) -> int:
        """
        Returns the complete size of the packet, including headers and data in bytes.
        """
        return len(self.data)

    def get_header_size(self) -> int:
        """
        Returns the size of the header portion of this packet in bytes.
        """
        return len(self.get_header())  # Currently hardcoded to be 2.

    def get_data_size(self) -> int:
        """
        Returns the size of the header portion of this packet in bytes.
        """
        return self.get_size() - self.get_header_size()

    def get_header(self) -> bytearray:
        """
        Returns the header portion of the packet.
        """
        return self.data[0:8]

    def get_packet_id(self) -> int:
        """
        Returns the packet identifier portion of the header.
        """
        return int.from_bytes(
            self.get_header()[0:4], byteorder=sys.byteorder, signed=False
        )

    def get_fragment_number(self) -> int:
        """
        Returns the fragment id portion of the header.
        """
        return int.from_bytes(
            self.get_header()[4:6], byteorder=sys.byteorder, signed=False
        )

    def get_last_fragment_number(self) -> int:
        """
        Returns the final fragment id in this sequence.
        """
        return int.from_bytes(
            self.get_header()[6:8], byteorder=sys.byteorder, signed=False
        )

    def get_data(self) -> bytearray:
        """
        Returns the data portion of the packet.
        """
        return self.data[8:]

    @staticmethod
    def fragment(packet: Packet, /, mtu: int = 500) -> Iterator[Packet]:
        """
        Fragments the packet appropriately for the chosen MTU.
        """
        # TODO: Finding a better way to determine TCP header size would avoid some overhead.
        # Perhaps we can assume that our Middleware makes no packets with additional TCP header options?
        effective_mtu = mtu - MAX_TCP_HEADER_BYTES - packet.get_header_size()

        if effective_mtu <= 0:
            raise EffectiveMTUTooLowException(
                "Adjusting mtu for TCP and header overhead resulted in a negative MTU. Please choose a larger MTU."
            )

        # No need to fragment if size is already < effective_mtu
        if packet.get_size() <= effective_mtu:
            return iter(packet)

        offset = 0
        counter = 0
        final = int(packet.get_size() / effective_mtu)

        while offset < packet.get_size():
            yield Packet(
                packet.data[offset : (offset + effective_mtu)],
                create_header=True,
                packet_counter=packet.get_packet_id(),
                seq=counter,
                final=final,
            )
            offset = offset + effective_mtu
            counter = counter + 1

        return

    @staticmethod
    def reorder(fragments: List[Packet]) -> List[Packet]:
        """
        Reorders a list of packets according to their sequence numbers.
        """
        return sorted(list(fragments), key=lambda p: p.get_fragment_number())

    @staticmethod
    def reassemble(fragments: Iterator[Packet]) -> Packet:
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

        for x in Packet.reorder(list(fragments)):
            result.extend(x.get_data())

        return Packet(result, create_header=False)

    @staticmethod
    def get_next_packet_id() -> int:
        """
        Increments the global packet id counter and returns the new value.
        """
        Packet.packet_id_counter = Packet.packet_id_counter + 1
        if Packet.packet_id_counter > 4294967295:  # 4 byte unsigned int max.
            Packet.packet_id_counter = 0
        return Packet.packet_id_counter
