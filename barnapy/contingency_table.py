"""2-by-2 contingency tables and scores"""

# Copyright (c) 2017 Aubrey Barnard.  This is free software released
# under the MIT license.  See LICENSE for details.


import math


class TwoByTwoTable(object):
    """Traditional 2-by-2 table as used in epidemiology, etc. to compare
    exposures and outcomes

    """

    _num_arg_types = (int, float)

    def __init__(
            self,
            exp_out=None, exp_no_out=None,
            out_no_exp=None, no_exp_out=None,
            exp_tot=None, out_tot=None, total=None,
            ):
        # Handle construction from 3-by-3 table corners
        if (isinstance(exp_out, self._num_arg_types)
            and isinstance(exp_tot, self._num_arg_types)
            and isinstance(out_tot, self._num_arg_types)
            and isinstance(total, self._num_arg_types)
            ):
            self._exp_out = exp_out
            self._exp_tot = exp_tot
            self._out_tot = out_tot
            self._total = total
        # Handle construction from 2-by-2 table
        elif (isinstance(exp_out, self._num_arg_types)
              and isinstance(exp_no_out, self._num_arg_types)
              and isinstance(out_no_exp, self._num_arg_types)
              and isinstance(no_exp_out, self._num_arg_types)
              ):
            self._exp_out = exp_out
            self._exp_tot = exp_out + exp_no_out
            self._out_tot = exp_out + out_no_exp
            self._total = (
                exp_out + exp_no_out + out_no_exp + no_exp_out)
        # Construction modes are only the above, bad arguments otherwise
        else:
            raise ValueError(
                'Insufficient {0} constructor arguments.'
                .format(self.__class__.__name__))

    @property
    def exp_out(self):
        return self._exp_out

    @property
    def exp_no_out(self):
        return self._exp_tot - self._exp_out

    @property
    def out_no_exp(self):
        return self._out_tot - self._exp_out

    @property
    def no_exp_out(self):
        return self._total - self._exp_tot - self._out_tot + self._exp_out

    @property
    def exp_tot(self):
        return self._exp_tot

    @property
    def no_exp_tot(self):
        return self._total - self._exp_tot

    @property
    def out_tot(self):
        return self._out_tot

    @property
    def no_out_tot(self):
        return self._total - self._out_tot

    @property
    def total(self):
        return self._total

    def smoothed(self, pseudocount=1):
        """Return a smoothed version of this table by adding the given
        pseudocount to each of the four cells.

        """
        return TwoByTwoTable(
            exp_out=self.exp_out + pseudocount,
            exp_no_out=self.exp_no_out + pseudocount,
            out_no_exp=self.out_no_exp + pseudocount,
            no_exp_out=self.no_exp_out + pseudocount,
            )

    def table_2x2(self, pseudocount=None):
        if isinstance(pseudocount, self._num_arg_types):
            return ((self.exp_out + pseudocount,
                     self.exp_no_out + pseudocount),
                    (self.out_no_exp + pseudocount,
                     self.no_exp_out + pseudocount))
        else:
            return ((self.exp_out, self.exp_no_out),
                    (self.out_no_exp, self.no_exp_out))

    def table_3x3(self, pseudocount=None):
        if isinstance(pseudocount, self._num_arg_types):
            return ((self.exp_out + pseudocount,
                     self.exp_no_out + pseudocount,
                     self.exp_tot + 2 * pseudocount),
                    (self.out_no_exp + pseudocount,
                     self.no_exp_out + pseudocount,
                     self.no_exp_tot + 2 * pseudocount),
                    (self.out_tot + 2 * pseudocount,
                     self.no_out_tot + 2 * pseudocount,
                     self.total + 4 * pseudocount))
        else:
            return ((self.exp_out, self.exp_no_out, self.exp_tot),
                    (self.out_no_exp, self.no_exp_out, self.no_exp_tot),
                    (self.out_tot, self.no_out_tot, self.total))


