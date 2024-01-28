"""
Generators for combinatorial sequences of sets.

In particular, `balanced_subsets` generates balanced subsets for
balanced incomplete block designs
(https://en.wikipedia.org/wiki/Block_design) such as would be applicable
for cross validation.
"""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free software released under the MIT license.  See `LICENSE` for
# details.


from collections.abc import Callable, Generator
import heapq
import itertools as itools
import typing

T = typing.TypeVar('T')


def _subsets(
        set: tuple | list, min_size: int=1, max_size: int | None=None,
) -> Generator[tuple]:
    if max_size is None:
        max_size = len(set)
    for subset_size in range(min_size, max_size + 1):
        for idxs in itools.combinations(range(len(set)), subset_size):
            yield tuple(set[i] for i in idxs)

def _score_ksubset_by_sum_counts_subsets(
        counts: dict[tuple, int], subsets: list[tuple]) -> int:
    return sum(counts.get(s, 0) for s in subsets)

def _score_ksubset_by_size2count_desc(
        counts: dict[tuple, int], subsets: list[tuple]) -> tuple:
    size2count = {}
    for subset in subsets:
        size = len(subset)
        size2count[size] = size2count.get(size, 0) + counts.get(subset, 0)
    return tuple(c for (s, c) in sorted(size2count.items(), reverse=True))

def _ksubset_min_score(
        ksubsets: list[tuple],
        subsets: list[list[tuple]],
        score_func: Callable[[tuple, list[tuple]], T],
) -> tuple[int, tuple, T]:
    idx_min = None
    min_score = None
    for (idx, (ksubset, subsets)) in enumerate(
            zip(ksubsets, subsets, strict=True)):
        score = score_func(ksubset, subsets)
        if min_score is None or score < min_score or (
                # Break ties lexicographically
                score == min_score and ksubset < ksubsets[idx_min]):
            min_score = score
            idx_min = idx
    return (idx_min, ksubsets[idx_min], min_score)

def _count_subsets(counts: dict[tuple, int], subsets: list[tuple]) -> None:
    for subset in subsets:
        counts[subset] = counts.get(subset, 0) + 1

def balanced_subsets__repeated_min_score(
        n_elements: int,
        subset_size: int,
        balance_level: int | None=None,
        delete_after_yield: bool=True,
) -> Generator[tuple]:
    # This algorithm needs the full balance level as a tie-breaker
    # crutch
    if balance_level is None:
        balance_level = subset_size
    counts = {}
    ksubsets = list(itools.combinations(range(n_elements), subset_size))
    subsets = [list(_subsets(s, 1, balance_level)) for s in ksubsets]
    # Repeatedly generate the ksubset with the minimum score until all
    # ksubsets have been generated
    n_ksubsets = len(ksubsets)
    for _ in range(n_ksubsets):
        scores_ksubsets = [
            (_score_ksubset_by_size2count_desc(counts, subs), ksub)
            for (ksub, subs) in zip(ksubsets, subsets, strict=True)]
        (score, ksubset) = min(scores_ksubsets)
        yield ksubset
        idx_min = scores_ksubsets.index((score, ksubset))
        _count_subsets(counts, subsets[idx_min])
        if delete_after_yield:
            del ksubsets[idx_min]
            del subsets[idx_min]

def balanced_subsets__heapq(
        n_elements: int,
        subset_size: int,
        balance_level: int | None=None,
) -> Generator[tuple]:
    # This algorithm doesn't actually need to track the largest subsets
    # as those are only ever generated once.  Thus, `balance_level =
    # subset_size - 1` is effectively the largest balance level.
    if balance_level is None or balance_level >= subset_size:
        balance_level = subset_size - 1
    counts = {}
    score = (0,) * balance_level
    ksubsets_q = list((score, ksubset, list(_subsets(ksubset, 1, balance_level)))
                      for ksubset in itools.combinations(range(n_elements), subset_size))
    while len(ksubsets_q) > 0:
        (old_score, ksubset, its_subsets) = heapq.heappop(ksubsets_q)
        new_score = _score_ksubset_by_size2count_desc(counts, its_subsets)
        if old_score == new_score:
            yield ksubset
            _count_subsets(counts, its_subsets)
        else:
            heapq.heappush(ksubsets_q, (new_score, ksubset, its_subsets))

def balanced_subsets(
        n_elements: int,
        subset_size: int,
        balance_level: int | None=None,
) -> Generator[tuple]:
    """
    Generate k-subsets of the given n elements in a balanced order.

    This generates combinations (like `itertools.combinations`), but in
    an order that balances the occurrences as much as possible.  That
    is, every next subset maintains balance invariants so that one can
    incrementally generate a sequence of subsets of arbitrary length
    that is as balanced as possible at all times.  Subsets are balanced
    if their subsets (up to size 'balance_level') occur equally many
    times.

    This is useful for generating experimental designs known as balanced
    incomplete block designs.

    For example, generating the 10 3-subsets of 5 elements in a balanced
    way produces the sequence

        {0, 1, 2}, {0, 3, 4}, {1, 2, 3}, {0, 1, 4}, {2, 3, 4},
        {0, 1, 3}, {0, 2, 4}, {1, 2, 4}, {0, 2, 3}, {1, 3, 4}.

    They are balanced because, after every next subset, the counts of
    individual elements, pairs, and triples are as close as possible.
    Continuing the example, the following matrices of counts, where the
    individual elements are counted on the diagonal and the pairs are
    counted above the diagonal, show that the imbalance in singles is at
    most 1 and in pairs is at most 2.  (The imbalance in triples is at
    most 1 at all times because each has either already been generated
    or not.)

        After First 3   After First 5   After All 10 Subsets
          0 1 2 3 4       0 1 2 3 4       0 1 2 3 4
        0 2 1 1 1 1     0 3 2 1 1 1     0 6 3 3 3 3
        1   2 2 1 0     1   3 2 1 1     1   6 3 3 3
        2     2 1 0     2     3 2 1     2     6 3 3
        3       2 1     3       3 2     3       6 3
        4         1     4         3     4         6

    The k-subsets are generated as tuples on the integers `range(0,
    n_elements)` so that the elements can easily index into a list of
    items.

    subset_size: int

        Size of subsets to generate, k.

    balance_level: int | None = None

        Maximum size of subset to keep balanced.  That is, subsets of
        sizes '1:balance_level' are kept balanced.  When `None`, uses
        `subset_size` to achieve the maximum balance.
    """
    return balanced_subsets__heapq(n_elements, subset_size, balance_level)
