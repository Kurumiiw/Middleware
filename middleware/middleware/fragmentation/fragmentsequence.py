from __future__ import annotations
from typing import Dict, List, Optional, Union
import time
from middleware.fragmentation.fragment import Fragment
from middleware.fragmentation.packet import Packet


class FragmentSequence:
    """
    This class is intended for collecting fragments for reassembly.
    """

    def __init__(self, fragment: Fragment):
        # Used for storing the timestamp at which the last fragment was received.
        self.last_fragment_received = int(time.time() * 1000)

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
            self.identification = fragment.get_identification()

        # Verify ID
        if self.identification != fragment.get_identification():
            raise ValueError(
                "Fragment identification does not match existing fragment identifications."
            )

        # Check that fragment doesn't already exist
        if fragment.get_fragment_number() in self.fragments.keys():
            raise ValueError("This packet has already been added to the PartialPacket")

        self.last_fragment_received = int(time.time() * 1000)
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
        return int(time.time() * 1000 - self.last_fragment_received)

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
