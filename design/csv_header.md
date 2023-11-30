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

* [I've been thinking from the beginning] format should be specifiable
  separately from the file and be `cat`-able, e.g., `cat fmt file`, just
  like a binary header

* support column- / field-specific options to allow data that involve
  varying levels of parsing complexity, e.g., Python literals, JSON,
  logs

  * allow data type to determine parsing options

* support specifying as a string on the command line (should work well
  embedded in shell syntax)

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
    existing fields (subsequent lines from table cells with wrapped
    text)

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

  * no identifier & paired dlm necessary.  in that case, final k-v sep
    is terminator.

* minimal fmt hdr

  * `csv-0.0.1::` `csv-0.0.1==` (positional args, all defaults)

  * `csv-0.0.1` (no need for k-v seps unless enclosing arguments)

  * obviously, this can default to current version of library and thus
    be omitted entirely

    * thus, header being just a value implies prefix of `csv-0.0.1:`

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

  * separate by whitespace or commas

    ```
    a b c d
    ``` ```
    a,b,c,d
    ``` ```
    a, b, c, d
    ```

  * every value is a sequence of words (seems more natural than
    requiring some sort of syntax to indicate a sequence, especially
    since a single word of multiple characters could be interpreted as a
    sequence of characters when warranted)

    * next key or newline ends value (this allows ending values without
      structural delimiters)  TODO? semicolon for ending, too?

    * all words accumulate onto last key

      ```
      a: b c d= e f: g h i j=klm
      ```

      this is similar to CLI, except that keys are indicated by a k-v
      sep suffix rather than a `-` or `--` prefix; also no positional
      args

      * what do do about initial words with no key, e.g.,

        ```
        a=( b c d: e f )     # ? `{'a': {None: ['b', 'c'], 'd': ['e', 'f']}}`?
        ``` ```
        a=( b c d e f )      # just list: `{'a': ['b', 'c', 'd', 'e', 'f']}`
        ``` ```
        a=( b: c d: e f )    # just dict: `{'a': {'b': ['c'], 'd': ['e', 'f']}}`
        ```

  * either paired delimiters needed for structure or need to require
    quoting empty strings (first example text below is equivalent to
    second text, not third) (it's possible to interpret like third by
    interpreting subsequent keys as nesting)

    ``` ```
    a: b= c: d          # `{'a': [], 'b': [], 'c': ['d']}`?
                        # `{'a': None, 'b': None, 'c': ['d']}`?
    ``` ```
    a: '' b= '' c: d    # `{'a': [''], 'b': [''], 'c': ['d']}`
    ``` ```
    a:(b=(c: d))        # `{'a': {'b': {'c': ['d']}}}`
    ```

    note the first could be "shortened" (written without whitespace) to

    ```
    a:,b=,c:d
    ```

    or expanded to

    ```
    a : b = c : d
    ```

  * putting this together suggests this tokenizing priority: quotes,
    structure, words

  * syntax is not sensitive to whitespace (whitespace is not relevant to
    syntax except to separate words)

  * the content defines the data structure, not the delimiters
    (structural delimiters shouldn't be necessary except to avoid
    ambiguity)

* alternatives (a sequence where membership matters and not necessarily
  order, so sets?)

  ```
  rs = \r\n | \n\r | \r | \n
  ``` ```
  nl : \r\n / \n\r / \r / \n
  ``` ```
  fs:,/|/;
  ``` ```
  fs=,|'|'|;
  ```

  * this suggests `|` and `/` are actually sequence separators rather
    than paired delimiters, which makes more sense (`\` is escape)

  * first `|` or `/` encountered after first character is separator

    * permit empty trailing elements? yes, à la `,` in Python (this also
      ends up being in analogy to trailing whitespace, which is
      typically allowed and is not an error even though it separates
      items otherwise)

      ```
      fs = /|    # `'fs': {'/'}`
      ``` ```
      fs = |/    # `'fs': {'|'}`

  * are the above strings interpreted as raw or as escaped?: `r'\r\n'`
    vs `'\r\n'`

* escaping: explicit or implicit?  regardless, need way to distinguish
  "raw" and "interpreted" strings.

  `\r\n` `\\r\n` `r'\r\n'` `\'\r\n'`

  * probably ought to default to interpreting escapes as that is the
    most common, especially if trying to avoid quoting words

  * prefix character seems to be common approach (but is always adjoined
    by a quote).  prefix is appropriate as determines how following
    string interpreted.  prefix character should make sense without
    quotes, e.g., `.\rawstri\ng` / `-\rawstri\ng` / `+\rawstri\ng`
    (actually `+`/`-` are bad choices as they are commonly prefix
    characters).  maybe one of `=:` makes more sense but that interacts
    with k-v seps.  the other punctuation that stands out to me is `!`.

    `!\` `!'\'` `!\t` `'!'` `.\` `.\r\n` `..` `.0`

    `~` implies approximation or matching, `?` implies matching, `$`
    implies substitution, `@` implies reference or membership, `#`
    implies comment, other punctuation are commonly operators

* named paired delimiters (structural delimiters)

  `:xyz( )xyz:` `.xyz( )xyz.`

  * parse respecting or ignoring intervening quotes / structure?
    ignoring makes it easier to skip over intervening content but
    introduces mixed parsing modes (`(` opens a structure sensitive to
    intervening content, but `.(` opens a structure insensitive to
    intervening content)

  * empty name is valid, e.g., `.(`

  * name-delimiter pairs do not need to be unique.  e.g., the following
    are valid and complete

    `.(.[.<.{}.>.].).` `.()..()..().`

    (I'm not sure what the semantics are, however.  An empty list?
    None?  Probably none / nothing / nil / null.  The delimiters are
    just delimiters, so, contrary to Python, they don't signify the
    construction of a data structure.)

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

  * round trip (concrete syntax tree)

  * unopened structure

  * on error

  * text encoding


Design (Syntax & Semantics)
---------------------------

* characters

  * key-value separators: `:` | `=`

  * sequence separator: r'\s+' | `,` | `|` | `/`

  * quotes: `'` | `"` | ‘`’

    * named quote (raw content): `.''.` | `."".` | ‘.``.’

    * by analogy, a word that starts with `.` is a raw word

  * structural / paired delimiters: `()` | `[]` | `{}` | `<>`

    * named delimiters: `.().` | `.[].` | `.{}.` | `.<>.`

  * escape: `\`

    removes special meaning of all above characters, plus supports the
    following escape sequences:

    `\a` `\b` `\f` `\n` `\r` `\t` `\v` `\xHH` `\uHHHH` `\UHHHHHHHH`

    any other backslash sequence is left as is.  (I'm not doing octal.)

    (semantics are as for C, Bash, Python, Java, Julia, etc.)

    TODO? support `\<newline>` (for multiline string literals)

* words

  the tokens remaining after splitting by above characters

TODO how write a paragraph of text, e.g., for data / column description?  (like YAML wrapped / preformatted strings)  (interacts with newlines)  (maybe explicit end syntax (;) instead of newline? in addition to newline?)  -> how long do values continue?  as long as possible, but control overall length?  as short as possible but extend length?  as long as possible seems more human: we go until we reach a separator.  how much of a chunk to digest off the top is a separate issue.  document delimiters like YAML? - no, already have named structure which can be used for document delimiters

* have data language (like JSON or YAML) that is separate from use in
  specifying CSV header: Parasol, a rich and simple options language

  * parasol-schema: writing a schema for valid parasol data in parasol

* dictionary that allows repeated keys

  * allows keeping order while assigning to default key (none / nil)

  * options for assigning values to keys: none, first, all

  * represented as list of (key, values) pairs with mapping from key to
    indices of its pairs

TODO? syntax for options on how to interpret a block? (options for semantics of a block) maybe `.asdf(:(accumulate=none) ... )asdf.`  (empty key has special meaning?) postfix?: `.asdf( ... )asdf.:(accumulate=none)` (I would prefer prefix.)  I'm tempted to put options into name, e.g., `.asdf:(accumulate=none)( ... )asdf.`, but that breaks visual balance and makes it harder for other tools to skip.

option to "relax" errors into normal words?  e.g., interpret `.z(` in `.a( .z( )a.` as a normal word rather than an error?  option could be 'unmatched: error / warning / drop / word / handle', and could be paired with option specifying handler.  If so, how recover, exactly?  Re-parse after dropping / treating as word?  Basically, just insert would-be content into surrounding context, like flattening.

if a data language, then text is data, how embed text? (including self and other computer languages)  allow arbitrarily repeated quotes? e.g.,

    ``` ... ```
    ''' ... '''
    "" ... ""
    .python````` ... `````python.

    (also, support weirder identifiers? e.g., `.-----( ... )-----.`)

    * not arbitrarily repeated quotes: must be odd number, or at least
      not 2 in a row, because need to distinguish from empty strings: ''
      / "" / ``.  How interpret larger multiples of 2?  Languages with
      triple-quoted strings suggest divide by 2.  But what if number of
      successive quotes divisible by higher powers of 2, like 4?  Is
      `''''` 2 empty strings next to each other?  (It can't be 1 empty
      string delimited by `''` and `''`, because `''` is not allowed to
      be quotation delimiter.)  Perhaps any even number of successive
      quotes just evaluates to the empty string because recursively
      dividing by 2 results in just a bunch of adjacent empty strings
      which concatenate to the empty string.  Maybe just allow single-
      and triple-quoted strings then, as that can be parsed as a stream.
      Or maybe allow small odd numbers, like 1, 3, 5 or 1, 3, 5, 7, 9.
      Or just have option for controlling limit?  Or just go with 1, 3
      and named quotes?

quotes allow options?  (no; don't want to have to escape initial `:`)

    ```:(lang=python)print('Hello, world!')```

only named quotes allow options?  (yes)

    .```:(lang=python)print('Hello, world!')```.

    more reasonably / idiomatically:

    .```:(lang=python, wrap=pre, indent=strip)
    print('Hello, world!')
    ```.

proposal: "meta-options" / processing directives / ??? can be specified for any named quote / structure, indicated by initial (raw) `:` (whitespace may precede to allow specifying on next line, for example), value is only one object (word / structure)

  * implemented as 2 special keys?  one for "meta-options" and one for
    "positional" arguments

what are "meta-options" even good for?  one good example is how to treat (post-process) a bunch of text: dedenting, re-wrapping vs. pre-formatted, etc.  This allows having different types of text blocks like YAML without needing separate / special syntaxes.  One thing I'm less fond of is changing the accumulation, but this could have legitimate uses and is more OK because it changes the semantics, not the syntax.  (With multi-key dicts, the default accumulation can be converted to any other accumulation anyway, since position is preserved.)

format for matrix / table à la Julia? (meta-option for interpreting newlines as row separators)

separate data language from CSV header; also allow JSON, YAML; API just takes dict with 1 key 'ahsv' (or whatever)
what to call data language? quote-lite data structures (qlds), shell data structures (shds) [no, confusing wrt shell syntax], human-readable data structures, data language?, human-readable data language (hurdle?), quick write data language done without quotes (qwdldwq), quick-write data language without quotes (qwdlwq) "Quiddlewick" -> British "Quiddle'ick", "War'ick", "Ber'ick", etc.
