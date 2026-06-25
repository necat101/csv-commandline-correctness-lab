# VERIFY.md – Fresh Clone Verification

This file proves the repository works end-to-end from a clean checkout.

## Clone

```
$ git clone https://github.com/necat101/csv-commandline-correctness-lab.git csv-verify
Cloning into 'csv-verify'...
```

## Compile check

```
$ cd csv-verify
$ python3 -m py_compile benchmark_csv_tools.py
$ echo $?
0
```

**py_compile exit code: 0** – script is syntax-valid.

## Run benchmark

```
$ python3 benchmark_csv_tools.py
CSV Command-Line Correctness Lab
============================================================
  ✓ awk: found
  ✓ cut: found
  ✓ sort: found
  ✓ grep: found
  ✗ goawk: not installed
  ✗ csvquote: not installed
  ✓ jq: found

Generating corpus...
  Generated 10 test cases

Benchmarking 5 workflows across 10 cases...

01_simple: simple clean CSV
  python_csv      ✓ 0.404ms
  naive_split     ✓ 0.498ms
  awk             ✓ 19.419ms
  cut             ✓ 16.407ms
  grep_count      ✗ 16.641ms

02_quoted_comma: quoted comma field
  python_csv      ✓ 0.413ms
  naive_split     ✗ 0.497ms
  awk             ✗ 19.953ms
  cut             ✗ 16.907ms
  grep_count      ✗ 17.828ms

03_multiline: quoted embedded newline
  python_csv      ✓ 0.42ms
  naive_split     ✗ 0.516ms
  awk             ✗ 20.608ms
  cut             ✗ 15.889ms
  grep_count      ✗ 17.87ms

04_escaped_quotes: escaped double quotes
  python_csv      ✓ 0.447ms
  naive_split     ✗ 0.501ms
  awk             ✗ 20.726ms
  cut             ✗ 16.852ms
  grep_count      ✗ 17.784ms

05_empty: empty fields
  python_csv      ✓ 0.419ms
  naive_split     ✓ 0.503ms
  awk             ✓ 20.405ms
  cut             ✓ 16.89ms
  grep_count      ✗ 17.7ms

06_crlf: CRLF line endings
  python_csv      ✓ 0.402ms
  naive_split     ✓ 0.497ms
  awk             ✓ 20.308ms
  cut             ✓ 17.744ms
  grep_count      ✗ 17.583ms

07_bom: UTF-8 BOM
  python_csv      ✓ 0.419ms
  naive_split     ✓ 0.495ms
  awk             ✓ 20.026ms
  cut             ✓ 16.463ms
  grep_count      ✗ 17.41ms

08_semicolon: semicolon-delimited (locale)
  python_csv      ✓ 0.404ms
  naive_split     ✗ 0.491ms
  awk             SKIP  non-comma delimiter
  cut             ✓ 16.698ms SILENT_WRONG
  grep_count      ✗ 17.892ms

09_ragged: ragged rows / malformed
  python_csv      ✓ 0.407ms
  naive_split     ✓ 0.525ms
  awk             ✓ 21.705ms
  cut             ✓ 17.291ms
  grep_count      ✗ 17.633ms

10_big: bigger synthetic file (5000 rows)
  python_csv      ✓ 3.738ms
  naive_split     ✓ 2.007ms
  awk             ✓ 25.207ms
  cut             ✓ 19.111ms
  grep_count      ✗ 18.93ms


Results written to RESULTS.md
Full JSON: results/results.json
```

**Exit code: 0**

## Verification Summary

- ✅ Repository clones successfully from GitHub
- ✅ `python3 -m py_compile benchmark_csv_tools.py` → exit code 0
- ✅ `python3 benchmark_csv_tools.py` → exit code 0
- ✅ Corpus generated: 10 test cases
- ✅ All workflows run: python_csv, naive_split, awk, cut, grep_count
- ✅ RESULTS.md generated with correctness and timing tables
- ✅ results/results.json written (full machine-readable output)

## Environment (verification run)

- Python: 3.12.3
- Platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39
- git: 2.43.0
- awk: GNU Awk 5.2.1
- cut/grep/sort: coreutils 9.4 / grep 3.11
- goawk: not installed (skipped honestly)
- csvquote: not installed (skipped honestly)
- jq: 1.6 (available, not used for CSV)

## Files in repo

```
benchmark_csv_tools.py  14,123 bytes
README.md                7,577 bytes
RESULTS.md               2,012 bytes
.gitignore                  52 bytes
VERIFY.md              (this file)
```

Total: ~24 KB, 4 files + VERIFY.md

No external dependencies beyond Python stdlib + standard Unix tools. No network calls during benchmark. No downloads. Corpus is generated locally with fixed random seed (42).

---

Verified: 2026-06-25T21:53:00Z
Commit: 474fd22f544cf08778a2d6b01f242488daebf562
