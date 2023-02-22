from __future__ import annotations
import time
from typing import Tuple, Union
from middleware.fragmentation.partialpacket import PartialPacket
from middleware.fragmentation.packet import Packet
from middleware.fragmentation.fragment import Fragment
import math
from collections import defaultdict

MAX_TCP_HEADER_BYTES = 60


class EffectiveMTUTooLowError(ValueError):
    """
    Raised when adjusting provided MTU for TCP/header overhead results in a value lower than or equal to 0.
    """

    pass


class PacketTooLargeError(ValueError):
    """
    Raised when a packet being fragmented is too large to be fragmented.
    """

    pass


class Fragmenter:
    timeout_ms: int = 10000
    min_cleanup_interval_ms: int = 5000

    last_timeout_cleanup: int = 0

    identification_counter: int = 0

    # Used for keeping track of partially assembled packets.
    partial_packets: defaultdict[
        Tuple[str, int], dict[int, PartialPacket]
    ] = defaultdict(dict)

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
            raise EffectiveMTUTooLowError(
                "Adjusting mtu for TCP and header overhead resulted in a <=0 MTU. Please choose a larger MTU."
            )

        # No need to fragment if size is already < effective_mtu
        if packet.get_size() <= effective_mtu:
            return [packet]

        offset = 0
        counter = 0
        final = math.ceil(packet.get_data_size() / effective_mtu) - 1

        if final > 8388608:  # 23 bit unsigned integer max.
            raise PacketTooLargeError("Packet is too large to be fragmented properly.")

        id = Fragmenter.get_next_identification()
        while offset < packet.get_data_size():
            if counter == final:
                fragments.append(
                    Fragment(
                        packet.get_data()[offset : (offset + effective_mtu)],
                        source=packet.source,
                        is_final=True,
                        identification=id,
                        seq=counter,
                    )
                )
            else:
                fragments.append(
                    Fragment(
                        packet.get_data()[offset : (offset + effective_mtu)],
                        source=packet.source,
                        identification=id,
                        seq=counter,
                    )
                )

            offset = offset + effective_mtu
            counter = counter + 1

        return fragments

    @staticmethod
    def process_packet(fragment: Union[Packet, Fragment]) -> list[Packet]:
        """
        Wrapper function to ease the processing of a single packet/fragment.
        """
        result = Fragmenter.process_packets([fragment])
        if len(result) > 1:
            #This should never happen.
            raise Exception("Fragmenter.process_packet() returned more than one packet.") 
        return result

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
                if (
                    f.get_identification()
                    in Fragmenter.partial_packets[f.source].keys()
                ):
                    Fragmenter.partial_packets[f.source][id].add_fragment(f)
                else:
                    Fragmenter.partial_packets[f.source][id] = PartialPacket(f)

                if Fragmenter.partial_packets[f.source][id].is_complete():
                    # Reassemble packet.
                    packets.append(
                        Fragmenter.partial_packets[f.source].pop(id).reassemble()
                    )
            else:  # No reassembly required. Return the packet as is.
                packets.append(f)

        # Delete any fragments that have timed out.
        Fragmenter.discard_timeouted_partials()
        return packets

    @staticmethod
    def get_next_identification() -> int:
        """
        Increments the global identification counter and returns the new value.
        """
        Fragmenter.identification_counter = Fragmenter.identification_counter + 1
        if Fragmenter.identification_counter > 16777215:  # 3 byte unsigned int max.
            Fragmenter.identification_counter = 1
        return Fragmenter.identification_counter

    @staticmethod
    def create_from_raw_data(
        data: bytearray, *, source: Tuple[str, int]
    ) -> Union[Fragment, Packet]:
        """
        Helper function which calls the right constructor to create either
        a packet or a fragment, from a byte array of raw data.
        """
        if int.from_bytes(data[0:3], byteorder="big", signed=False) == 0:
            return Packet(data, source=source, no_header=True)

        return Fragment(data, source=source, no_header=True)

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
    def get_cleanup_interval_ms() -> int:
        """
        Returns the currently configured minimum interval between cleanup.
        """
        return Fragmenter.min_cleanup_interval_ms

    @staticmethod
    def set_cleanup_interval_ms(value: int) -> None:
        """
        Sets the minimum interval between cleanup of timeouted partial packages in
        milliseconds.
        """
        if value < 0:
            raise ValueError(
                "Cleanup interval should be greater than or equal to zero."
            )
        Fragmenter.min_cleanup_interval_ms = value

    @staticmethod
    def discard_timeouted_partials() -> None:
        """
        Discards partial packets which have reached timeout age.
        """
        # Check to ensure that cleanup doesn't occur to quickly after the previous one.
        if (
            int(time.time() * 1000) - Fragmenter.last_timeout_cleanup
            >= Fragmenter.get_cleanup_interval_ms()
        ):
            return

        Fragmenter.last_timeout_cleanup = int(time.time() * 1000)

        # TODO: Runtime scales with number of sources we are receiving from times number of partial fragments
        # we are currently storing. There may be a more efficient way of doing this that avoids nested loops,
        # but we can wait to see how it affects Service round-trip-delay before prematurely optimizing.
        for outer in Fragmenter.partial_packets.values():
            for key in outer.keys():
                if (
                    outer[key].get_time_since_last_fragment_received_ms()
                    >= Fragmenter.get_timeout_ms()
                ):
                    outer.pop(key)
