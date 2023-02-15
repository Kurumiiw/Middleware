from __future__ import annotations
from typing import Iterator, List

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

    data: bytearray = None

    # Preliminary header format:
    # Byte 1: Sequence number.
    # Byte 2: Last sequence number required for this packet to be complete.
    def __init__(
        self,
        data: bytearray,
        /,
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
            self.data.extend([seq, final])
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
        return 2  # Currently hardcoded to be 2.

    def get_data_size(self) -> int:
        """
        Returns the size of the header portion of this packet in bytes.
        """
        return self.get_size() - self.get_header_size()

    def get_header(self) -> bytearray:
        """
        Returns the header portion of the packet.
        """
        return self.data[0:2]

    def get_data(self) -> bytearray:
        """
        Returns the data portion of the packet.
        """
        return self.data[2:]

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

        offset = 0
        counter = 0
        final = int(packet.get_size() / effective_mtu)

        while offset < packet.get_size():
            yield Packet(
                packet.data[offset : (offset + effective_mtu)],
                create_header=True,
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
        return sorted(list(fragments), key=lambda p: p.data[0])

    @staticmethod
    def reassemble(fragments: Iterator[Packet]) -> Packet:
        """
        Reassembles a collection of fragments into the original packet. Fragments should
        contain only fragments from the original packet, but can be unordered.
        """
        # Check for missing packets.
        if len(fragments) != fragments[0].get_header()[1]:
            raise MissingFragmentException(
                "A packet was missing during attempt at reassembly."
            )

        result = bytearray()

        for x in Packet.reorder(list(fragments)):
            result.extend(x.get_data())

        return Packet(result, create_header=False)