class TemporalTwoByTwoTable(TwoByTwoTable):
    """A temporal 2-by-2 table splits the first cell (exposure and outcome)
    into two counts: exposure before outcome and exposure after outcome.

    """

    def __init__(
            self,
            exp_bef_out=None, exp_aft_out=None, exp_out=None,
            exp_no_out=None, out_no_exp=None, no_exp_out=None,
            exp_tot=None, out_tot=None, total=None,
            ):
        # Construct this class
        if ((isinstance(exp_bef_out, self._num_arg_types)
             and isinstance(exp_aft_out, self._num_arg_types))
            or (isinstance(exp_out, self._num_arg_types)
                and (isinstance(exp_bef_out, self._num_arg_types)
                     or isinstance(exp_aft_out, self._num_arg_types)))
            ):
            self._exp_bef_out = (exp_bef_out
                                 if exp_bef_out is not None
                                 else exp_out - exp_aft_out)
            self._exp_aft_out = (exp_aft_out
                                 if exp_aft_out is not None
                                 else exp_out - exp_bef_out)
            exp_out = (exp_out
                       if exp_out is not None
                       else exp_bef_out + exp_aft_out)
            # Construct superclass
            super().__init__(
                exp_out, exp_no_out,
                out_no_exp, no_exp_out,
                exp_tot, out_tot, total,
                )
        # Otherwise arguments don't completely define a 2-by-2 table
        else:
            raise ValueError(
                'Insufficient {0} constructor arguments.'
                .format(self.__class__.__name__))

    @property
    def exp_bef_out(self):
        return self._exp_bef_out

    @property
    def exp_aft_out(self):
        return self._exp_aft_out

    def smoothed(self, pseudocount=1):
        """Return a smoothed version of this table by adding the given
        pseudocount to each of the four cells.

        """
        half_count = pseudocount / 2
        return TemporalTwoByTwoTable(
            exp_bef_out=self.exp_bef_out + half_count,
            exp_aft_out=self.exp_aft_out + half_count,
            exp_out=self.exp_out + pseudocount,
            exp_no_out=self.exp_no_out + pseudocount,
            out_no_exp=self.out_no_exp + pseudocount,
            no_exp_out=self.no_exp_out + pseudocount,
            )

    def cohort_table(self):
        """Creates a copy of this table that treats the counts as in a cohort
        study.  That is, 'exp_aft_out' is counted as part of
        'out_no_exp' rather than as part of 'exp_out'.  These are the
        counts a cohort study would use having followed subjects over
        time: the outcome happened first, so the exposure does not
        matter.

        """
        return TwoByTwoTable(
            exp_out=self.exp_bef_out,
            exp_tot=(self.exp_tot - self.exp_aft_out),
            out_tot=self.out_tot,
            total=self.total,
            )


def binary_mutual_information(table):
    """Return the mutual information between the two binary variables in the
    given 2-by-2 table

    """
    # Shortcut / Special-Case the zero distribution
    if table.total == 0:
        return 0.0
    # Do the calculation in a way that handles zeros.  (If the numerator
    # in the log is greater than zero, the denominator cannot be zero.)
    mi_sum = 0.0
    if table.exp_out > 0:
        mi_sum += (table.exp_out
                   * math.log((table.exp_out * table.total)
                              / (table.exp_tot * table.out_tot)))
    if table.exp_no_out > 0:
        mi_sum += (table.exp_no_out
                   * math.log((table.exp_no_out * table.total)
                              / (table.exp_tot * table.no_out_tot)))
    if table.out_no_exp > 0:
        mi_sum += (table.out_no_exp
                   * math.log((table.out_no_exp * table.total)
                              / (table.out_tot * table.no_exp_tot)))
    if table.no_exp_out > 0:
        mi_sum += (table.no_exp_out
                   * math.log((table.no_exp_out * table.total)
                              / (table.no_out_tot * table.no_exp_tot)))
    return mi_sum / table.total


def relative_risk(table):
    """Return the relative risk for the given 2-by-2 table"""
    # When all the cells are zero or both numerators are zero the rates
    # are "equal" so the relative risk is one
    if ((table.exp_tot == 0 and table.no_exp_tot == 0)
        or (table.exp_out == 0 and table.out_no_exp == 0)
        ):
        return 1.0
    # If the numerator rate is zero, then the relative risk cannot get
    # any less, so it is also zero
    elif table.exp_tot == 0:
        return 0.0
    # If the denominator rate is zero, then the relative risk cannot get
    # any larger, so it is infinity
    elif table.no_exp_tot == 0:
        return float('inf')
    # (eo/et)/(one/net) -> (eo*net)/(one*et)
    return ((table.exp_out * table.no_exp_tot)
            / (table.out_no_exp * table.exp_tot))


def odds_ratio(table):
    """Return the odds ratio for the given 2-by-2 table"""
    # When all the cells are zero or both numerators are zero the odds
    # are "equal" so the ratio is one
    if ((table.exp_tot == 0 and table.no_exp_tot == 0)
        or (table.exp_out == 0 and table.out_no_exp == 0)
        ):
        return 1.0
    # If the numerator odds are zero, then the ratio cannot get any
    # less, so it is zero
    elif table.exp_tot == 0:
        return 0.0
    # If the denominator odds are zero, then the ratio cannot get any
    # larger, so it is infinity
    elif table.no_exp_tot == 0:
        return float('inf')
    # (eo/eno)/(one/neo) -> (eo*neo)/(eno*one)
    return ((table.exp_out * table.no_exp_out)
            / (table.exp_no_out * table.out_no_exp))


def absolute_risk_difference(table):
    """Return the absolute risk difference for the given 2-by-2 table"""
    # Absolute risk difference: (eo/et)-(one/net)
    # Define the risk as zero if the row totals are zero to avoid
    # division by zero
    risk_exp = ((table.exp_out / table.exp_tot)
                if table.exp_tot > 0
                else 0.0)
    risk_no_exp = ((table.out_no_exp / table.no_exp_tot)
                   if table.no_exp_tot > 0
                   else 0.0)
    # Return the difference of the risks of outcome in the exposed and
    # unexposed
    return risk_exp - risk_no_exp
