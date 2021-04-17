import numba
import numpy as np

# Placeholder globals that will be set in _target_jit_lookup()
CHARACTERISTIC = None  # The field's prime characteristic `p`
ORDER = None  # The field's order `p^m`

EXP = []  # EXP[i] = alpha^i
LOG = []  # LOG[i] = x, such that alpha^x = i
ZECH_LOG = []  # ZECH_LOG[i] = log(1 + alpha^i)
ZECH_E = None  # alpha^ZECH_E = -1, ZECH_LOG[ZECH_E] = -Inf

ADD_JIT = lambda x, y: x + y
MULTIPLY_JIT = lambda x, y: x * y


class TargetMixin(type):
    """
    A mixin class that provides the basics for compiling ufuncs.
    """
    # pylint: disable=no-value-for-parameter

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace, **kwargs)
        cls._EXP = None
        cls._LOG = None
        cls._ZECH_LOG = None

        cls._ufunc_add = None
        cls._ufunc_subtract = None
        cls._ufunc_multiply = None
        cls._ufunc_divide = None
        cls._ufunc_negative = None
        cls._ufunc_multiple_add = None
        cls._ufunc_power = None
        cls._ufunc_log = None
        cls._ufunc_poly_eval = None

        # Integer representations of the field's primitive element and primitive polynomial to be used in the
        # pure python ufunc implementations for `ufunc_mode = "object"`
        cls._primitive_element_dec = None
        cls._irreducible_poly_dec = None

    def _check_ufunc_mode(cls, mode):
        raise NotImplementedError

    def _build_lookup_tables(cls):
        """
        To be implemented in PrimeTargetMixin and ExtensionTargetMixin. Each class GF2Meta, GF2mMeta,
        GFpMeta, and GFpmMeta will inherit from either PrimeTargetMixin or ExtensionLookupMixin.
        """
        raise NotImplementedError

    def _target_jit_lookup(cls, target):
        """
        A method to JIT-compile the standard lookup arithmetic for any field. The functions that are
        JIT compiled are at the bottom of this file.
        """
        global CHARACTERISTIC, ORDER, EXP, LOG, ZECH_LOG, ZECH_E, ADD_JIT, MULTIPLY_JIT

        # Build the lookup tables if they don't exist
        if cls._EXP is None:
            cls._EXP, cls._LOG, cls._ZECH_LOG = cls._build_lookup_tables()

        # Export lookup tables to global variables so JIT compiling can cache the tables in the binaries
        CHARACTERISTIC = cls.characteristic
        ORDER = cls.order
        EXP = cls._EXP
        LOG = cls._LOG
        ZECH_LOG = cls._ZECH_LOG
        if cls.characteristic == 2:
            ZECH_E = 0
        else:
            ZECH_E = (cls.order - 1) // 2

        # JIT-compile add and multiply routines for reference in other routines
        ADD_JIT = numba.jit("int64(int64, int64)", nopython=True)(_add)
        MULTIPLY_JIT = numba.jit("int64(int64, int64)", nopython=True)(_multiply)

        kwargs = {"nopython": True, "target": target}
        if target == "cuda":
            kwargs.pop("nopython")

        # Create numba JIT-compiled ufuncs using the *current* EXP, LOG, and MUL_INV lookup tables
        cls._ufunc_add = numba.vectorize(["int64(int64, int64)"], **kwargs)(_add)
        cls._ufunc_subtract = numba.vectorize(["int64(int64, int64)"], **kwargs)(_subtract)
        cls._ufunc_multiply = numba.vectorize(["int64(int64, int64)"], **kwargs)(_multiply)
        cls._ufunc_divide = numba.vectorize(["int64(int64, int64)"], **kwargs)(_divide)
        cls._ufunc_negative = numba.vectorize(["int64(int64)"], **kwargs)(_additive_inverse)
        cls._ufunc_multiple_add = numba.vectorize(["int64(int64, int64)"], **kwargs)(_multiple_add)
        cls._ufunc_power = numba.vectorize(["int64(int64, int64)"], **kwargs)(_power)
        cls._ufunc_log = numba.vectorize(["int64(int64)"], **kwargs)(_log)
        cls._ufunc_poly_eval = numba.guvectorize([(numba.int64[:], numba.int64[:], numba.int64[:])], "(n),(m)->(m)", **kwargs)(_poly_eval)

    def _target_jit_calculate(cls, target):
        """
        To be implemented in GF2Meta, GF2mMeta, GFpMeta, and GFpmMeta. The functions that will
        be JIT-compiled will be located at the bottom of those files.
        """
        raise NotImplementedError

    def _target_python_calculate(cls):
        cls._ufunc_add = np.frompyfunc(cls._add_python, 2, 1)
        cls._ufunc_subtract = np.frompyfunc(cls._subtract_python, 2, 1)
        cls._ufunc_multiply = np.frompyfunc(cls._multiply_python, 2, 1)
        cls._ufunc_divide = np.frompyfunc(cls._divide_python, 2, 1)
        cls._ufunc_negative = np.frompyfunc(cls._additive_inverse_python, 1, 1)
        cls._ufunc_multiple_add = np.frompyfunc(cls._multiple_add_python, 2, 1)
        cls._ufunc_power = np.frompyfunc(cls._power_python, 2, 1)
        cls._ufunc_log = np.frompyfunc(cls._log_python, 1, 1)
        cls._ufunc_poly_eval = np.vectorize(cls._poly_eval_python, excluded=["coeffs"], otypes=[np.object_])

    ###############################################################################
    # Pure python arithmetic methods
    ###############################################################################

    def _add_python(cls, a, b):
        """
        To be implemented by GF2, GF2m, GFp, and GFpm.
        """
        raise NotImplementedError

    def _subtract_python(cls, a, b):
        """
        To be implemented by GF2, GF2m, GFp, and GFpm.
        """
        raise NotImplementedError

    def _multiply_python(cls, a, b):
        """
        To be implemented by GF2, GF2m, GFp, and GFpm.
        """
        raise NotImplementedError

    def _divide_python(cls, a, b):
        if a == 0 or b == 0:
            # NOTE: The b == 0 condition will be caught outside of the ufunc and raise ZeroDivisonError
            return 0
        b_inv = cls._multiplicative_inverse_python(b)
        return cls._multiply_python(a, b_inv)

    def _additive_inverse_python(cls, a):
        """
        To be implemented by GF2, GF2m, GFp, and GFpm.
        """
        raise NotImplementedError

    def _multiplicative_inverse_python(cls, a):
        """
        To be implemented by GF2, GF2m, GFp, and GFpm.
        """
        raise NotImplementedError

    def _multiple_add_python(cls, a, multiple):
        b = multiple % cls.characteristic
        return cls._multiply_python(a, b)

    def _power_python(cls, a, power):
        """
        Square and Multiply Algorithm

        a^13 = (1) * (a)^13
            = (a) * (a)^12
            = (a) * (a^2)^6
            = (a) * (a^4)^3
            = (a * a^4) * (a^4)^2
            = (a * a^4) * (a^8)
            = result_m * result_s
        """
        # NOTE: The a == 0 and b < 0 condition will be caught outside of the the ufunc and raise ZeroDivisonError
        if power == 0:
            return 1
        elif power < 0:
            a = cls._multiplicative_inverse_python(a)
            power = abs(power)

        result_s = a  # The "squaring" part
        result_m = 1  # The "multiplicative" part

        while power > 1:
            if power % 2 == 0:
                result_s = cls._multiply_python(result_s, result_s)
                power //= 2
            else:
                result_m = cls._multiply_python(result_m, result_s)
                power -= 1

        result = cls._multiply_python(result_m, result_s)

        return result

    def _log_python(cls, beta):
        """
        TODO: Replace this with more efficient algorithm

        alpha in GF(p^m) and generates field
        beta in GF(p^m)

        gamma = log_primitive_element(beta), such that: alpha^gamma = beta
        """
        # Naive algorithm
        result = 1
        for i in range(0, cls.order - 1):
            if result == beta:
                break
            result = cls._multiply_python(result, cls.primitive_element)
        return i

    def _poly_eval_python(cls, coeffs, values):
        result = coeffs[0]
        for j in range(1, coeffs.size):
            p = cls._multiply_python(result, values)
            result = cls._add_python(coeffs[j], p)
        return result


