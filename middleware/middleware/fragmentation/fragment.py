from __future__ import annotations
from typing import Tuple
from middleware.fragmentation.packet import Packet


class Fragment(Packet):
    def __init__(
        self,
        data: bytearray,
        *,
        source: Tuple[str, int],
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

            raw.extend(identification.to_bytes(2, byteorder="big", signed = False))
            raw.extend(int.to_bytes(7 + len(data), 2, byteorder="big", signed = False))
            tmp = seq | (is_final << 23)
            raw.extend(tmp.to_bytes(3, byteorder="big"))

        raw.extend(data)

        super().__init__(raw, source=source, no_header=True)

    def get_header(self):
        return self.data[0:7]

    def get_data(self):
        return self.data[7:]

    def is_final_fragment(self) -> bool:
        """
        Returns true if the fragment is the final fragment in the sequence.
        """
        if (self.get_header()[4] >> 7) & 1:
            return True

        return False

    def get_sequence_number(self) -> int:
        """
        Returns the fragment sequence number.
        """
        # Ensure the final fragment flag is stripped before converting to integer.
        return (
            int.from_bytes(self.get_header()[4:7], byteorder="big", signed=False)
            & 0b011111111111111111111111
        )
