from __future__ import annotations
from typing import Union


class Packet:
    """
    Represents a base instance of a packet.
    """

    # Current header format:
    # Byte 1-4: Packet ID. Used for distinguishing
    # Byte 5-6: Fragment ID.
    # Byte 7-8: Max fragment ID. If 0, packet is not fragmented.
    def __init__(self, data: bytearray, no_header: bool = False):
        if len(data) == 0:
            raise ValueError(
                "Unexpected data length. Data must be greater than 0 in length."
            )

        self.data = bytearray()
        if not no_header:
            self.data.extend(bytearray([0, 0, 0, 0]))

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
        return len(self.get_header())

    def get_data_size(self) -> int:
        """
        Returns the size of the header portion of this packet in bytes.
        """
        return self.get_size() - self.get_header_size()

    def get_header(self) -> bytearray:
        """
        Returns the header portion of the packet.
        """
        return self.data[0:4]

    def get_packet_id(self) -> int:
        """
        Returns the packet identifier portion of the header.
        """
        return int.from_bytes(self.get_header()[0:4], byteorder="little", signed=False)

    def get_data(self) -> bytearray:
        """
        Returns the data portion of the packet.
        """
        return self.data[4:]

    def is_fragment(self) -> bool:
        """
        Checks whether a package is a fragment.
        """
        return not self.get_packet_id() == 0
