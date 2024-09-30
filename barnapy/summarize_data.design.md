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


Design from 2024-09-25
----------------------

From "Decomposition" notebook with paisley-like plant cover design in
yellow, red, and black.


### Initial Thoughts ###

* design of general data summarizer with memory constraints -> memory
  only matters if doing 2 passes -> one pass can just be streaming ->
  then (if needed), 2 passes can be 2 streams
  * in a 2-pass situation: prefer to stream columns if possible
* are there 1-pass algorithms for variance, skew, and kurtosis?
* does anything else need more than 1 pass?
  * discretization based on q-tiles, std dev, etc.
* can Parquet be streamed?  (if so, by row?  by col?)
* custom loader to stream SVMLight? -> stream within row (by value)
* stream feeds values to accumulators
* what about n_unique?  hyperloglog?
* flexibility to collect stats by col or by row (matrix or other formats
  might be able to stream cols instead of rows)
* do design, record design, implement minimum sufficient solution by
  approximating goals <- different design for minimal implementation
* flexible enough for n-dimensional histograms?  like for discrete
  factors?


### Design for Minimal Summary Statistics Implementation ###

* goals
  * summary statistics
  * contingency tables (for the given labels, if any)
* have
  * SVMLight data, possibly compressed
    * homogeneously-typed matrix
    * use SciKit loader for now, generalize later
* ignore (for now)
  * memory usage -> assume data fits in memory
  * CSVs -> hence ignore patterns for data types
  * hyperloglog
  * own SVMLight loader that accepts different data types
    * 2 modes: strict & generalized
  * any other format
  * CSV output (just YAML for now)
  * unifying stats for discrete & continuous (just omit inapplicable)
  * contingency tables for continuous–continuous & continuous–discrete
    -> _discretize_!  (lo, ok, hi based on std devs?)
* CLI options
  * input data format (CSV, SVMLight, matrix as CSV (DoK), SQLite,
    DuckDB, ODBC, etc.)  (mime type?  e.g. for compression)
  * stats
    * 1-pass
    * pairwise
    * 2-pass (or more passes)
    * option for 1-pass only (discard incompatible stats)
    * option for individual only (discard pairwise stats)
  * mem target / limit
  * output format(s)
    * specify files with URI syntax?  csv://stdout yaml://stderr
      json:/./stats.json
    * only need to specify format if extension doesn't specify (or
      contrary to extension)
    * probably best to just prepend filename with format name & args &
      colon: `csv(|"e\):stats.csv` <- pretty much need general parsing
      and escaping right away
  * might be algorithm options (e.g. for 1-pass vs 2-pass variance)
  * header (col types)
  * weight column
  * "direction": row-wise / col-wise / cell-wise
* dimensions of statistics
  * passes: {1-pass, 2-pass, 3-or-more passes (etc.)} ×
  * columns: {individual, pairwise, 3-way (etc.)} ×
  * scope/stage: {about file, about data} ×
  * RV type: {discrete, continuous}
* implement
  * accumulators (how connect to avoid redundancy?)
  * feeder: given stream (of rows, cols, whatever), feed accumulators
  * streamer (for in-mem SVMLight) -> streams (row, col, value) (how
    connect with labels(s)?) -> pairwise & higher-order need multiple
    cols at once (entire example?)
  * reporter (individual, pairwise)
  * NO -> assembler? (for pairwise & higher-order) <- NO
    the key is how to stream multiple cols at once (or how to stream
    entire rows at once) -> push down to data format?  declare all
    interactions to streamer up front?
  * problem is how to flexibly do pairs (& higher-order)
    * DB viewpoint
      * discrete: (fields...), count(*) from .. group by (fields...)
      * continuous: product(fields...) (construct features that are the
        product of other features)
    * {row-wise, col-wise} × {discrete, continuous} ?  do all need to be
      implemented separately?
* !!! construction of higher-order features _orthogonal_ to summary
  stats -> need separate generator of higher-order features
* processing flow: data parsing (file format) -> data (type) recognition
  & interpretation & validation -> representation -> cleaning -> feature
  generation -> transformation -> stats, analysis, modeling (although
  modeling could come before transformation e.g. as part of cleaning)
* stats have at least 2 sources: representation (what is in file) &
  transformation (about the data)
* accumulators handle multiple columns simultaneously (if needed) ->
  store array of stats -- e.g. needed for sum / avg but not count
* accumulators have prerequisites / dependencies -- e.g. avg depends on
  sum & count -> how enforce during construction?  require in
  constructor?  look up by name?  construct own deps recursively as
  needed?
* accumulators depends on access / streaming method -> e.g. for random
  access cells "count of rows" needs to store unique row IDs
  * -> stream both cells and rows / cols for files that support?
    (otherwise have to collect full rows / cols before feeding)
* native access patterns
  * rows: CSV, SVMLight, CSV (in mem), row store DBs (and their APIs), C
    arrays
  * cols: CSC (in mem), col store DBs, Fortran / Julia arrays
  * cells: table / matrix in unsorted "DB" (row, col, val)
    representation, SciPy "DoK" sparse
  * (cells can always be iterated within a row / col)
* is cell-wise sufficient?  (I think so, but it's not optimal for some,
  like n_rows.)
* only problem for n_uniq (per column) is continuous or high-cardinality
  discrete (effectively continuous as n elements grows with data size)
  -- anything finite / bounded is probably worth spending memory on ->
  track up to max size & then convert to hyperloglog? -> "n_uniq" (set),
  "n_uniq_approx" (hyperloglog), "n_uniq_adapt" (set / hyper)


-----

Copyright (c) 2024 Aubrey Barnard.  This is free, open software released
under the MIT license.  See `LICENSE` for details.
