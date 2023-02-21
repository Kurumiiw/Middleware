from __future__ import annotations
from middleware.fragmentation.packet import Packet
from typing import Iterator, List, Optional, Union
import math

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
    identification_counter: int = 0

    def __init__(
        self,
        data: bytearray,
        /,
        no_header: bool = False,
        is_final: bool = False,
        identification: int = 0,
        seq: int = 0,
    ):
        if len(data) == 0:
            raise ValueError(
                "Unexpected data length. Data must be greater than 0 in length."
            )

        raw = bytearray()
        if not no_header:
            if identification == 0:
                raise ValueError("Packet ID of 0 is reserved for unfragmented packets.")

            raw.extend(identification.to_bytes(3, byteorder="big"))
            tmp = seq | (is_final << 23)
            raw.extend(tmp.to_bytes(3, byteorder="big"))

        raw.extend(data)

        super().__init__(raw, no_header=True)

    def get_header(self):
        return self.data[0:6]

    def get_data(self):
        return self.data[6:]

    def is_final_fragment(self) -> bool:
        if (self.get_header()[3] >> 7) & 1:
            return True

        return False

    def get_fragment_number(self) -> int:
        """
        Returns the fragment id portion of the header.
        """
        # Ensure the final fragment flag is stripped before converting to integer.
        return (
            int.from_bytes(self.get_header()[3:6], byteorder="big", signed=False)
            & 0b011111111111111111111111
        )

    @staticmethod
    def fragment(
        packet: Packet, /, mtu: int = 500
    ) -> Iterator[Union[Fragment, Packet]]:
        """
        Fragments the packet appropriately for the chosen MTU.
        """
        # TODO: Finding a better way to determine TCP header size would avoid some overhead.
        # Perhaps we can assume that our Middleware makes no packets with additional TCP header options?
        effective_mtu = mtu - MAX_TCP_HEADER_BYTES - 6

        if effective_mtu <= 0:
            raise EffectiveMTUTooLowException(
                "Adjusting mtu for TCP and header overhead resulted in a negative MTU. Please choose a larger MTU."
            )

        # No need to fragment if size is already < effective_mtu
        if packet.get_size() <= effective_mtu:
            yield packet
            return

        offset = 0
        counter = 0
        final = math.ceil(packet.get_data_size() / effective_mtu) -1

        if final > 8388608:  # 23 bit unsigned integer max.
            raise PacketTooLarge("Packet is too large to be fragmented properly.")

        pid = Fragment.get_next_packet_id()
        while offset < packet.get_data_size():
            if counter == final:
                yield Fragment(
                    packet.get_data()[offset : (offset + effective_mtu)],
                    is_final=True,
                    identification=pid,
                    seq=counter,
                )
            else:
                yield Fragment(
                    packet.get_data()[offset : (offset + effective_mtu)],
                    identification=pid,
                    seq=counter,
                )

            offset = offset + effective_mtu
            counter = counter + 1

        return

    @staticmethod
    def get_next_packet_id() -> int:
        """
        Increments the global packet id counter and returns the new value.
        """
        Fragment.identification_counter = Fragment.identification_counter + 1
        if Fragment.identification_counter > 16777215:  # 3 byte unsigned int max.
            Fragment.identification_counter = 1
        return Fragment.identification_counter

    @staticmethod
    def create_from_raw_data(data: bytearray) -> Union[Fragment, Packet]:
        """
        Helper function which calls the right constructor for a
        """
        if int.from_bytes(data[0:3], byteorder="big", signed=False) == 0:
            return Packet(data, no_header=True)

        return Fragment(data, no_header=True)
