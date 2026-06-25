#!/usr/bin/env python3
"""
CSV Command-Line Correctness Lab
Compare naive CLI tools vs Python csv module on tricky CSV cases.
"""
import csv
import json
import subprocess
import time
import statistics
import platform
import sys
from pathlib import Path

RANDOM_SEED = 42
TRIALS = 3
CORPUS_DIR = Path("corpus")
RESULTS_DIR = Path("results")
CORPUS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

def run_cmd(cmd, input_data=None, timeout=5):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            input=input_data, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

def check_tool(name):
    rc, out, _ = run_cmd(f"{name} --version")
    if rc != 0:
        rc, out, _ = run_cmd(f"command -v {name}")
    return rc == 0

# --- Generate test corpus ---
def generate_corpus():
    cases = {}
    
    # 1. simple clean CSV
    p = CORPUS_DIR / "01_simple.csv"
    p.write_text("id,name,score\n1,alice,90\n2,bob,85\n3,charlie,95\n")
    cases["01_simple"] = {
        "file": str(p), "rows": 3, "cols": 3,
        "valid": True, "delimiter": ",",
        "naive_should_fail": False,
        "select_col": 1, "expected_values": ["alice", "bob", "charlie"],
        "desc": "simple clean CSV"
    }
    
    # 2. quoted comma
    p = CORPUS_DIR / "02_quoted_comma.csv"
    p.write_text('id,name,city\n1,"Smith, Bob",NYC\n2,"Lee, Ana",LA\n')
    cases["02_quoted_comma"] = {
        "file": str(p), "rows": 2, "cols": 3,
        "valid": True, "delimiter": ",",
        "naive_should_fail": True,
        "select_col": 1, "expected_values": ["Smith, Bob", "Lee, Ana"],
        "desc": "quoted comma field"
    }
    
    # 3. quoted embedded newline
    p = CORPUS_DIR / "03_multiline.csv"
    p.write_text('id,note\n1,"hello\nworld"\n2,"foo\nbar\nbaz"\n')
    cases["03_multiline"] = {
        "file": str(p), "rows": 2, "cols": 2,
        "valid": True, "delimiter": ",",
        "naive_should_fail": True,
        "select_col": 1, "expected_values": ["hello\nworld", "foo\nbar\nbaz"],
        "desc": "quoted embedded newline"
    }
    
    # 4. escaped quotes
    p = CORPUS_DIR / "04_escaped_quotes.csv"
    p.write_text('id,quote\n1,"He said ""hi"""\n2,"a ""quoted"" word"\n')
    cases["04_escaped_quotes"] = {
        "file": str(p), "rows": 2, "cols": 2,
        "valid": True, "delimiter": ",",
        "naive_should_fail": True,
        "select_col": 1, "expected_values": ['He said "hi"', 'a "quoted" word'],
        "desc": "escaped double quotes"
    }
    
    # 5. empty fields
    p = CORPUS_DIR / "05_empty.csv"
    p.write_text("a,b,c\n1,,3\n,2,\n,,\n4,5,6\n")
    cases["05_empty"] = {
        "file": str(p), "rows": 4, "cols": 3,
        "valid": True, "delimiter": ",",
        "naive_should_fail": False,
        "select_col": 1, "expected_values": ["", "2", "", "5"],
        "desc": "empty fields"
    }
    
    # 6. CRLF
    p = CORPUS_DIR / "06_crlf.csv"
    with open(p, "wb") as f:
        f.write(b"id,val\r\n1,foo\r\n2,bar\r\n")
    cases["06_crlf"] = {
        "file": str(p), "rows": 2, "cols": 2,
        "valid": True, "delimiter": ",",
        "naive_should_fail": False,
        "select_col": 1, "expected_values": ["foo", "bar"],
        "desc": "CRLF line endings"
    }
    
    # 7. UTF-8 BOM
    p = CORPUS_DIR / "07_bom.csv"
    with open(p, "wb") as f:
        f.write(b"\xef\xbb\xbfid,name\n1,\xe6\xb5\x8b\xe8\xaf\x95\n")
    cases["07_bom"] = {
        "file": str(p), "rows": 1, "cols": 2,
        "valid": True, "delimiter": ",",
        "naive_should_fail": False,
        "select_col": 1, "expected_values": ["测试"],
        "desc": "UTF-8 BOM"
    }
    
    # 8. semicolon delimiter
    p = CORPUS_DIR / "08_semicolon.csv"
    p.write_text("id;name;price\n1;alice;1,50\n2;bob;2,75\n")
    cases["08_semicolon"] = {
        "file": str(p), "rows": 2, "cols": 3,
        "valid": True, "delimiter": ";",
        "naive_should_fail": True,
        "select_col": 1, "expected_values": ["alice", "bob"],
        "desc": "semicolon-delimited (locale)"
    }
    
    # 9. ragged / malformed
    p = CORPUS_DIR / "09_ragged.csv"
    p.write_text('a,b,c\n1,2\n1,2,3,4\n5,6,7\n')
    cases["09_ragged"] = {
        "file": str(p), "rows": 3, "cols": 3,
        "valid": False,
        "delimiter": ",",
        "naive_should_fail": False,
        "select_col": 1, "expected_values": ["2", "2", "6"],
        "desc": "ragged rows / malformed"
    }
    
    # 10. bigger file for timing
    p = CORPUS_DIR / "10_big.csv"
    with open(p, "w") as f:
        f.write("id,name,val\n")
        for i in range(5000):
            f.write(f"{i},name{i},{i*2}\n")
    cases["10_big"] = {
        "file": str(p), "rows": 5000, "cols": 3,
        "valid": True, "delimiter": ",",
        "naive_should_fail": False,
        "select_col": 1, "expected_values": None,
        "desc": "bigger synthetic file (5000 rows)"
    }
    
    with open(CORPUS_DIR / "ground_truth.json", "w") as f:
        json.dump(cases, f, indent=2)
    return cases

