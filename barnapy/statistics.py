# Statistics functions not provided in the standard library or in NumPy
# / SciPy.

import math

# TODO add interpolation a la numpy.percentile (lower, upper, nearest, midpoint, linear)
# TODO update to algorithm that doesn't need to store / sort all data
def quantile(data, probability, key=None):
    """Return the smallest item `x` of the data such that
    `probability <= empirical-CDF(x)`.

    This is the inverse of the empirical cumulative distribution
    function.  As such, all the quantiles are given as exemplars; that
    is, the returned quantiles are elements of the given data and are
    not computed in any way.  This allows for non-numerical data.

    `quantile(data, 0)` returns the minimum, `quantile(data, 1)` returns
    the maximum, and `quantile(data, 1/2)` returns the exemplar median.

    * data: Iterable of items.
    * probability: Probability of the desired quantile.
    * key: Function providing an ordering key for each data item, like
      for `sorted`.  If `None`, the item is its own key.
    """
    if not (0 <= probability <= 1):
        raise ValueError(
            'Probability not in [0,1]: {}'.format(probability))
    data = sorted(data, key=key)
    len_data = len(data)
    if len_data == 0:
        raise ValueError('Empty data.')
    # TODO Document why this is correct.  See notebook.  Refs in Gibbons and Chakraborti?
    quantile_idx = math.ceil(len_data * probability) - 1
    # Handle Q(0) as a special case (0 is the only probability that
    # makes quantile_idx == -1)
    if quantile_idx == -1:
        quantile_idx = 0
    return data[quantile_idx]
