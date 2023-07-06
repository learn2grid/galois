"""
A module containing LUTs for primitive elements.
"""

from .primitive_elements_2 import (
    PRIMITIVE_ELEMENTS_2_2,
    PRIMITIVE_ELEMENTS_2_3,
    PRIMITIVE_ELEMENTS_2_4,
    PRIMITIVE_ELEMENTS_2_5,
    PRIMITIVE_ELEMENTS_2_6,
)
from .primitive_elements_3 import (
    PRIMITIVE_ELEMENTS_3_2,
    PRIMITIVE_ELEMENTS_3_3,
    PRIMITIVE_ELEMENTS_3_4,
)
from .primitive_elements_5 import (
    PRIMITIVE_ELEMENTS_5_2,
    PRIMITIVE_ELEMENTS_5_3,
    PRIMITIVE_ELEMENTS_5_4,
)

PRIMITIVE_ELEMENTS = [
    (2, 2, PRIMITIVE_ELEMENTS_2_2),
    (2, 3, PRIMITIVE_ELEMENTS_2_3),
    (2, 4, PRIMITIVE_ELEMENTS_2_4),
    (2, 5, PRIMITIVE_ELEMENTS_2_5),
    (2, 6, PRIMITIVE_ELEMENTS_2_6),
    (3, 2, PRIMITIVE_ELEMENTS_3_2),
    (3, 3, PRIMITIVE_ELEMENTS_3_3),
    (3, 4, PRIMITIVE_ELEMENTS_3_4),
    (5, 2, PRIMITIVE_ELEMENTS_5_2),
    (5, 3, PRIMITIVE_ELEMENTS_5_3),
    (5, 4, PRIMITIVE_ELEMENTS_5_4),
]