"""
Scores and contingency tables / confusion matrices for analyzing the
results of classification or the results of exposures and outcomes
(epidemiology / causal inference).

Part of the point here is to implement the terminology and synonyms to
enable writing self-documenting code and avoid mix-ups.
"""

# Copyright (c) 2024 Aubrey Barnard.
#
# This is free, open software released under the MIT license.  See
# `LICENSE` for details.


import math
from numbers import Real
import typing


##### Tables #####


Table2x2 = typing.ForwardRef('Table2x2')
class Table2x2:
    """
    2-by-2 table for analyzing the results of binary classification or
    exposures and outcomes.

    A "3-by-3" table is just a 2-by-2 table with its row and column
    totals.


    Terminology for 2-by-2 / 3-by-3 Tables
    --------------------------------------

    ## Machine Learning / Classification ##

    ```
              | True / Actual                  |
    Predicted | Positive        Negative       | Total
    --------- + --------------  -------------- + ------------------
    Positive  | true pos  (tp)  false pos (fp) | predicted pos (pp)
    Negative  | false neg (fn)  true neg  (tn) | predicted neg (pn)
    --------- + --------------  -------------- + ------------------
    Total     | total pos (p)   total neg (n)  | all / total   (a)
    ```


    ## Epidemiology / Causal Inference ##

    Typically the exposure precedes the outcome, but see 'TemporalTable2x2'
    below for also tracking exposure after outcome (rather than ignoring it
    or putting it in the outcome-no-exposure bucket).

    ```
    Treatment / | Disease / Outcome    |
    Exposure    | Yes        No        | Total
    ----------- + ---------  --------- + ---------------
    Yes         | yeyo (tp)  yeno (fp) | ye  (pp)
    No          | neyo (fn)  neno (tn) | ne  (pn)
    ----------- + ---------  --------- + ---------------
    Total       | yo   (p)   no   (n)  | all (a)
    ```

    See <https://en.wikipedia.org/wiki/Sensitivity_and_specificity>.
    """

    __slots__ = ('_tp', '_tn', '_fp', '_fn')

    def __init__(self, tp: Real, tn: Real, fp: Real, fn: Real):
        """
        Construct a 2-by-2 table from the given classification result
        numbers.

        The numbers can be integers or floats but are assumed to be
        positive (counts or fractional counts).

        One of the 'from_*' constructors may be more appropriate.
        """
        self._tp = tp
        self._tn = tn
        self._fp = fp
        self._fn = fn

    @staticmethod
    def from_classification_result(
            n_true_positives: Real,
            n_false_positives: Real,
            n_false_negatives: Real,
            n_true_negatives: Real,
    ) -> Table2x2:
        """
        Construct a 2-by-2 table from the given classification result
        numbers, {true, false} × {positive, negative}.
        """
        return Table2x2(tp=n_true_positives, fp=n_false_positives,
                        fn=n_false_negatives, tn=n_true_negatives)

    @staticmethod
    def from_cls(tp: Real, fp: Real, fn: Real, tn: Real) -> Table2x2:
        # Doc string copied below from 'from_classification_result'
        return Table2x2.from_classification_result(
            n_true_positives=tp, n_false_positives=fp,
            n_false_negatives=fn, n_true_negatives=tn)
    from_2x2 = from_cls

    @staticmethod
    def from_3x3_corners(
            n_true_positives: Real,
            n_predicted_positives: Real,
            n_positives: Real,
            n_total: Real,
    ) -> Table2x2:
        """
        Construct a 2-by-2 table from the corners (positives totals) of a
        3-by-3 table.
        """
        fp = n_predicted_positives - n_true_positives
        fn = n_positives - n_true_positives
        tn = n_total - n_positives - n_predicted_positives + n_true_positives
        return Table2x2(tp=n_true_positives, tn=tn, fp=fp, fn=fn)

    @staticmethod
    def from_pppa(tp: Real, pp: Real, p: Real, all: Real) -> Table2x2:
        # Doc string copied below from 'from_3x3_corners'
        return Table2x2.from_3x3_corners(
            n_true_positives=tp,
            n_predicted_positives=pp,
            n_positives=p,
            n_total=all,
        )

    # TODO? from_skl

    @staticmethod
    def from_exposures_outcomes(
            n_exposures_outcomes: Real,
            n_exposures_no_outcomes: Real,
            n_no_exposures_outcomes: Real,
            n_no_exposures_no_outcomes: Real,
    ) -> Table2x2:
        """
        Construct a 2-by-2 table from the given numbers of exposures and
        outcomes.

        Uses the mapping:

            n_exposures_outcomes       -> true positive
            n_exposures_no_outcomes    -> false positive
            n_no_exposures_outcomes    -> false negative
            n_no_exposures_no_outcomes -> true negative
        """
        return Table2x2(
            tp=n_exposures_outcomes,
            tn=n_no_exposures_no_outcomes,
            fp=n_exposures_no_outcomes,
            fn=n_no_exposures_outcomes,
        )

    @staticmethod
    def from_eos(
            yeyo: Real, yeno: Real, neyo: Real, neno: Real,
    ) -> Table2x2:
        """
        Construct a 2-by-2 table from the given numbers of exposures and
        outcomes.

        Uses the mapping:

            yeyo -> n_exposures_outcomes       -> true positive
            yeno -> n_exposures_no_outcomes    -> false positive
            neyo -> n_no_exposures_outcomes    -> false negative
            neno -> n_no_exposures_no_outcomes -> true negative
        """
        return Table2x2.from_exposures_outcomes(
            n_exposures_outcomes=yeyo,
            n_exposures_no_outcomes=yeno,
            n_no_exposures_outcomes=neyo,
            n_no_exposures_no_outcomes=neno,
        )

    @property
    def n_true_positives(self) -> Real:
        """Number of true postives."""
        return self._tp
    tp = n_true_positives

    @property
    def n_true_negatives(self) -> Real:
        """Number of true negatives."""
        return self._tn
    tn = n_true_negatives

    @property
    def n_false_positives(self) -> Real:
        """Number of false positives."""
        return self._fp
    fp = n_false_positives

    @property
    def n_false_negatives(self) -> Real:
        """Number of false negatives."""
        return self._fn
    fn = n_false_negatives

    @property
    def n_positives(self) -> Real:
        """Number of labeled positives."""
        return self.tp + self.fn
    p = n_positives

    @property
    def n_negatives(self) -> Real:
        """Number of labeled negatives."""
        return self.fp + self.tn
    n = n_negatives

    @property
    def n_predicted_positives(self) -> Real:
        """Number of predicted positives."""
        return self.tp + self.fp
    pp = n_predicted_positives

    @property
    def n_predicted_negatives(self) -> Real:
        """Number of predicted negatives."""
        return self.fn + self.tn
    pn = n_predicted_negatives

    @property
    def n_total(self) -> Real:
        """Total number of things classified."""
        return self.tp + self.tn + self.fp + self.fn
    all = n_total

    @property
    def n_exposures_outcomes(self) -> Real:
        """Number of subjects having the exposure and the outcome."""
        return self.tp
    yeyo = n_exposures_outcomes

    @property
    def n_no_exposures_no_outcomes(self) -> Real:
        """Number of subjects having neither the exposure nor the outcome."""
        return self.tn
    neno = n_no_exposures_no_outcomes

    @property
    def n_exposures_no_outcomes(self) -> Real:
        """Number of subjects having the exposure but not the outcome."""
        return self.fp
    yeno = n_exposures_no_outcomes

    @property
    def n_no_exposures_outcomes(self) -> Real:
        """Number of subjects having the outcome but not the exposure."""
        return self.fn
    neyo = n_no_exposures_outcomes

    @property
    def n_exposures(self) -> Real:
        """Number of subjects having the exposure."""
        return self.pp
    ye = n_exposures

    @property
    def n_no_exposures(self) -> Real:
        """Number of subjects not having the exposure."""
        return self.pn
    ne = n_no_exposures

    @property
    def n_outcomes(self) -> Real:
        """Number of subjects having the outcome."""
        return self.p
    yo = n_outcomes

    @property
    def n_no_outcomes(self) -> Real:
        """Number of subjects not having the outcome."""
        return self.n
    no = n_no_outcomes

    def __repr__(self) -> str:
        return '{}(tp={}, fp={}, fn={}, tn={})'.format(
            self.__class__.__name__, self.tp, self.fp, self.fn, self.tn)

    def __eq__(self, other) -> bool:
        return (isinstance(other, Table2x2) and
                self.tp == other.tp and
                self.tn == other.tn and
                self.fp == other.fp and
                self.fn == other.fn)

    def __hash__(self) -> int:
        return hash((self.tp, self.tn, self.fp, self.fn))

    def __neg__(self) -> Table2x2:
        return Table2x2(tp=-self.tp, tn=-self.tn, fp=-self.fp, fn=-self.fn)

    def __add__(self, other) -> Table2x2:
        return Table2x2(
            tp=self.tp + other.tp,
            tn=self.tn + other.tn,
            fp=self.fp + other.fp,
            fn=self.fn + other.fn,
        )

    def __sub__(self, other) -> Table2x2:
        return Table2x2(
            tp=self.tp - other.tp,
            tn=self.tn - other.tn,
            fp=self.fp - other.fp,
            fn=self.fn - other.fn,
        )

    def smoothed(self, pseudocount: Real=1) -> Table2x2:
        """
        Return a smoothed version of this table by adding the given
        pseudocount to each of the four cells.

        The pseudocount may be fractional.

        (If you want to have a separate pseudocount for each count, just
        put the pseudocounts in a separate 'Table2x2' and add it to this
        one.)
        """
        pc = pseudocount
        return Table2x2(tp=self.tp + pc, tn=self.tn + pc,
                        fp=self.fp + pc, fn=self.fn + pc)

    def tuple_2x2(self) -> tuple:
        """
        Represent the contents of this table as a ((tp, fp), (fn, tn))
        tuple.
        """
        return ((self.tp, self.fp),
                (self.fn, self.tn))

    @staticmethod
    def from_tuple_2x2(tuple_2x2: tuple) -> Table2x2:
        """
        Construct a 2-by-2 table from the given ((tp, fp), (fn, tn)) tuple.
        """
        ((tp, fp), (fn, tn)) = tuple_2x2
        return Table2x2(tp=tp, tn=tn, fp=fp, fn=fn)

    def tuple_3x3(self) -> tuple:
        """
        Represent the contents of this table as a ((tp, fp, pp), (fn, tn,
        pn), (p, n, all)) tuple.
        """
        return ((self.tp, self.fp, self.pp),
                (self.fn, self.tn, self.pn),
                (self.p, self.n, self.all))

    @staticmethod
    def from_tuple_3x3(tuple_3x3: tuple) -> tuple:
        """
        Construct a 2-by-2 table from the given ((tp, fp, pp), (fn, tn, pn),
        (p, n, all)) tuple.
        """
        ((tp, fp, pp), (fn, tn, pn), (p, n, all)) = tuple_3x3
        return Table2x2(tp=tp, tn=tn, fp=fp, fn=fn)

    # Scores

    def true_positive_rate(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'true_positive_rate'
        return true_positive_rate(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)
    recall = true_positive_rate
    sensitivity = true_positive_rate
    tpr = true_positive_rate

    def true_negative_rate(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'true_negative_rate'
        return true_negative_rate(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)
    specificity = true_negative_rate
    tnr = true_negative_rate

    def false_positive_rate(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'false_positive_rate'
        return false_positive_rate(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)
    fpr = false_positive_rate

    def false_negative_rate(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'false_negative_rate'
        return false_negative_rate(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)
    fnr = false_negative_rate

    def positive_predictive_value(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'positive_predictive_value'
        return positive_predictive_value(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)
    precision = positive_predictive_value
    ppv = positive_predictive_value

    def negative_predictive_value(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'negative_predictive_value'
        return negative_predictive_value(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)
    npv = negative_predictive_value

    def false_discovery_rate(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'false_discovery_rate'
        return false_discovery_rate(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)
    fdr = false_discovery_rate

    def false_omission_rate(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'false_omission_rate'
        return false_omission_rate(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

    def accuracy(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'accuracy'
        return accuracy(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

    def balanced_accuracy(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'balanced_accuracy'
        return balanced_accuracy(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

    def f_beta(self, beta: Real=1, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'f_beta'
        return f_beta(tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn,
                      beta=beta, default=default)

    def f1(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'f1'
        return f1(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

    def mutual_information(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'binary_mutual_information'
        return binary_mutual_information(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

    def relative_risk(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'relative_risk'
        return relative_risk(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

    def odds_ratio(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'odds_ratio'
        return odds_ratio(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

    def absolute_risk_difference(self, default: Real=float('nan')) -> Real:
        # Doc string copied below from 'absolute_risk_difference'
        return absolute_risk_difference(
            tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn, default=default)

# Copy doc strings
Table2x2.from_cls.__doc__ = Table2x2.from_classification_result.__doc__
Table2x2.from_pppa.__doc__ = Table2x2.from_3x3_corners.__doc__


class TemporalTable2x2(Table2x2): # TODO
    """Not yet implemented."""


##### Scores #####


 #### TPR / TNR / FPR / FNR ####


def true_positive_rate(tp: Real, fp: Real, fn: Real, tn: Real,
                       default: Real=float('nan')) -> Real:
    """
    Calculate the true positive rate (recall, sensitivity) (tp / p) of
    the given 2-by-2 table.

    Return 'default' if the total number of positives (p) is zero.
    """
    n_pos = tp + fn
    return tp / n_pos if n_pos != 0 else default
recall = true_positive_rate
sensitivity = true_positive_rate
Table2x2.true_positive_rate.__doc__ = true_positive_rate.__doc__


def true_negative_rate(tp: Real, fp: Real, fn: Real, tn: Real,
                       default: Real=float('nan')) -> Real:
    """
    Calculate the true negative rate (specificity) (tn / n) of the given
    2-by-2 table.

    Return 'default' if the total number of negatives (n) is zero.
    """
    n_neg = fp + tn
    return tn / n_neg if n_neg != 0 else default
specificity = true_negative_rate
Table2x2.true_negative_rate.__doc__ = true_negative_rate.__doc__


def false_positive_rate(tp: Real, fp: Real, fn: Real, tn: Real,
                        default: Real=float('nan')) -> Real:
    """
    Calculate the false positive rate (type 1 error) (fp / n) of the
    given 2-by-2 table.

    Return 'default' if the total number of negatives (n) is zero.
    """
    n_neg = fp + tn
    return fp / n_neg if n_neg != 0 else default
Table2x2.false_positive_rate.__doc__ = false_positive_rate.__doc__


def false_negative_rate(tp: Real, fp: Real, fn: Real, tn: Real,
                        default: Real=float('nan')) -> Real:
    """
    Calculate the false negative rate (type 2 error) (fn / p) of the
    given 2-by-2 table.

    Return 'default' if the total number of positives (p) is zero.
    """
    n_pos = tp + fn
    return fn / n_pos if n_pos != 0 else default
Table2x2.false_negative_rate.__doc__ = false_negative_rate.__doc__


 #### PPV / NPV / FDR ####


def positive_predictive_value(tp: Real, fp: Real, fn: Real, tn: Real,
                              default: Real=float('nan')) -> Real:
    """
    Calculate the positive predictive value (precision) (tp / pp) of the
    given 2-by-2 table.

    Return 'default' if the total number of predicted positives (pp) is
    zero.  Probably the best default here is the fraction of examples
    labeled positive (because that's the random result for precision),
    but you'll have to calculate that yourself.
    """
    n_pp = tp + fp
    return tp / n_pp if n_pp != 0 else default
precision = positive_predictive_value
Table2x2.positive_predictive_value.__doc__ = positive_predictive_value.__doc__


def negative_predictive_value(tp: Real, fp: Real, fn: Real, tn: Real,
                              default: Real=float('nan')) -> Real:
    """
    Calculate the negative predictive value (tn / pn) of the given
    2-by-2 table.

    Return 'default' if the total number of predicted negatives (pn) is
    zero.
    """
    n_pn = tn + fn
    return tn / n_pn if n_pn != 0 else default
Table2x2.negative_predictive_value.__doc__ = negative_predictive_value.__doc__


def false_discovery_rate(tp: Real, fp: Real, fn: Real, tn: Real,
                         default: Real=float('nan')) -> Real:
    """
    Calculate the false discovery rate (fp / pp) of the given 2-by-2
    table.

    Return 'default' if the total number of predicted positives (pp) is
    zero.
    """
    n_pp = tp + fp
    return fp / n_pp if n_pp != 0 else default
Table2x2.false_discovery_rate.__doc__ = false_discovery_rate.__doc__


def false_omission_rate(tp: Real, fp: Real, fn: Real, tn: Real,
                        default: Real=float('nan')) -> Real:
    """
    Calculate the false omission rate (fn / pn) of the given 2-by-2
    table.

    Return 'default' if the total number of predicted negatives (pn) is
    zero.
    """
    n_pn = tn + fn
    return fn / n_pn if n_pn != 0 else default
Table2x2.false_omission_rate.__doc__ = false_omission_rate.__doc__


 #### ACC / F1 / MI ####


def accuracy(tp: Real, fp: Real, fn: Real, tn: Real,
             default: Real=float('nan')) -> Real:
    """
    Calculate the accuracy ((tp + tn) / all) of the given 2-by-2 table.

    Return 'default' if the total number of examples (all) is zero.
    """
    total = tp + fp + fn + tn
    return (tp + tn) / total if total != 0 else default
Table2x2.accuracy.__doc__ = accuracy.__doc__


def balanced_accuracy(tp: Real, fp: Real, fn: Real, tn: Real,
                      default: Real=float('nan')) -> Real:
    """
    Calculate the balanced accuracy ((tpr + tnr) / 2) of the given
    2-by-2 table.

    Return 'default' if the total number of examples is zero.
    """
    total = tp + fp + fn + tn
    if total == 0:
        return default
    tpr = true_positive_rate(tp=tp, fp=fp, fn=fn, tn=tn, default=default)
    tnr = true_negative_rate(tp=tp, fp=fp, fn=fn, tn=tn, default=default)
    return (tpr + tnr) / 2
Table2x2.balanced_accuracy.__doc__ = balanced_accuracy.__doc__


def f_beta(tp: Real, fp: Real, fn: Real, tn: Real,
           beta: Real=1, default: Real=float('nan')) -> Real:
    """
    Calculate the general Fβ score of the given 2-by-2 table.

    The general Fβ score weights recall β times as important as
    precision.

    Return 'default' if the total number of positives, both predicted
    and true, is zero.
    """
    n_p = tp + fn + fp
    if n_p == 0:
        return default
    beta_sqrd = beta * beta
    tp_term = (1 + beta_sqrd) * tp
    return tp_term / (tp_term + beta_sqrd * fn + fp)
Table2x2.f_beta.__doc__ = f_beta.__doc__


def f1(tp: Real, fp: Real, fn: Real, tn: Real,
       default: Real=float('nan')) -> Real:
    """
    Calculate the F1 score of the given 2-by-2 table.

    The F1 score is the harmonic mean of precision and recall.

    Return 'default' if the total number of positives, both predicted
    and true, is zero.
    """
    return f_beta(tp=tp, fp=fp, fn=fn, tn=tn, beta=1, default=default)
Table2x2.f1.__doc__ = f1.__doc__


def binary_mutual_information(tp: Real, fp: Real, fn: Real, tn: Real,
                              default: Real=float('nan')) -> Real:
    """
    Return the mutual information between the binary variables in the
    given 2-by-2 table.

    Return 'default' if the total number is zero.
    """
    # Totals
    ye = tp + fp
    ne = fn + tn
    yo = tp + fn
    no = fp + tn
    all = tp + fp + fn + tn
    # Shortcut / Special-Case the zero distribution
    if all == 0:
        return default
    # Do the calculation in a way that handles zeros.  (If the numerator
    # in the log is greater than zero, the denominator cannot be zero.)
    mi_sum = 0.0
    if tp > 0:
        mi_sum += tp * math.log((tp * all) / (ye * yo))
    if fp > 0:
        mi_sum += fp * math.log((fp * all) / (ye * no))
    if fn > 0:
        mi_sum += fn * math.log((fn * all) / (yo * ne))
    if tn > 0:
        mi_sum += tn * math.log((tn * all) / (no * ne))
    return mi_sum / all
Table2x2.mutual_information.__doc__ = binary_mutual_information.__doc__


 #### Epidemiological ####


def relative_risk(tp: Real, fp: Real, fn: Real, tn: Real,
                  default: Real=float('nan')) -> Real:
    """
    Return the relative risk (yeyo / ye) / (neyo / ne) for the given
    2-by-2 table.

    Return 'default' if the total number is zero.
    """
    # Totals
    all = tp + fp + fn + tn
    # Shortcut / Special-Case the zero distribution
    if all == 0:
        return default
    # When both numerators are zero the rates are "equal" so the
    # relative risk is one
    if tp == 0 and fn == 0:
        return 1
    # If the numerator rate is zero, then the relative risk cannot get
    # any less, so it is also zero
    elif tp == 0:
        return 0
    # If the denominator rate is zero, then the relative risk cannot get
    # any larger, so it is infinity
    elif fn == 0:
        return float('inf')
    # (yeyo/ye)/(neyo/ne) -> (yeyo*ne)/(neyo*ye)
    return (tp * (fn + tn)) / (fn * (tp + fp))


def odds_ratio(tp: Real, fp: Real, fn: Real, tn: Real,
               default: Real=float('nan')) -> Real:
    """
    Return the odds ratio (yeyo / yeno) / (neyo / neno) for the given
    2-by-2 table.

    Return 'default' if the total number is zero.
    """
    # Totals
    all = tp + fp + fn + tn
    # Shortcut / Special-Case the zero distribution
    if all == 0:
        return default
    # When both numerators are zero the odds are "equal" so the ratio is
    # one
    if tp == 0 and fn == 0:
        return 1
    # If the numerator odds are zero, then the ratio cannot get any
    # less, so it is zero
    elif tp == 0:
        return 0
    # If the denominator odds are zero, then the ratio cannot get any
    # larger, so it is infinity
    elif fn == 0:
        return float('inf')
    # (yeyo/yeno)/(neyo/neno) -> (yeyo*neno)/(yeno*neyo)
    return (tp * tn) / (fp * fn)


def absolute_risk_difference(tp: Real, fp: Real, fn: Real, tn: Real,
                             default: Real=float('nan')) -> Real:
    """
    Return the absolute risk difference (yeyo / ye) - (neyo / ne) for
    the given 2-by-2 table.

    Return 'default' if the total number is zero.
    """
    # Totals
    all = tp + fp + fn + tn
    # Shortcut / Special-Case the zero distribution
    if all == 0:
        return default
    # Define the risk as zero if the numerators are zero to avoid
    # division by zero
    risk_ye = tp / (tp + fp) if tp > 0 else 0
    risk_ne = fn / (fn + tn) if fn > 0 else 0
    # Return the difference of the risks of outcome in the exposed and
    # unexposed
    return risk_ye - risk_ne


##### Hypothesis Tests #####


class _HypothesisTests2x2: # TODO?
    pass


'''
TODO:
p-value from g-test, Fisher's exact?
risk_in_exposed
risk_in_unexposed
'''
