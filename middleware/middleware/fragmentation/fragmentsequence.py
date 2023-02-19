from __future__ import annotations
from typing import Dict, List, Optional, Union
import time
from middleware.fragmentation.fragment import Fragment
from middleware.fragmentation.packet import Packet


class FragmentSequence:
    """
    This class is intended for collecting fragments for reassembly.
    """

    # Static variable used to collect incomplete fragments.
    fragment_sequences: Dict[int, FragmentSequence] = {}

    def __init__(self, fragment: Fragment):
        # Used for calculating age.
        self.creation_time = int(time.time() * 1000)

        # Keeps track of the first fragment in the sequence that is still missing.
        self.first_unreceived_fragment: int = 0
        self.identification: Optional[int] = None
        self.final_fragment_number: Optional[int] = None

        self.fragments: Dict[int, Fragment] = {}

        self.add_fragment(fragment)

    def add_fragment(self, fragment: Fragment):
        """
        Adds a fragment to this partial packet.
        """
        if self.identification is None:
            # Initialize identification, so that future fragments can be verified to belong to this sequence.
            self.identification = fragment.get_packet_id()

        # Verify ID
        if self.identification != fragment.get_packet_id():
            raise ValueError(
                "Fragment identification does not match existing fragment identifications."
            )

        # Check that fragment doesn't already exist
        if fragment.get_fragment_number() in self.fragments.keys():
            raise ValueError("This packet has already been added to the PartialPacket")

        self.fragments[fragment.get_fragment_number()] = fragment

        # Update first_unreceived_fragment, marker if necessary
        if fragment.get_fragment_number() == self.first_unreceived_fragment:
            id = self.first_unreceived_fragment + 1
            while True:
                if not (id in self.fragments.keys()):
                    break

                id = id + 1

            self.first_unreceived_fragment = id

        if fragment.is_final_fragment():
            self.final_fragment_number = fragment.get_fragment_number()

    def get_age_in_ms(self) -> int:
        """
        Returns the elapsed time since the first packet in this sequence was processed in ms.
        """
        return int(time.time() * 1000 - self.creation_time)

    def is_complete(self) -> bool:
        """
        Checks if all fragments in sequence have been received, indicating that the packet
        is ready for reassembly.
        """
        if self.final_fragment_number is None:
            return False

        return self.first_unreceived_fragment >= self.final_fragment_number

    def reassemble(self) -> Packet:
        if not self.is_complete():
            raise Exception(
                "This packet is missing fragments and can not be reassembled yet."
            )

        data = bytearray()
        for f in sorted(self.fragments.values(), key=lambda p: p.get_fragment_number()):
            data = data + f.get_data()

        return Packet(data)

    @staticmethod
    def process_fragments(fragments: List[Union[Packet, Fragment]]) -> List[Packet]:
        """
        Processes fragments and packets. Partial packets will be kept track of in a dictionary
        until they can be completed or are discarded due to timeout. Packets and reassembled
        sequences will be returned as a list.
        """
        packets = []

        for f in fragments:
            if f.is_fragment():  # Reassembly required.
                id = f.get_packet_id()
                if f.get_packet_id() in FragmentSequence.fragment_sequences.keys():
                    FragmentSequence.fragment_sequences[id].add_fragment(f)
                else:
                    FragmentSequence.fragment_sequences[id] = FragmentSequence(f)

                if FragmentSequence.fragment_sequences[id].is_complete():
                    # Reassemble packet.
                    p = FragmentSequence.fragment_sequences[id].reassemble()
                    FragmentSequence.fragment_sequences.pop(id)
                    packets.append(p)
            else:  # No reassembly required. Return the packet as is.
                packets.append(f)

        return packets
