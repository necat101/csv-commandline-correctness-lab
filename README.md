# CSV Command-Line Correctness Lab

A local benchmark testing when naive `awk -F,` / `cut -d,` CSV processing works, and when it silently produces garbage.

Inspired by [HN discussion: "Using command line to process CSV files"](https://news.ycombinator.com/item?id=36501364) on [muhammadraza.me/2022/data-oneliners](https://muhammadraza.me/2022/data-oneliners/).

## What HN Users Were Debating

### 1. "awk -F," looks right, fails silently on real CSV

The linked article shows handy one-liners like:

```bash
awk -F, '{print $2}' file.csv
cut -d, -f2 file.csv
```

**HN top comment** (Ben Hoyt, author of GoAWK):

> Unfortunately "awk -F," doesn't work with most real CSV files, because of quoted fields, commas in fields, and (less frequently) multiline fields.

Classic Unix text tools work great on simple delimited text. CSV just isn't simple delimited text.

### 2. Silent wrong output is worse than a loud failure

> And because often also the error handling is incomplete it might be difficult to know that the pipeline is producing garbage output.

From the tool's point of view, there is no error:
> You ask awk to split on commas and give you the second field, it splits on commas and gives you the second field … There were no errors to speak of from what it could see. The "error" is an error in the overall logic of the code.

This lab tracks silent wrong answers explicitly.

### 3. "Just avoid quotes when generating CSV"

One HN commenter:

> I make and process csvs a lot, and just avoid quotes when generating them.

Reply:

> Yeah, I guess that kinda works if you're the one generating them. But … a name field containing "Smith, John" …?

If you control end-to-end generation, simple splitting works. If you don't, use a real parser.

### 4. Locale separators, BOMs, encodings

> Also localized csv files in a language where the comma is the decimal separator (and the field separator is ;), column headers and unexpected character encodings. CSV is truly the worst.

This lab includes a semicolon-delimited test case and UTF-8 BOM handling.

### 5. CSV is deceptively hard to parse correctly

> CSV is deceptive in that it looks like it parses easily, but the truth is CSV is one of the most difficult formats to reliably parse. I mean, just look at the number of arguments that pandas.read_csv has.

> Parsing a CSV by hand is almost always the wrong thing to do unless you also wrote the CSV generating process and can limit the variance.

The recommended approach from multiple HN commenters: farm CSV parsing out to a battle-tested engine (DuckDB, sqlite, pandas, polars, clickhouse-local) and work with the parsed object.

### 6. Tools that actually handle CSV

HN-recommended CSV-aware tools:
- **csvkit** – `csvsql`, `csvcut`, `csvgrep` – SQL on CSVs
- **DuckDB** – `duckdb -c "select … from 'file.csv'"`
- **csvquote** – [dbro/csvquote](https://github.com/dbro/csvquote) – makes CSV safe for awk/cut/sed: `csvquote file.csv | awk -F, '…' | csvquote -u`
- **GoAWK** – `goawk -i csv` – CSV-aware awk
- **Miller** – supports ASCII record separators
- **Visidata** – TUI table viewer/editor
- **dsq** – SQL on CSV/JSON/Parquet
- **pawk** – awk-like but parses CSV/JSON/YAML/TOML/Parquet

### 7. Python csv is not "fancy", it's the boring correct baseline

For quick scripts:

```python
import csv
with open('file.csv', newline='') as f:
    for row in csv.reader(f):
        print(row[1])
```

That's it. No dependencies, handles quotes, newlines, escapes, BOMs. Boring, correct.

## What's in This Lab

### Test Cases (10)

1. **simple** – clean CSV, naive splitting should work
2. **quoted_comma** – `"Smith, Bob"` – naive split fails
3. **multiline** – quoted embedded newline – naive split fails
4. **escaped_quotes** – `"He said ""hi"""` – naive split fails
5. **empty** – empty fields – should still work
6. **crlf** – CRLF line endings
7. **bom** – UTF-8 BOM prefix
8. **semicolon** – `;` delimiter, locale-style – naive comma split fails
9. **ragged** – malformed, inconsistent column counts
10. **big** – 5000 rows, simple timing

Each case includes ground truth JSON: expected row count, column count, selected field values, validity flag, delimiter, and whether naive splitting is expected to fail.

### Workflows Tested

- ✅ **python_csv** – Python `csv` module, correctness baseline
- ✅ **naive_split** – `line.split(",")`, shows where it breaks
- ✅ **awk** – `awk -F, 'NR>1 {print $N}'` – if installed
- ✅ **cut** – `tail -n +2 file | cut -d, -fN` – if installed
- ✅ **grep_count** – `grep -c .` – NOT a CSV parser, reference only
- ❌ **goawk** – not installed, skipped honestly
- ❌ **csvquote** – not installed, skipped honestly
- ❌ **jq** – available but not used (JSON tool, not CSV)

### Correctness Validation

For every case/workflow:
- Did it produce expected field values?
- Did it get the expected row count?
- Did it silently return wrong answers?
- Did it fail loudly (non-zero exit)?
- Was the case supposed to be supported?

A fast workflow that returns garbage is scored as **FAILED**.

### Timing

3 trials per case/workflow, `time.perf_counter()`, reports mean/median/stdev/min/max.

## Running the Lab

```bash
python3 -m py_compile benchmark_csv_tools.py
python3 benchmark_csv_tools.py
cat RESULTS.md
```

## Results (Linux, Python 3.12.3)

| Case | python_csv | naive_split | awk | cut |
|------|------------|-------------|-----|-----|
| simple | ✓ | ✓ | ✓ | ✓ |
| quoted_comma | ✓ | ✗ | ✗ | ✗ |
| multiline | ✓ | ✗ | ✗ | ✗ |
| escaped_quotes | ✓ | ✗ | ✗ | ✗ |
| empty | ✓ | ✓ | ✓ | ✓ |
| crlf | ✓ | ✓ | ✓ | ✓ |
| bom | ✓ | ✓ | ✓ | ✓ |
| semicolon | ✓ | ✗ | skip | ✓ silent_wrong |
| ragged | ✓ | ✓ | ✓ | ✓ |
| big (5000 rows) | ✓ | ✓ | ✓ | ✓ |

**Key finding**: awk/cut fail silently on quoted commas, multiline fields, and escaped quotes – exactly as HN warned. The `cut` tool on semicolon-delimited input with comma-split returns the wrong column silently (flagged as `SILENT_WRONG`).

**Timing**: Python csv ~0.4ms per small file, naive_split ~0.5ms, awk ~20ms (process startup dominates), cut ~16ms. On 5000 rows: python_csv 3.7ms, naive 2.0ms, awk 25ms, cut 19ms. Correctness matters more than microseconds.

## Tool Availability

| Tool | Status |
|------|--------|
| python csv | ✓ stdlib |
| awk | ✓ GNU Awk 5.2.1 |
| cut | ✓ coreutils 9.4 |
| sort | ✓ coreutils 9.4 |
| grep | ✓ 3.11 |
| goawk | ✗ not installed |
| csvquote | ✗ not installed |
| jq | ✓ 1.6 (not used for CSV) |

## Takeaway

Command-line tools are great for simple delimited text. CSV is deceptively tricky. Quoted commas and multiline fields break naive `awk -F,` / `cut -d,`. Silent wrong output is worse than a loud failure.

Python's `csv` module is not "fancy" – it's the boring correct baseline. Use it. Or DuckDB, csvkit, Miller, Visidata, whatever – just use something that actually parses CSV.

The best workflow depends on whether you control the input. If you generate the CSV and can guarantee no quotes/commas/newlines in fields, `awk -F,` is fine. If you're processing CSV from the outside world, use a real parser.

---

**Inspired by**: [HN #36501364](https://news.ycombinator.com/item?id=36501364) · [data-oneliners](https://muhammadraza.me/2022/data-oneliners/) · [goawk-csv](https://benhoyt.com/writings/goawk-csv/) · [csvquote](https://github.com/dbro/csvquote) · [RFC 4180](https://www.rfc-editor.org/rfc/rfc4180)