###################################################################################
# Galois field arithmetic for any field using EXP, LOG, and ZECH_LOG lookup tables
###################################################################################

def _add(a, b):  # pragma: no cover
    """
    a in GF(p^m)
    b in GF(p^m)
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    a + b = alpha^m + alpha^n
          = alpha^m * (1 + alpha^(n - m))  # If n is larger, factor out alpha^m
          = alpha^m * alpha^ZECH_LOG(n - m)
          = alpha^(m + ZECH_LOG(n - m))
    """
    m = LOG[a]
    n = LOG[b]

    # LOG[0] = -Inf, so catch these conditions
    if a == 0:
        return b
    if b == 0:
        return a

    if m > n:
        # We want to factor out alpha^m, where m is smaller than n, such that `n - m` is always positive. If
        # m is larger than n, switch a and b in the addition.
        m, n = n, m

    if n - m == ZECH_E:
        # ZECH_LOG[ZECH_E] = -Inf and alpha^(-Inf) = 0
        return 0

    return EXP[m + ZECH_LOG[n - m]]


def _subtract(a, b):  # pragma: no cover
    """
    a in GF(p^m)
    b in GF(p^m)
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    a - b = alpha^m - alpha^n
          = alpha^m + (-alpha^n)
          = alpha^m + (-1 * alpha^n)
          = alpha^m + (alpha^e * alpha^n)
          = alpha^m + alpha^(e + n)
    """
    # Same as addition if n = LOG[b] + e
    m = LOG[a]
    n = LOG[b] + ZECH_E

    # LOG[0] = -Inf, so catch these conditions
    if b == 0:
        return a
    if a == 0:
        return EXP[n]

    if m > n:
        # We want to factor out alpha^m, where m is smaller than n, such that `n - m` is always positive. If
        # m is larger than n, switch a and b in the addition.
        m, n = n, m

    z = n - m
    if z == ZECH_E:
        # ZECH_LOG[ZECH_E] = -Inf and alpha^(-Inf) = 0
        return 0
    if z >= ORDER - 1:
        # Reduce index of ZECH_LOG by the multiplicative order of the field, i.e. `order - 1`
        z -= ORDER - 1

    return EXP[m + ZECH_LOG[z]]


