Design
======

This aims to be a library that supports summarizing raw tabular data
that is larger than memory (or is otherwise unwieldy like having many
columns) plus a script to do so.  In addition to typical summary
statistics for numerical data, the goal is to provide information that
is useful during initial data exploration for a variety of data types,
that is, before you even know if there are numbers to compute summary
statistics on.


Thoughts
--------

* goals
  * support data larger than memory
  * support "wide" data
  * data summary / analysis by column
  * assumes readable tabular format (whose values might all be
    unconverted text) (à la CSV)
* one-pass mode (for streams)
  * invokes only statistics that can be computed in one pass
* constant- or low-memory mode (for large data)
  * invokes only statistics that take constant or low (e.g., k, log(n))
    memory per statistic
* mode determined by statistics requested
  * except CLI options to select statistics by performance
    characteristics
* ability to chunk columns (to save on memory for things like order
  statistics)
  * outer loop over chunks of columns, inner loop over data "rows"
  * complete statistics for chunk of columns before moving on, even if
    means making multiple passes over those columns
* ability to make multiple passes (for those underlying data formats
  that support it)
  * necessary for statistics that need multiple passes like standard
    deviation
* abstract collecting statistics with "accumulators"
  * one accumulator object could calculate several related statistics to
    save work (calls to accumulate) (still need a way of only
    accumulating requested statistics)
  * ? could accumulators depend on one another? e.g., many would need a
    count of data points
  * pass accumulator row index and value (so accumulator can distinguish
    equal values by position if needed)
  * accumulators have attributes so that they can automatically be
    sorted by performance criteria (n passes (computation), amount of
    memory (maximum total)); either criterion could possibly depend on:
    user-specified k (e.g., top-k), data-dependent u (u < n) (e.g., n
    unique values), or data size n)
* abstract underlying data formats
  * source of bytes can be either file or stream (seekable (file),
    repeatable (command with piped IO), or not)
  * iterate over rows from a selection of columns
  * CSV
  * SvmLight
  * other?
* output / report
  * in multiple formats, e.g., CSV, YAML
  * CSV: one row per column of data
    * need to be able to output structured summaries, such as top-k, as
      individual fields
  * YAML: one document per column of data
    * structured summaries ok as is
  * statistics reported in CLI order (so as to customize CSV column
    order, for example) (as enabled by CLI option?)
  * emitted incrementally (as possible)
  * allow for customized statistics names in output (and in CLI args?)
    (according to a provided map from standard (descriptive) names to
    output (e.g., abbreviated) names; map can be provided in YAML-syntax
    string or file); default identity map of standard names, overridden
    by map of standard names to abbreviations (if allowed by CLI flag),
    overridden by user-provided map of standard names to abbreviations
    (if any)
* cli
  * specify columns to summarize by name or number (defaults to all)
  * specify stratification column(s) (defaults to none)
* previous ideas on API
  * input: NumPy / SciPy matrix, column index, list of column indices to
    stratify by, list of keys for what to report, params for individual
    calculations
  * output: report on specified column (mapping of names to statistics)
* include contingency tables and contingency table statistics (accuracy,
  PPV)


YAML Report Idea
----------------

```
---
id: <column-id>
nm: <column-name>
values:
  n_vals:
  n_uniq:  # n_vals == n_uniq + n_rpts n_dups?
  n_rpts:  # n_nunq? n_nonu?
  n_muls:  # n values that have freq >= 2, n_rptd
  p_uniq:  # high p_uniq => continuous
  n_topk: {x: n, x: n, x: n, x: n, x: n}  # top density if continuous? with rounded density * n instead of count; what is window? 5%? 10%? adaptive?; how handle ends? discount according to how end falls in window?; maybe tails should just decay, like histogram?
  n_true:
  n_nzro:
types:
  n_nil:
  n_int:
  n_ifl:
  n_flt:
  n_nan:
  n_inf:
  n_str:
  n_dtm:
  n_bln:
  n_oth:
stats:
  min:
  max:
  7ns:
  avg:
  sdv:
  skw:
  krt:
  normalness?
  histogram?
strata:
  lbl=0:
    values:
    stats:
  lbl=1:
    values:
    stats:
contingency table:
...
```


-----

Copyright (c) 2024 Aubrey Barnard.  This is free, open software released
under the MIT license.  See `LICENSE` for details.