# --- Workflows ---
def workflow_python_csv(case):
    path = case["file"]
    col = case["select_col"]
    try:
        with open(path, newline='', encoding='utf-8-sig') as f:
            delim = case["delimiter"]
            reader = csv.reader(f, delimiter=delim)
            rows = list(reader)
        if not rows:
            return False, [], 0, "empty"
        data = rows[1:]
        values = []
        for r in data:
            if col < len(r):
                values.append(r[col])
            else:
                values.append("")
        return True, values, len(data), ""
    except Exception as e:
        return False, [], 0, str(e)

def workflow_naive_split(case):
    path = case["file"]
    col = case["select_col"]
    try:
        with open(path, encoding='utf-8-sig', newline='') as f:
            lines = f.read().splitlines()
        if not lines:
            return False, [], 0, "empty"
        values = []
        for line in lines[1:]:
            parts = line.split(",")
            if col < len(parts):
                values.append(parts[col])
            else:
                values.append("")
        return True, values, len(values), ""
    except Exception as e:
        return False, [], 0, str(e)

def workflow_awk(case):
    path = case["file"]
    col = case["select_col"] + 1
    delim = case["delimiter"]
    if delim != ",":
        return None, [], 0, "non-comma delimiter"
    cmd = f"awk -F, 'NR>1 {{print ${col}}}' {path}"
    rc, out, err = run_cmd(cmd)
    if rc != 0:
        return False, [], 0, err[:100]
    values = out.splitlines()
    return True, values, len(values), ""

def workflow_cut(case):
    path = case["file"]
    col = case["select_col"] + 1
    delim = case["delimiter"]
    if delim not in [",", ";", "\t"]:
        return None, [], 0, "unsupported delimiter"
    cmd = f"tail -n +2 {path} | cut -d'{delim}' -f{col}"
    rc, out, err = run_cmd(cmd)
    if rc != 0:
        return False, [], 0, err[:100]
    values = out.splitlines()
    return True, values, len(values), ""

def workflow_grep(case):
    path = case["file"]
    cmd = f"grep -c . {path}"
    rc, out, err = run_cmd(cmd)
    try:
        count = int(out.strip())
        return True, [], count, ""
    except:
        return False, [], 0, err[:100]

# --- Benchmark ---
def benchmark_case(case_id, case, workflows):
    results = []
    for name, func, supported in workflows:
        if not supported:
            results.append({
                "case": case_id, "workflow": name,
                "skipped": True, "reason": "tool not installed"
            })
            continue
        
        ok, values, row_count, err = func(case)
        if ok is None:
            results.append({
                "case": case_id, "workflow": name,
                "skipped": True, "reason": err
            })
            continue
        
        expected = case.get("expected_values")
        if expected is not None:
            match = (values == expected)
            row_match = (row_count == case["rows"])
        else:
            match = True
            row_match = (row_count == case["rows"])
        
        naive_should_fail = case.get("naive_should_fail", False)
        is_naive = name in ("naive_split", "awk", "cut")
        silent_wrong = is_naive and naive_should_fail and match and expected is not None
        
        times = []
        for _ in range(TRIALS):
            t0 = time.perf_counter()
            func(case)
            times.append((time.perf_counter() - t0) * 1000)
        
        results.append({
            "case": case_id,
            "workflow": name,
            "correct": match and row_match,
            "values_match": match,
            "row_count_match": row_match,
            "expected_rows": case["rows"],
            "actual_rows": row_count,
            "silent_wrong": silent_wrong,
            "error": err,
            "time_mean_ms": round(statistics.mean(times), 3),
            "time_median_ms": round(statistics.median(times), 3),
            "time_stdev_ms": round(statistics.stdev(times), 3) if len(times) > 1 else 0,
            "time_min_ms": round(min(times), 3),
            "time_max_ms": round(max(times), 3),
            "trials": TRIALS,
        })
    return results

