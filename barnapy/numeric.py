"""Numeric algorithms and general number processing."""

# Copyright (c) 2020 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import heapq
import math


def nearest_integers(reals, budget, min_int=0):
    """
    Find the integers that are closest to the given reals within the
    given budget (sum of integers).

    Providing a minimum integer bounds the integers away from zero but
    proportionally shrinks the largest integers.  This distorts the
    shape of the integers compared to the shape of the reals.


    # Examples #

    ```
    >>> nearest_integers([0.1, -0.2, 0.3, 10.0], 10, 1)
    [1, -1, 1, 7]
    ```
    """
    reals = list(reals)
    budget = int(budget)
    # Check for sufficient budget
    if budget < (min_int * len(reals)):
        raise ValueError(
            'Insufficient budget for {} times the minimum {}: {}'
            .format(len(reals), min_int, budget))
    # Make everything positive to enable proportions
    signs = [1] * len(reals)
    for (idx, flt) in enumerate(reals):
        if flt < 0:
            reals[idx] = math.fabs(flt)
            signs[idx] = -1
    total_reals = math.fsum(reals)
    target_reals = [r * budget / total_reals for r in reals]
    # Calculate the nearest integers to the target reals
    ints = [max(round(r), min_int) for r in target_reals]
    #breakpoint()
    # Adjust until the budget is satisfied
    total_ints = sum(ints)
    if total_ints != budget:
        delta = budget - total_ints
        sign = 1 if delta >= 0 else -1
        # Create a priority queue of integers to adjust, prioritized by
        # the largest difference that matches the sign of the delta
        pq = [(sign * (ints[idx] - target_reals[idx]), idx)
              for idx in range(len(ints))]
        heapq.heapify(pq)
        # Adjust the largest difference by one until the budget is
        # satisfied
        while total_ints != budget and len(pq) > 0:
            _, idx = heapq.heappop(pq)
            # Enforce minimum: only update if new value will be above
            # minimum; otherwise drop (do not re-push) integer at this
            # index from consideration
            new_int = ints[idx] + sign
            if new_int >= min_int:
                ints[idx] = new_int
                total_ints += sign
                heapq.heappush(
                    pq, (sign * (ints[idx] - target_reals[idx]), idx))
        if total_ints != budget:
            raise ValueError(
                'Budget not met: Not enough candidate integers to adjust')
    # Apply the signs and return
    return [s * i for (s, i) in zip(signs, ints)]
