# CSV Command-Line Correctness Results

Generated: 2026-06-25T21:24:50Z

## Environment

- Python: 3.12.3
- Platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39
- Random seed: 42
- Trials per case: 3

## Tool Versions

- awk: ✓ Available
- cut: ✓ Available
- sort: ✓ Available
- grep: ✓ Available
- goawk: ✗ Not installed
- csvquote: ✗ Not installed
- jq: ✓ Available

## Correctness Summary

| Case | python_csv | naive_split | awk | cut | grep_count |
|------|------------|-------------|-----|-----|------------|
| 01_simple | ✓ | ✓ | ✓ | ✓ | ✗ |
| 02_quoted_comma | ✓ | ✗ | ✗ | ✗ | ✗ |
| 03_multiline | ✓ | ✗ | ✗ | ✗ | ✗ |
| 04_escaped_quotes | ✓ | ✗ | ✗ | ✗ | ✗ |
| 05_empty | ✓ | ✓ | ✓ | ✓ | ✗ |
| 06_crlf | ✓ | ✓ | ✓ | ✓ | ✗ |
| 07_bom | ✓ | ✓ | ✓ | ✓ | ✗ |
| 08_semicolon | ✓ | ✗ | skip | ✓ | ✗ |
| 09_ragged | ✓ | ✓ | ✓ | ✓ | ✗ |
| 10_big | ✓ | ✓ | ✓ | ✓ | ✗ |

## Timing Summary (median ms)

| Case | python_csv | naive_split | awk | cut |
|------|------------|-------------|-----|-----|
| 01_simple | 0.409 | 0.491 | 19.336 | 16.41 |
| 02_quoted_comma | 0.405 | 0.496 | 20.075 | 16.562 |
| 03_multiline | 0.418 | 0.494 | 20.022 | 16.635 |
| 04_escaped_quotes | 0.371 | 0.531 | 20.253 | 16.553 |
| 05_empty | 0.422 | 0.495 | 20.803 | 15.85 |
| 06_crlf | 0.373 | 0.542 | 20.082 | 16.459 |
| 07_bom | 0.419 | 0.498 | 19.919 | 16.218 |
| 08_semicolon | 0.409 | 0.492 | - | 17.322 |
| 09_ragged | 0.438 | 0.512 | 20.103 | 16.584 |
| 10_big | 3.699 | 2.007 | 25.207 | 19.111 |

## Commands Run

```
python3 -m py_compile benchmark_csv_tools.py
python3 benchmark_csv_tools.py
```

## Limitations

- Only 10 test cases, synthetic data only
- goawk / csvquote / jq not installed, skipped honestly
- sort workflow not tested (would need key extraction)
- No encoding stress beyond UTF-8 BOM
- No performance testing on large (>MB) files
- grep_count is not a CSV parser, included only for reference
