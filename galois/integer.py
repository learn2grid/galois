"""
A module that contains integer arithmetic routines.
"""
import math
import sys

import numpy as np

from .overrides import set_module

__all__ = ["isqrt", "iroot", "ilog"]


@set_module("galois")
def isqrt(n):
    r"""
    Computes the integer square root of :math:`n` such that :math:`\textrm{isqrt}(n)^2 \le n`.

    Note
    ----
    This function is included for Python versions before 3.8. For Python 3.8 and later, this function
    calls :func:`math.isqrt` from the standard library.

    Parameters
    ----------
    n : int
        A non-negative integer.

    Returns
    -------
    int
        The integer square root of :math:`n` such that :math:`\textrm{isqrt}(n)^2 \le n`.

    Examples
    --------
    .. ipython:: python

        galois.isqrt(27**2 - 1)
        galois.isqrt(27**2)
        galois.isqrt(27**2 + 1)
    """
    if sys.version_info.major == 3 and sys.version_info.minor >= 8:
        return math.isqrt(n)  # pylint: disable=no-member
    else:
        if not isinstance(n, (int, np.integer)):
            raise TypeError(f"Argument `n` must be an integer, not {type(n)}.")
        if not n >= 0:
            raise ValueError(f"Argument `n` must be non-negative, not {n}.")

        n = int(n)
        if n < 2:
            return n

        small_candidate = isqrt(n >> 2) << 1
        large_candidate = small_candidate + 1
        if large_candidate * large_candidate > n:
            return small_candidate
        else:
            return large_candidate


@set_module("galois")
def iroot(n, k):
    r"""
    Finds the integer :math:`k`-th root :math:`x` of :math:`n`, such that :math:`x^k \le n`.

    Parameters
    ----------
    n : int
        A positive integer.
    k : int
        The root :math:`k`, must be at least 2.

    Returns
    -------
    int
        The integer :math:`k`-th root :math:`x` of :math:`n`, such that :math:`x^k \le n`

    Examples
    --------
    .. ipython :: python

        galois.iroot(27**5 - 1, 5)
        galois.iroot(27**5, 5)
        galois.iroot(27**5 + 1, 5)
    """
    if not isinstance(n, (int, np.integer)):
        raise TypeError(f"Argument `n` must be an integer, not {type(n)}.")
    if not isinstance(k, (int, np.integer)):
        raise TypeError(f"Argument `k` must be an integer, not {type(k)}.")
    if not n > 0:
        raise ValueError(f"Argument `n` must be positive, not {n}.")
    if not k >= 2:
        raise ValueError(f"Argument `k` must be at least 2, not {k}.")
    n, k = int(n), int(k)

    # https://stackoverflow.com/a/39191163/11694321
    u = n
    x = n + 1
    k1 = k - 1

    while u < x:
        x = u
        u = (k1*u + n // u**k1) // k

    return x


@set_module("galois")
def ilog(n, b):
    r"""
    Finds the integer :math:`\textrm{log}_b(n) = k`, such that :math:`b^k \le n`.

    Parameters
    ----------
    n : int
        A positive integer.
    b : int
        The logarithm base :math:`b`.

    Returns
    -------
    int
        The integer :math:`\textrm{log}_b(n) = k`, such that :math:`b^k \le n`.

    Examples
    --------
    .. ipython :: python

        galois.ilog(27**5 - 1, 27)
        galois.ilog(27**5, 27)
        galois.ilog(27**5 + 1, 27)
    """
    if not isinstance(n, (int, np.integer)):
        raise TypeError(f"Argument `n` must be an integer, not {type(n)}.")
    if not isinstance(b, (int, np.integer)):
        raise TypeError(f"Argument `b` must be an integer, not {type(b)}.")
    if not n > 0:
        raise ValueError(f"Argument `n` must be positive, not {n}.")
    if not b >= 2:
        raise ValueError(f"Argument `b` must be at least 2, not {b}.")
    n, b = int(n), int(b)

    # https://stackoverflow.com/a/39191163/11694321
    low, b_low, high, b_high = 0, 1, 1, b

    while b_high < n:
        low, b_low, high, b_high = high, b_high, high*2, b_high**2

    while high - low > 1:
        mid = (low + high) // 2
        b_mid = b_low * b**(mid - low)
        if n < b_mid:
            high, b_high = mid, b_mid
        elif b_mid < n:
            low, b_low = mid, b_mid
        else:
            return mid

    if b_high == n:
        return high

    return low