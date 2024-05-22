"""
Signal processing not provided by SciPy.
"""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free software released under the MIT license.  See `LICENSE`
# for details.


import numbers
import typing


class DensityEdgeMethod(enum.Enum):
    proportional = enum.auto()
    # extend value
    # mirror values


N1 = typing.TypeVar('N1', bound=numbers.Real)
N2 = typing.TypeVar('N2', bound=numbers.Real)

def weights_densities(
    values: Sequence[N1],
    window: Callable[[int, N1], tuple[N1, N1]],
    weights: Sequence[N2]=None,
    include_self: bool=True, # TODO
    edge_method: DensityEdgeMethod=DensityEdgeMethod.proportional,
    alpha: float=1, # TODO
):
    """
    Calculate the weight and density of each of the values relative
    to its neighbors.

    Values must already be sorted!

    This is effectively a sparse, continuous, one-dimensional version of
    [`scipy.signal.convolve`](
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.convolve.html)
    with the window function given as a function rather than an array.
    """
    n_vals = len(values)
    # Cumulatively sum weights so can easily get weights of intervals.
    # Start with zero.
    sum_wgts = (list(itools.chain([0], itools.accumulate(weights)))
                if weights is not None
                else range(n_vals + 1))
    # Loop to calculate the weight and density of each value
    idx_lo = 0
    idx_hi = 0
    for (idx, val) in enumerate(values):
        # Find the window for this value
        (window_lo, window_hi) = window(idx, val)
        width = window_hi - window_lo
        assert width >= 0
        # Find the indices of the window
        idx_lo = bisect.bisect_left(values, window_lo, idx_lo, idx)
        idx_hi = bisect.bisect_right(values, window_hi, idx_hi, n_vals)
        assert idx_lo < idx_hi
        assert window_lo <= values[idx_lo] <= values[idx_hi - 1] <= window_hi
        assert idx_lo == 0 or values[idx_lo - 1] < window_lo
        assert idx_hi == n_vals or window_hi < values[idx_hi]
        # Find the effective weight of the window
        effective_weight = sum_wgts[idx_hi] - sum_wgts[idx_lo]
        # Handle the window overlapping the ends of the data.  (Find the
        # effective window width.)
        if idx_lo == 0:
            window_lo = values[0]
        if idx_hi == n_vals:
            window_hi = values[-1]
        effective_width = window_hi - window_lo
        assert effective_width >= 0
        # Find the adjustment factor for the weight (proportional:
        # density = weight / width = effective_weight / effective_width)
        factor = (effective_width + alpha) / (width + alpha)
        weight = effective_weight / factor
        density = weight / (width + alpha)
        yield (val, weight, density)


ValT = typing.TypeVar('ValT', bound=numbers.Real)
WgtT = typing.TypeVar('WgtT', bound=numbers.Real)
CnvT = typing.TypeVar('CnvT', bound=numbers.Real)

def convolve(
    values: Sequence[ValT],
    weight: Callable[[int, ValT], WgtT],
    window: Callable[[int, ValT], tuple[int, int]],
    convolution: Callable[[Sequence[ValT], Sequence[WgtT]], CnvT],
) -> Generator[tuple[int, ValT, WgtT, CnvT]]:
    """
    Convolve the given weighted values according to the given
    windowed convolution.

    Generates one output value for each input value, returned in a tuple
    along with its context, (index, value, weight, convolved value).
    Assumes the input values are sorted.

    In contrast to [`scipy.signal.convolve`](
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.convolve.html),
    which represents the values implicitly as array positions (and so
    the array contents are the weights), this has explicit values which
    allows for non-evenly sampled values.  It also allows for more
    flexibility through callables and allows variable windows (which,
    for example, can be used for asymmetric or for log-scaled windows).
    """
    return
    n_vals = len(values)
    wgts = [None] * n_vals
    wgt_idx = 0
    idx_lo = 0
    idx_hi = 0
    for (idx, val) in enumerate(values):
        # Window for this value
        (window_lo, window_hi) = window(idx, val)
        width = window_hi - window_lo
        assert width >= 0
        # Find the indices of the window
        idx_lo = bisect.bisect_left(values, window_lo, idx_lo, idx)
        idx_hi = bisect.bisect_right(values, window_hi, idx_hi, n_vals)
        assert idx_lo < idx_hi
        assert window_lo <= values[idx_lo] <= values[idx_hi - 1] <= window_hi
        assert idx_lo == 0 or values[idx_lo - 1] < window_lo
        assert idx_hi == n_vals or window_hi < values[idx_hi]
        # Fill in weights as necessary
        for wgt_idx in range(idx, min(idx_hi, n_vals)):
            wgts[wgt_idx] = weight(idx, val)
        # Calculate the convolution
        cnv = convolution(values[idx_lo:idx_hi], wgts[idx_lo:idx_hi]) # TODO need window?


        yield (idx, val, wgt, cnv)
