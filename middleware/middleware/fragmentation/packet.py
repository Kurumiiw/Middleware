from __future__ import annotations
from typing import Tuple


class Packet:
    """
    Represents a base instance of a packet.
    """

    # Header format:
    # Byte 1-3: If 0, indicates unfragmented packet with data at bytes 5+
    #           If non-zero, indicates part of fragmented package.

    # If fragment:
    # Byte 4-6: Fragment id in packet. First bit indicates if the fragment is the final
    # in the sequence

    # See also the diagram in #17 for a graphical representation:
    # https://github.com/Kurumiiw/Middleware/issues/17

    def __init__(
        self, data: bytearray, *, source: Tuple[str, int], no_header: bool = False
    ):
        if len(data) == 0:
            raise ValueError(
                "Unexpected data length. Data must be greater than 0 in length."
            )

        self.source = source
        self.data = bytearray()
        if not no_header:
            # We set the length either to the length of the data, or to the maximum length possible, if the packet is too big. If so the packet
            # should never be sent without fragmenting, but this allows services to send and receive data in bigger chunks than 
            # 2^16 bytes easily. This should work as long as the fragmenting code runs on every Packet, but will fail silently and
            # catastrophically if not (the receiver will not be able to deliniate between received packet).
            # TODO: Better solutions are welcome. Also see #22
            self.data.extend(bytearray([0, 0]) + min([len(data) + 4, 2**16-1]).to_bytes(2, byteorder="big", signed = False))

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

    def get_identification(self) -> int:
        """
        Returns the packet identifier portion of the header.
        """
        return int.from_bytes(self.get_header()[0:2], byteorder="big", signed=False)

    def get_length(self) -> int:
        """
        Returns the length field as stored in the header.
        """
        return int.from_bytes(self.get_header()[2:4], byteorder="big", signed = False)

    def get_data(self) -> bytearray:
        """
        Returns the data portion of the packet.
        """
        return self.data[4:]

    def is_fragment(self) -> bool:
        """
        Checks whether a package is a fragment.
        """
        return not self.get_identification() == 0
