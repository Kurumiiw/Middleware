from middleware.configuration.config import config
from typing import Optional
import time
import math

DGRAM_ID_BITS = 28
FRAG_IDX_BITS = 11
UDP_IP_HEADER_SIZE = 28
MW_HEADER_SIZE = 5
TOTAL_HEADER_SIZE = UDP_IP_HEADER_SIZE + MW_HEADER_SIZE
MTU_MIN = 64
MAX_DGRAM_PAYLOAD = (MTU_MIN - TOTAL_HEADER_SIZE) * 2**FRAG_IDX_BITS
MAX_FRAG_PAYLOAD = config.mtu - TOTAL_HEADER_SIZE


class Fragmenter:
    current_dgram_id: int

    def __init__(self):
        self.current_dgram_id = 0

    def fragment(self, data: bytes) -> list[bytes]:
        if len(data) > MAX_DGRAM_PAYLOAD:
            raise ValueError(
                "Payload is too large to be sent with a MiddlewareUnreliable datagram"
            )

        dgram_id = self.current_dgram_id
        self.current_dgram_id = (self.current_dgram_id + 1) % 2**DGRAM_ID_BITS

        frag_count = int(math.ceil(len(data) / MAX_FRAG_PAYLOAD))

        fragments = []
        for frag_idx in range(frag_count):
            is_fin = int(frag_idx == frag_count - 1)

            header_bits = (dgram_id << 12) | (is_fin << 11) | frag_idx
            header = header_bits.to_bytes(length=5, byteorder="little", signed=False)

            fragment = bytearray()
            fragment.extend(header)
            fragment.extend(
                data[frag_idx * MAX_FRAG_PAYLOAD : (frag_idx + 1) * MAX_FRAG_PAYLOAD]
            )

            fragments.append(fragment)

        return fragments


class Reassembler:
    datagrams: dict

    class DatagramStoreEntry:
        timestamp: float
        is_fin: bool
        expected_frag_count: int
        frag_store: dict

        def __init__(self):
            self.timestamp = time.perf_counter()
            self.is_fin = False
            self.expected_frag_count = -1
            self.frag_store = {}

    def __init__(self):
        self.datagrams = {}

    def timeout_old_datagrams(self) -> None:
        """
        Goes through all received partial/complete datagrams and times out old ones based on
        the arrival of their first fragment
        """
        for key in list(self.datagrams.keys()):
            if (
                time.perf_counter() - self.datagrams[key].timestamp
            ) >= config.fragment_timeout:
                del self.datagrams[key]

    def add_fragment_to_datagram(self, frag: bytes, addr: tuple[str, int]) -> None:
        """
        Appends a fragment to a partial/complete datagram
        """
        header = frag[:MW_HEADER_SIZE]
        payload = frag[MW_HEADER_SIZE:]

        header_bits = int.from_bytes(header, byteorder="little", signed=False)
        dgram_id = (header_bits >> 12) & ((1 << DGRAM_ID_BITS) - 1)
        is_fin = bool(header_bits & (1 << 11))
        frag_idx = header_bits & ((1 << FRAG_IDX_BITS) - 1)

        if (addr, dgram_id) not in self.datagrams:
            self.datagrams[addr, dgram_id] = self.DatagramStoreEntry()

        self.datagrams[addr, dgram_id].frag_store[frag_idx] = payload

        if is_fin:
            self.datagrams[addr, dgram_id].is_fin = True
            self.datagrams[addr, dgram_id].expected_frag_count = frag_idx + 1

    def check_for_completed_datagrams(self) -> Optional[tuple[bytes, tuple[str, int]]]:
        """
        Returns the first complete datagram found, else None
        """
        for key in self.datagrams:
            if (
                self.datagrams[key].is_fin
                and len(self.datagrams[key].frag_store.keys())
                == self.datagrams[key].expected_frag_count
            ):
                frag_store = self.datagrams[key].frag_store
                addr = key[0]
                data = bytearray(
                    b"".join([frag_store[i] for i in range(len(frag_store.keys()))])
                )

                del self.datagrams[key]
                return data, addr
        return None
