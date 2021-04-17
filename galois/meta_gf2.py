import numba
import numpy as np

from .dtypes import DTYPES
from .meta_gf import GFMeta
from .meta_mixin_prime_field import PrimeFieldMixin

# Field attribute globals
CHARACTERISTIC = None  # The prime characteristic `p` of the Galois field

# Placeholder functions to be replaced by JIT-compiled function
ADD_JIT = lambda x, y: x + y
MULTIPLY_JIT = lambda x, y: x * y


class GF2Meta(GFMeta, PrimeFieldMixin):
    """
    Create an array over :math:`\\mathrm{GF}(2)`.

    Note
    ----
        This Galois field class is a pre-made subclass of :obj:`galois.GFArray`. It is included in the package
        because of the ubiquity of :math:`\\mathrm{GF}(2)` fields.

        .. ipython:: python

            # The pre-made GF(2) class
            print(galois.GF2)

            # The GF class factory for an order of 2 returns `galois.GF2`
            GF2 = galois.GF(2); print(GF2)
            GF2 is galois.GF2

    Parameters
    ----------
    array : array_like
        The input array to be converted to a Galois field array. The input array is copied, so the original array
        is unmodified by changes to the Galois field array. Valid input array types are :obj:`numpy.ndarray`,
        :obj:`list`, :obj:`tuple`, or :obj:`int`.
    dtype : numpy.dtype, optional
        The :obj:`numpy.dtype` of the array elements. The default is :obj:`numpy.int64`.

    Returns
    -------
    galois.GF2
        The copied input array as a :math:`\\mathrm{GF}(2)` field array.

    Examples
    --------

    Various Galois field properties are accessible as class attributes.

    .. ipython:: python

        print(galois.GF2)
        galois.GF2.characteristic
        galois.GF2.degree
        galois.GF2.order
        galois.GF2.irreducible_poly

    Construct arrays over :math:`\\mathrm{GF}(2)`.

    .. ipython:: python

        a = galois.GF2([1,0,1,1]); a
        b = galois.GF2([1,1,1,1]); b

    Perform array arithmetic over :math:`\\mathrm{GF}(2)`.

    .. ipython:: python

        # Element-wise addition
        a + b

        # Element-wise subtraction
        a - b

        # Element-wise multiplication
        a * b

        # Element-wise division
        a / b
    """
    # pylint: disable=abstract-method,no-value-for-parameter

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace, **kwargs)
        cls._characteristic = 2
        cls._degree = 1
        cls._order = cls.characteristic**cls.degree
        cls._irreducible_poly = None  # Will be set in __init__.py to avoid circular import with Poly
        cls._primitive_element = 1
        cls._dtypes = cls._valid_dtypes()

        cls.target(kwargs["target"], kwargs["mode"])

        cls._primitive_element = cls(cls.primitive_element)
        cls._is_primitive_poly = True

    def _valid_dtypes(cls):
        dtypes = [dtype for dtype in DTYPES if np.iinfo(dtype).max >= cls.order - 1]
        if len(dtypes) == 0:
            dtypes = [np.object_]
        return dtypes

    def _check_ufunc_mode(cls, mode):
        if mode not in ["auto", "calculate"]:
            raise ValueError(f"{cls.name} arrays can only be targeted in 'calculate' mode, not {mode}. For {cls.name} arrays 'calculate' mode is always fastest.")
        return "calculate"

    def _target_jit_calculate(cls, target):
        global CHARACTERISTIC, ADD_JIT, MULTIPLY_JIT
        CHARACTERISTIC = cls._characteristic

        # JIT-compile add and multiply routines for reference in polynomial evaluation routine
        ADD_JIT = numba.jit("int64(int64, int64)", nopython=True)(_add_jit)
        MULTIPLY_JIT = numba.jit("int64(int64, int64)", nopython=True)(_multiply_jit)

        kwargs = {"nopython": True, "target": target}
        if target == "cuda":
            kwargs.pop("nopython")

        # Create numba JIT-compiled ufuncs using the *current* EXP, LOG, and MUL_INV lookup tables
        cls._ufunc_add = numba.vectorize(["int64(int64, int64)"], **kwargs)(_add_jit)
        cls._ufunc_subtract = numba.vectorize(["int64(int64, int64)"], **kwargs)(_subtract_jit)
        cls._ufunc_multiply = numba.vectorize(["int64(int64, int64)"], **kwargs)(_multiply_jit)
        cls._ufunc_divide = numba.vectorize(["int64(int64, int64)"], **kwargs)(_divide_jit)
        cls._ufunc_negative = numba.vectorize(["int64(int64)"], **kwargs)(_negative_jit)
        cls._ufunc_multiple_add = numba.vectorize(["int64(int64, int64)"], **kwargs)(_multiple_add_jit)
        cls._ufunc_power = numba.vectorize(["int64(int64, int64)"], **kwargs)(_power_jit)
        cls._ufunc_log = numba.vectorize(["int64(int64)"], **kwargs)(_log_jit)
        cls._ufunc_poly_eval = numba.guvectorize([(numba.int64[:], numba.int64[:], numba.int64[:])], "(n),(m)->(m)", **kwargs)(_poly_eval_jit)


###############################################################################
# Galois field arithmetic, explicitly calculated without lookup tables
###############################################################################

def _add_jit(a, b):  # pragma: no cover
    return a ^ b


def _subtract_jit(a, b):  # pragma: no cover
    return a ^ b


def _multiply_jit(a, b):  # pragma: no cover
    return a & b


def _divide_jit(a, b):  # pragma: no cover
    if b == 0:
        # NOTE: The b == 0 condition will be caught outside of the ufunc and raise ZeroDivisonError
        return 0
    else:
        return a


def _negative_jit(a):  # pragma: no cover
    return a


def _multiple_add_jit(a, multiple):  # pragma: no cover
    multiple = multiple % CHARACTERISTIC
    return MULTIPLY_JIT(a, multiple)


def _power_jit(a, power):  # pragma: no cover
    # NOTE: The a == 0 and b < 0 condition will be caught outside of the the ufunc and raise ZeroDivisonError
    if power == 0:
        return 1
    elif a == 0:
        return 0
    else:
        return a


def _log_jit(a):  # pragma: no cover
    # pylint: disable=unused-argument
    # NOTE: The a == 0 condition will be caught outside of the ufunc and raise ArithmeticError
    return 0


def _poly_eval_jit(coeffs, values, results):  # pragma: no cover
    for i in range(values.size):
        results[i] = coeffs[0]
        for j in range(1, coeffs.size):
            results[i] = ADD_JIT(coeffs[j], MULTIPLY_JIT(results[i], values[i]))