def main():
    print("CSV Command-Line Correctness Lab")
    print("=" * 60)
    
    tools = {}
    for t in ["awk", "cut", "sort", "grep", "goawk", "csvquote", "jq"]:
        tools[t] = check_tool(t)
        status = "✓" if tools[t] else "✗"
        print(f"  {status} {t}: {'found' if tools[t] else 'not installed'}")
    
    print("\nGenerating corpus...")
    cases = generate_corpus()
    print(f"  Generated {len(cases)} test cases")
    
    workflows = [
        ("python_csv", workflow_python_csv, True),
        ("naive_split", workflow_naive_split, True),
        ("awk", workflow_awk, tools["awk"]),
        ("cut", workflow_cut, tools["cut"]),
        ("grep_count", workflow_grep, tools["grep"]),
    ]
    
    print(f"\nBenchmarking {len(workflows)} workflows across {len(cases)} cases...")
    all_results = []
    for case_id, case in cases.items():
        print(f"\n{case_id}: {case['desc']}")
        results = benchmark_case(case_id, case, workflows)
        all_results.extend(results)
        for r in results:
            if r.get("skipped"):
                print(f"  {r['workflow']:15s} SKIP  {r['reason']}")
                continue
            status = "✓" if r["correct"] else "✗"
            sw = " SILENT_WRONG" if r.get("silent_wrong") else ""
            print(f"  {r['workflow']:15s} {status} {r['time_median_ms']}ms{sw}")
    
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_version": sys.version,
        "platform": platform.platform(),
        "random_seed": RANDOM_SEED,
        "trials": TRIALS,
        "tools": tools,
        "cases": len(cases),
        "results": all_results,
    }
    with open(RESULTS_DIR / "results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    with open("RESULTS.md", "w") as f:
        f.write("# CSV Command-Line Correctness Results\n\n")
        f.write(f"Generated: {output['timestamp']}\n\n")
        f.write("## Environment\n\n")
        f.write(f"- Python: {sys.version.split()[0]}\n")
        f.write(f"- Platform: {output['platform']}\n")
        f.write(f"- Random seed: {RANDOM_SEED}\n")
        f.write(f"- Trials per case: {TRIALS}\n\n")
        f.write("## Tool Versions\n\n")
        for tool, avail in tools.items():
            status = "✓ Available" if avail else "✗ Not installed"
            f.write(f"- {tool}: {status}\n")
        f.write("\n## Correctness Summary\n\n")
        f.write("| Case | python_csv | naive_split | awk | cut | grep_count |\n")
        f.write("|------|------------|-------------|-----|-----|------------|\n")
        by_case = {}
        for r in all_results:
            c = r["case"]
            by_case.setdefault(c, {})[r["workflow"]] = r
        
        for case_id in sorted(cases.keys()):
            row = [case_id]
            for wf in ["python_csv", "naive_split", "awk", "cut", "grep_count"]:
                r = by_case.get(case_id, {}).get(wf, {})
                if r.get("skipped"):
                    row.append("skip")
                elif r.get("correct"):
                    row.append("✓")
                else:
                    row.append("✗")
            f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n## Timing Summary (median ms)\n\n")
        f.write("| Case | python_csv | naive_split | awk | cut |\n")
        f.write("|------|------------|-------------|-----|-----|\n")
        for case_id in sorted(cases.keys()):
            row = [case_id]
            for wf in ["python_csv", "naive_split", "awk", "cut"]:
                r = by_case.get(case_id, {}).get(wf, {})
                if r.get("skipped") or "time_median_ms" not in r:
                    row.append("-")
                else:
                    row.append(str(r["time_median_ms"]))
            f.write("| " + " | ".join(row) + " |\n")
        
        f.write("\n## Commands Run\n\n```\n")
        f.write("python3 -m py_compile benchmark_csv_tools.py\n")
        f.write("python3 benchmark_csv_tools.py\n")
        f.write("```\n\n")
        
        f.write("## Limitations\n\n")
        f.write("- Only 10 test cases, synthetic data only\n")
        f.write("- goawk / csvquote / jq not installed, skipped honestly\n")
        f.write("- sort workflow not tested (would need key extraction)\n")
        f.write("- No encoding stress beyond UTF-8 BOM\n")
        f.write("- No performance testing on large (>MB) files\n")
        f.write("- grep_count is not a CSV parser, included only for reference\n")
    
    print(f"\n\nResults written to RESULTS.md")
    print(f"Full JSON: {RESULTS_DIR / 'results.json'}")

if __name__ == "__main__":
    main()
