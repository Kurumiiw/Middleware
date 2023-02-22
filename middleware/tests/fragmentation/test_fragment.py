import pytest
import random
from middleware.fragmentation.fragment import Fragment

random.seed(42069)
SAMPLE_DATA = bytearray([145, 234, 255, 245])


def test_creation():
    f = Fragment(
        SAMPLE_DATA,
        source=("a", 1),
        is_final=False,
        identification=10,
        seq=5,
    )

    assert f.get_data() == SAMPLE_DATA
    assert f.get_identification() == 10
    assert f.get_sequence_number() == 5
    assert f.is_final_fragment() == False
    assert f.source == ("a", 1)

    f = Fragment(
        SAMPLE_DATA,
        source=("a", 1),
        is_final=True,
        identification=35000,
        seq=38948,
    )
    assert f.get_data() == SAMPLE_DATA
    assert f.get_identification() == 35000
    assert f.get_sequence_number() == 38948
    assert f.is_final_fragment() == True
    assert f.source == ("a", 1)


def test_constructor_validation():
    with pytest.raises(ValueError):
        Fragment(bytearray(), source=("a", 1), identification=10, seq=5)

    with pytest.raises(ValueError):
        Fragment(SAMPLE_DATA, source=("a", 1), identification=0, seq=0)
