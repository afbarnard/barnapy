CSV Format Header Design
========================


CSV Header that includes Schema
-------------------------------

[From medium red book, p. 70, 2019/05/10.]

* consider CSV like binary format: magic number, version, info on how to
  interpret remaining file

* header intro: "csv", version, delimiter / comment / quoting characters
  / specification -> each may be string (multiple chars)

  * how encode record separator?  first char after intro?

    separators must not be prefixes of one another

  * use balanced punctuation to delimit -> this allows quoting of
    balanced punc as special characters

    () [] {} || <> // \\   -> also support any char like sed

  * while there will be a standard order of args, allow keyword args;
    fill in w/ defaults (style configurable via arg)

  * intro should just be first line to easy for tools to skip

  * interpret backslash escaped & unicode escaped chars: intro needs to
    be able to be written in ASCII if needed

* line after intro (excluding comments) is header (schema) & consists of
  name ":" type pairs in a record, i.e. separated by delimiters &
  terminated w/ a record separator

  * if types not recognized, preserve for application & treat as strings
    in meantime

  * type "any" means "parse as what it looks like"?  "object"?

* for example:                  (assume UTF-8) (allow as arg?)
```
csv-0.0.1:(#)(,)(")(\)
# This file contains ...
# Copyright ...  License ...
id:int, lo:date, hi:date, tbl:str, typ:str, val:any, jsn:json
1,1978-01-03,1980-03-01,dx,544,,,
```

* format args: delimiter, comment, quote, escape, record-separator,
  field-separator           c       q      e        rs  r
     fs   f                                                 others?


Continuing from p. 70 for specifying CSV Format
-----------------------------------------------

[From medium red book, pp. 82-83, 2023/09/27.]

* no quoting needed -> simple parsing, human understanding

* allow both ':' & '=' as key-val separators

* (:) & (=) just return ':' & '=' (empty key & empty val means separator
  is val)

* "magic number": ahxsv, ahsv (cf. ahdb), ahdlm, ahtbl

  * consider as file extension [.ahsv, .asv]

                                       ↙ no WS trimming
* how handle whitespace?  sensitive?  insensitive?  how specify
  whitespace as character?  literally (but then what about newlines?)

* what about options [alternatives], e.g., "\n" | "\r\n" | "\r" | "\n\r"
  etc.

* allow escapes, at least for whitespace?  named entities?

* need to be able to specify pairs of strings.  just extra k-v seps?

* allow for (mostly) arbitrary k-v seps?  (q:':') ~~[q-«-»]~~
  <lt:\n><nl=\r\n>{d,\t}
   rs     r

* multiple values: just repeat options

* allowing escapes good for CLI & other possibly ASCII-only situations
  (also, not actually hard to implement escapes)

* C-style escapes, \x00, \u0000 -> follow a specific language's defs
  (Python, Julia, Rust?)

  * identifier chars (not available as k-v seps): [a-zA-Z0-9_-] . ?