def _multiply(a, b):  # pragma: no cover
    """
    a in GF(p^m)
    b in GF(p^m)
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    a * b = alpha^m * alpha^n
          = alpha^(m + n)
    """
    m = LOG[a]
    n = LOG[b]

    # LOG[0] = -Inf, so catch these conditions
    if a == 0 or b == 0:
        return 0

    return EXP[m + n]


def _divide(a, b):  # pragma: no cover
    """
    a in GF(p^m)
    b in GF(p^m)
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    a / b = alpha^m / alpha^n
          = alpha^(m - n)
          = 1 * alpha^(m - n)
          = alpha^(ORDER - 1) * alpha^(m - n)
          = alpha^(ORDER - 1 + m - n)
    """
    m = LOG[a]
    n = LOG[b]

    # LOG[0] = -Inf, so catch these conditions
    if a == 0 or b == 0:
        # NOTE: The b == 0 condition will be caught outside of the ufunc and raise ZeroDivisonError
        return 0

    # We add `ORDER - 1` to guarantee the index is non-negative
    return EXP[(ORDER - 1) + m - n]


def _additive_inverse(a):  # pragma: no cover
    """
    a in GF(p^m)
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    -a = -alpha^n
       = -1 * alpha^n
       = alpha^e * alpha^n
       = alpha^(e + n)
    """
    n = LOG[a]

    # LOG[0] = -Inf, so catch these conditions
    if a == 0:
        return 0

    return EXP[ZECH_E + n]


def _multiplicative_inverse(a):  # pragma: no cover
    """
    a in GF(p^m)
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    1 / a = 1 / alpha^m
          = alpha^(-m)
          = 1 * alpha^(-m)
          = alpha^(ORDER - 1) * alpha^(-m)
          = alpha^(ORDER - 1 - m)
    """
    m = LOG[a]

    # LOG[0] = -Inf, so catch these conditions
    if a == 0:
        # NOTE: The a == 0 condition will be caught outside of the ufunc and raise ZeroDivisonError
        return 0

    return EXP[(ORDER - 1) - m]


def _multiple_add(a, b_int):  # pragma: no cover
    """
    a in GF(p^m)
    b_int in Z
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}
    b in GF(p^m)

    a . b_int = a + a + ... + a = b_int additions of a
    a . p_int = 0, where p_int is the prime characteristic of the field

    a . b_int = a * ((b_int // p_int)*p_int + b_int % p_int)
              = a * ((b_int // p_int)*p_int) + a * (b_int % p_int)
              = 0 + a * (b_int % p_int)
              = a * (b_int % p_int)
              = a * b, field multiplication

    b = b_int % p_int
    """
    b = b_int % CHARACTERISTIC
    m = LOG[a]
    n = LOG[b]

    # LOG[0] = -Inf, so catch these conditions
    if a == 0 or b == 0:
        return 0

    return EXP[m + n]


def _power(a, b_int):  # pragma: no cover
    """
    a in GF(p^m)
    b_int in Z
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    a ** b_int = alpha^m ** b_int
               = alpha^(m * b_int)
               = alpha^(m * ((b_int // (ORDER - 1))*(ORDER - 1) + b_int % (ORDER - 1)))
               = alpha^(m * ((b_int // (ORDER - 1))*(ORDER - 1)) * alpha^(m * (b_int % (ORDER - 1)))
               = 1 * alpha^(m * (b_int % (ORDER - 1)))
               = alpha^(m * (b_int % (ORDER - 1)))
    """
    m = LOG[a]

    if b_int == 0:
        return 1

    # LOG[0] = -Inf, so catch these conditions
    if a == 0:
        return 0

    return EXP[(m * b_int) % (ORDER - 1)]


def _log(a):  # pragma: no cover
    """
    a in GF(p^m)
    alpha is a primitive element of GF(p^m), such that GF(p^m) = {0, 1, alpha^1, ..., alpha^(p^m - 2)}

    log_primitive_element(a) = log_primitive_element(alpha^m)
                 = m
    """
    return LOG[a]


def _poly_eval(coeffs, values, results):  # pragma: no cover
    for i in range(values.size):
        results[i] = coeffs[0]
        for j in range(1, coeffs.size):
            results[i] = ADD_JIT(coeffs[j], MULTIPLY_JIT(results[i], values[i]))