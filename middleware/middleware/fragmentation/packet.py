from __future__ import annotations
from typing import Iterator, List


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
            self.data.append(seq)
            self.data.append(final)
        self.data = self.data + data

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
        return self.data[0:1]

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
        # Correct for max TCP header size.
        # TODO: Make this smarter?
        adjusted_mtu = mtu - 60 - packet.get_header_size()
        offset = 0
        counter = 0
        final = int(packet.get_size() / adjusted_mtu) + 1

        # TODO: Implement adding header for reordering and reassembling.
        while offset < packet.get_size():
            yield Packet(
                packet.data[offset : (offset + adjusted_mtu)],
                create_header=True,
                seq=counter,
                final=final,
            )
            offset = offset + adjusted_mtu
            counter = counter + 1

        return

    @staticmethod
    def reorder(fragments: List[Packet]) -> List[Packet]:
        # TODO: Sort fragments by sequence number.
        return sorted(list(fragments), key=lambda packet: packet.data[0])

    @staticmethod
    def reassemble(fragments: Iterator[Packet]) -> Packet:
        """
        Reassembles a collection of fragments into the original packet.
        """
        # TODO: Currently this does not reorder fragments. Not sure if that should
        # be done here or somewhere else?

        # TODO: Take header into account when reassembling.
        result = bytearray()
        for x in Packet.reorder(list(fragments)):
            result = result + x.get_data()

        return Packet(result, create_header=False)