* how end CSV format spec?  repeat initial char(s)?  fixed value?  e.g.,
  ahsv-0.0.1::: .... :::   :( ):   :[ ]:   :< >:   =( )=   ={ }=   =| |=
  :/ /:   =\ \=   (have depend on inner parsing?  or disallow occurrence?)
                                                                   ↑
  disallow occur but allow non-WS chars btw, eg  :---(  ===[  :EOF<
  >FOE: or >EOF:
    ✗       ✓

* WS around key -> trim WS around value

* WS allowed btw. opts

* ~~id chars: [a-zA_Z0-9._-]~~

* k-v seps: [:=]

* paired delimiters: "()[]{}<>||//\\"

* open-dlm:  [([{<|/\]

* close-dlm: [)]}>|/\]

* num chars: [0-9.]

* id chars: [a-zA-Z_-]

                                        ①        ②         ③
* grammar: "ahsv-" <num-char>+ <ws>* <kv-sep> <id-char>* <open-dlm>
                             ③         ②         ①
  (<ws>* <opt>)*? <ws>* <close-dlm> <id-char>* <kv-sep>

  [where ① & ② need to match exactly and ③ needs to match as an
  open–close pair]

* limit entire header to 1024? bytes by default.  controllable by
  option.                      ↘ what is double entire single-char header?

* TODO: column-specific options (quoting, escaping, structure)
                               ↘ append :( ): groups to name:type pairs?

* text-encoding: t, txt

* fields in format header?  (no)

* structure: s,

* syntax mode: fixed width, seps, seps w/ runs, enclosed / structured

* escape mode

* skip lines, bytes, until, up to

* ignore unrecognized opts


Thoughts / Decisions After Above 2 Design Sessions
--------------------------------------------------

* [from the beginning] format should be specifiable separately from the
  file and be `cat`-able, e.g., `cat fmt file`, just like a binary header

* support column- / field-specific options to allow data that involve
  varying levels of parsing complexity, e.g., Python literals, JSON,
  logs

  * allow data type to determine parsing options

* support specifying as a string on the command line

* support arbitrary user-specified properties

* in order to support above

  * quoting inevitable, but provide ways to avoid / minimize it

  * escaping inevitable, ditto

* limit possible extent of parsing by maximum bytes and absolute
  (unquotable, unescapable) start and end tokens

  * allows to pick off top chunk of bytes to process in detail

  * start and end tokens need to be self-describing / configurable for
    flexibility; take cues from shell here documents

  * makes easier for other tools to skip over

  * prevents attacks

* make format configurable enough to support CSVs of all kinds, SQL
  inserts, and various plain text tables

  * supporting plain text tables needs ability to append lines to
    existing fields

* support non-human numbers of fields / columns (e.g., genomics,
  transposed time series)

  * specify options by field index range?  by field name pattern?

* goal: be able to read tables in weird formats as a way of converting
  to more sensible formats (e.g., could be used as preprocessor for DB
  loads when emitting SQL tuples)

* modes of quoting fields: none, enclosed, shell (quotes can start
  anywhere, adjacent strings are concatenated)

* commas as additional k-v sep?  (as a reference to pairs)  or only w/in
  paired delimiters?

* additional design should be done by working out examples


Design by Examples
------------------

* allow start and end tokens to be customized by specifying arbitrary
  identifier, à la shell here documents.  identifier occurs btw k-v sep
  and paired dlm.

  ```
  ahsv-0.0.1:fmt-xyz(
    ...
  )fmt-xyz:
  ```

  * need to absorb any trailing newline

  * no identifier & paired dlm necessary.  in that case, k-v sep is
    terminator.

* minimal fmt hdr

  * `csv-0.0.1::` `csv-0.0.1==` (positional args, all defaults)

  * `csv-0.0.1` (no need for k-v seps unless enclosing arguments)

  * obviously, this can default to current version of library and thus
    be omitted entirely

  * -> empty fmt hdr should be valid fmt hdr

* positional args separated by whitespace à la the shell

  ```
  xsv-0.0.1: , :
  ``` ```
  ahdlm-0.0.1= : (") \ # =
  ``` ```
  csv-0.0.1:|"\#:
  ``` ```
  csv-0.0.0:(:"\):
  ```

  * no whitespace after start token indicates positional arguments from
    byte array (?)

* basic, shell-assignment-like keyword args

  ```
  csv-0.0.0: d=, q=(") e=\ c=# :
  ``` ```
  csv-0.0.0:( d:, q:(") e:\ c:# ):
  ```

* positional args before keyword args

  ```
  ahdb-0.0.0: , (") e=\ c=# :
  ```

  * "raw" string unless quoted?  (is a bare "\" allowed?)

  * when does quoting kick in?  can it be specified?  no.  syntax for
    header is set ahead of time, as for all computer langs.  should be
    straightforward to handle various quoting scenarios given paired
    delimiters act as quoting mechanisms.

  * allow all quoting mechanisms to have escaping?  or escaping only
    within single / double quotes?  i.e., is `(\)` valid?  make
    configurable à la Python raw strings or Bash `''` vs. `$''`?  `\""`
    `\()` `\\""` `\\()` `+()` `:():` (no, conflicts with purpose of
    having 2 chars which is to avoid quoting)

* what are all options?

  ```
  csv-0.0.0:fmt-hdr(
  field-separator: ,  # fs, delimiter, d
  quote: (")  # q, empty means none
  escape: \  # e, empty means none
  quoting-mode: minimal  # qm, quote-style, qs, in {none, minimal, always}
  escaping-mode: escaping  # em, escape-style, es, in {escaping, doubling}
  outer-whitespace: trim  # ow, in {trim, skip, keep}
  skip: 0 lines  # s, e.g., 3 lines | 1024 bytes | until -----
  comment: (#)  # c
  record-separator: \'\r\n|\n\r|\n|\r' # rs
  newline: \'\r\n|\n\r|\n|\r' # nl
  format: unix  # f, flavor, syntax, style, in {excel, unix, names from config?}
  quoting-region: partial  # qr, in {whole, entire, partial}
  structure
  null: ()  # signifiers of missing values
  +null: na
  -null: ''
  blank-line: skip  # bl, in {trim, skip, keep}
  default-value: ()  # could be 0 for things like sparse arrays
  raw from ? until RS:
  pattern FS
  sequence FS
  pattern RS
  fields:
  schema:
  )fmt-hdr:
  ```

  * where can quoted fields start?  only at beginning (after
    whitespace)?  at any position?

  * allow specifying individual options on CLI, e.g. `+n:NA`

  * what to do about case sensitivity?

  * value modifiers?  e.g., raw string, split up value like list / chars
    / words, case sensitivity, data structure type?

    * split on `r',\s*|\s+'`?

  * is there a unifying syntax that works for value modifiers and start
    / end sentinels?  (can entire format header be a key-value pair with
    a compound value?)  `()` vs. `:():` | `:x()x:`?

  * scan / parse modes: raw, named raw (à la shell here document),
    escaped, structured / nested

    * how to safely emit named raw?  have to scan contents and do
      escaping, just as for any safe interpolation

  * distinguish between structure and quoting?  how handle?  yes.
    structure allows nested structure which must be recognized by the
    parser.  quoteds don't need any internal interpretation by the
    parser except escape sequences.

  * all words, quoteds, and structures are raw (no escaping).  prefix
    with `\` to tell the parser to interpret escape sequences.  also,
    strings can have named start and end tokens, same as for structures.

  * allow [?.] in identifiers for namespaces and boolean options.  also
    makes `csv-0.0.1` an identifier.

  * how signal take positional values from a single word / string?  just
    whether value is expected to be a sequence?

  * since everything is strings, adjacency is string concatenation, just
    like shell

* sequences

* alternatives

* format header value is JSON or YAML

* field-specific options (just nesting of dictionaries)

  ```
  csv-0.0.0:fmt-hdr(
  )fmt-hdr:
  ```

* parser options (not format header)

  * how handle irregular record lengths

  * max field size

  * allow newlines in fields

  * max record size

  * round trip

  * unopened structure

  * on error

  * text encoding
