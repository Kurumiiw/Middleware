from __future__ import annotations
from typing import Iterator


class Packet:
    """
    Represents a base instance of a packet.
    """

    data: bytearray = None

    def __init__(self, data: bytearray):
        if len(data) == 0:
            raise ValueError(
                "Unexpected data length. Data must be greater than 0 in length."
            )

        self.data = data

    def get_size(self) -> int:
        """
        Returns the complete size of the packet, including headers and data.
        """
        return len(self.data)

    def get_header(self) -> bytearray:
        """
        Returns the header portion of the packet.
        """
        pass

    def get_data(self) -> bytearray:
        """
        Returns the data portion of the packet.
        """
        pass

    @staticmethod
    def fragment(packet: Packet, /, mtu: int = 500) -> Iterator[Packet]:
        """
        Fragments the packet appropriately for the chosen MTU.
        """
        # Correct for max TCP header size.
        # TODO: Make this smarter?
        adjusted_mtu = mtu - 60
        offset = 0

        # TODO: Implement adding header for reordering and reassembling.
        while offset < packet.get_size():
            yield Packet(packet.data[offset : (offset + adjusted_mtu)])
            offset = offset + adjusted_mtu

    @staticmethod
    def reassemble(fragments: Iterator[Packet]) -> Packet:
        """
        Reassembles a collection of fragments into the original packet.
        """
        # TODO: Currently this does not reorder fragments. Not sure if that should
        # be done here or somewhere else?

        # TODO: Take header into account when reassembling.
        result = bytearray()
        for x in fragments:
            result = result + x.data

        return Packet(result)
