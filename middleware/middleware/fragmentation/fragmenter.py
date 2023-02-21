from __future__ import annotations
import time
from typing import Union
from middleware.fragmentation.fragmentsequence import FragmentSequence
from middleware.fragmentation.packet import Packet
from middleware.fragmentation.fragment import Fragment
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


class PacketTooLargeException(ValueError):
    """
    Raised when a packet being fragmented is too large to be fragmented.
    """

    pass


class Fragmenter:
    timeout_ms: int = 10000

    last_timeout_cleanup: int = 0

    identification_counter: int = 0

    # Used for keeping track of partially assembled packets.
    partial_packets: dict[int, FragmentSequence] = {}

    @staticmethod
    def fragment(packet: Packet, /, mtu=500) -> list[Union[Fragment, Packet]]:
        """
        Fragments the packet appropriately for the chosen MTU, returning a list of fragments or
        a list containing the original packet.
        """
        fragments: list[Union[Fragment, Packet]] = []

        # TODO: Finding a better way to determine TCP header size would avoid some overhead.
        # Perhaps we can assume that our Middleware makes no packets with additional TCP header options?
        effective_mtu = mtu - MAX_TCP_HEADER_BYTES - 6

        if effective_mtu <= 0:
            raise EffectiveMTUTooLowException(
                "Adjusting mtu for TCP and header overhead resulted in a negative MTU. Please choose a larger MTU."
            )

        # No need to fragment if size is already < effective_mtu
        if packet.get_size() <= effective_mtu:
            return [packet]

        offset = 0
        counter = 0
        final = math.ceil(packet.get_data_size() / effective_mtu) - 1

        if final > 8388608:  # 23 bit unsigned integer max.
            raise PacketTooLargeException(
                "Packet is too large to be fragmented properly."
            )

        pid = Fragmenter.get_next_identification()
        while offset < packet.get_data_size():
            if counter == final:
                fragments.append(
                    Fragment(
                        packet.get_data()[offset : (offset + effective_mtu)],
                        is_final=True,
                        identification=pid,
                        seq=counter,
                    )
                )
            else:
                fragments.append(
                    Fragment(
                        packet.get_data()[offset : (offset + effective_mtu)],
                        identification=pid,
                        seq=counter,
                    )
                )

            offset = offset + effective_mtu
            counter = counter + 1

        return fragments

    @staticmethod
    def process_packets(fragments: list[Union[Packet, Fragment]]) -> list[Packet]:
        """
        Processes fragments and packets. Partial packets will be kept track of in a dictionary
        until they can be completed or are discarded due to timeout. Packets and reassembled
        sequences will be returned as a list.
        """
        packets = []

        for f in fragments:
            if f.is_fragment():  # Reassembly required.
                id = f.get_identification()
                if f.get_identification() in Fragmenter.partial_packets.keys():
                    Fragmenter.partial_packets[id].add_fragment(f)
                else:
                    Fragmenter.partial_packets[id] = FragmentSequence(f)

                if Fragmenter.partial_packets[id].is_complete():
                    # Reassemble packet.
                    packets.append(Fragmenter.partial_packets.pop(id).reassemble())
            else:  # No reassembly required. Return the packet as is.
                packets.append(f)

        # Delete any fragments that have timed out.
        Fragmenter.discard_timeouted_partials()
        return packets

    @staticmethod
    def get_next_identification() -> int:
        """
        Increments the global packet id counter and returns the new value.
        """
        Fragmenter.identification_counter = Fragmenter.identification_counter + 1
        if Fragmenter.identification_counter > 16777215:  # 3 byte unsigned int max.
            Fragmenter.identification_counter = 1
        return Fragmenter.identification_counter

    @staticmethod
    def create_from_raw_data(data: bytearray) -> Union[Fragment, Packet]:
        """
        Helper function which calls the right constructor to create either
        a packet or a fragment, from a list of raw data.
        """
        if int.from_bytes(data[0:3], byteorder="big", signed=False) == 0:
            return Packet(data, no_header=True)

        return Fragment(data, no_header=True)

    @staticmethod
    def get_timeout_ms() -> int:
        """
        Gets the timeout duration in milliseconds.
        """
        return Fragmenter.timeout_ms

    @staticmethod
    def set_timeout_ms(timeout_ms) -> None:
        """
        Sets the timeout duration in milliseconds.
        """
        if timeout_ms <= 0:
            raise ValueError("Timeout must be a positive number.")

        Fragmenter.timeout_ms = timeout_ms

    @staticmethod
    def discard_timeouted_partials() -> None:
        """
        Discards partial packets which have reached timeout age.
        """
        # Check to ensure that cleanup doesn't occur to quickly after the previous one.
        if time.time() - Fragmenter.last_timeout_cleanup >= 2:
            return

        Fragmenter.last_timeout_cleanup = time.time()

        for key in Fragmenter.partial_packets.keys():
            if (
                Fragmenter.partial_packets[key].get_age_in_ms()
                >= Fragmenter.get_timeout_ms()
            ):
                Fragmenter.partial_packets.pop(key)
