#!/usr/bin/env python3
"""Generate M0 mini task set: each task is a directory with code + test_task.py (exit 0 = solved).

Tasks are small on purpose (M0 sanity check of the loop vs DSH), ~1 file each, a few multi-file.
"""
import json, shutil, textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "tasks"

TASKS = {
"t01_sum_range": {
 "prompt": "test_task.py 失败了。修复 mathx.py 中的 bug，使测试通过。不要修改测试文件。",
 "files": {
  "mathx.py": "def sum_to(n):\n    \"\"\"Return 1 + 2 + ... + n.\"\"\"\n    return sum(range(1, n))\n",
  "test_task.py": "from mathx import sum_to\nassert sum_to(1) == 1\nassert sum_to(10) == 55\nassert sum_to(0) == 0\nprint('ok')\n"}},
"t02_fizzbuzz": {
 "prompt": "实现 fb.py 里的 fizzbuzz(n)，让 test_task.py 通过。不要修改测试文件。",
 "files": {
  "fb.py": "def fizzbuzz(n):\n    raise NotImplementedError\n",
  "test_task.py": "from fb import fizzbuzz\nassert fizzbuzz(15) == ['1','2','Fizz','4','Buzz','Fizz','7','8','Fizz','Buzz','11','Fizz','13','14','FizzBuzz']\nassert fizzbuzz(0) == []\nprint('ok')\n"}},
"t03_reverse_words": {
 "prompt": "test_task.py 失败了，请修复 text.py，不要修改测试文件。",
 "files": {
  "text.py": "def reverse_words(s):\n    \"\"\"Reverse word order; collapse runs of whitespace to one space; strip ends.\"\"\"\n    return ' '.join(s.split(' ')[::-1])\n",
  "test_task.py": "from text import reverse_words\nassert reverse_words('a b c') == 'c b a'\nassert reverse_words('  hello   world ') == 'world hello'\nassert reverse_words('') == ''\nprint('ok')\n"}},
"t04_merge_no_mutate": {
 "prompt": "merge_config 有副作用导致 test_task.py 失败，修复 cfg.py。不要修改测试文件。",
 "files": {
  "cfg.py": "def merge_config(base, override):\n    \"\"\"Deep-merge override into a copy of base. Must not mutate inputs.\"\"\"\n    for k, v in override.items():\n        if isinstance(v, dict) and isinstance(base.get(k), dict):\n            base[k] = merge_config(base[k], v)\n        else:\n            base[k] = v\n    return base\n",
  "test_task.py": "from cfg import merge_config\nbase = {'a': 1, 'n': {'x': 1, 'y': 2}}\nover = {'n': {'y': 3}, 'b': 2}\nout = merge_config(base, over)\nassert out == {'a': 1, 'n': {'x': 1, 'y': 3}, 'b': 2}, out\nassert base == {'a': 1, 'n': {'x': 1, 'y': 2}}, base\nassert over == {'n': {'y': 3}, 'b': 2}\nprint('ok')\n"}},
"t05_parse_duration": {
 "prompt": "实现 dur.py 里的 parse_duration，规格见 docstring 和 test_task.py。不要修改测试文件。",
 "files": {
  "dur.py": "def parse_duration(s: str) -> int:\n    \"\"\"Parse durations like '1h30m', '45s', '2h', '1h2m3s' into seconds.\n    Units: h, m, s; each at most once, in that order. Raise ValueError on bad input.\"\"\"\n    raise NotImplementedError\n",
  "test_task.py": "from dur import parse_duration\nassert parse_duration('1h30m') == 5400\nassert parse_duration('45s') == 45\nassert parse_duration('1h2m3s') == 3723\nassert parse_duration('2h') == 7200\nfor bad in ['', 'h', '1x', '30m1h', '1h1h', 'abc']:\n    try:\n        parse_duration(bad)\n    except ValueError:\n        pass\n    else:\n        raise AssertionError('accepted ' + repr(bad))\nprint('ok')\n"}},
"t06_fib_memo": {
 "prompt": "fib(80) 跑不完，test_task.py 超时。修复 fib.py 的性能问题，结果要正确。不要修改测试文件。",
 "files": {
  "fib.py": "def fib(n, memo={}):\n    if n < 2:\n        return n\n    return fib(n - 1) + fib(n - 2)\n",
  "test_task.py": "import signal\nsignal.alarm(5)\nfrom fib import fib\nassert fib(10) == 55\nassert fib(80) == 23416728348467685\nprint('ok')\n"}},
"t07_rename_import": {
 "prompt": "有人把 util.py 里的 normalize 改名成了 normalize_name，但没更新调用方，test_task.py 报错。修复调用方（不要把函数名改回去，不要改测试）。",
 "files": {
  "util.py": "def normalize_name(s):\n    return ' '.join(s.strip().lower().split())\n",
  "users.py": "from util import normalize\n\ndef key(user):\n    return normalize(user['name'])\n",
  "report.py": "import util\n\ndef title(rows):\n    return [util.normalize(r) for r in rows]\n",
  "test_task.py": "import users, report, util\nassert not hasattr(util, 'normalize')\nassert users.key({'name': '  Ada  LOVELACE '}) == 'ada lovelace'\nassert report.title(['A  B']) == ['a b']\nprint('ok')\n"}},
"t08_csv_quotes": {
 "prompt": "load_rows 解析带引号和逗号的 CSV 字段出错，修复 data.py 让 test_task.py 通过。不要修改测试文件。",
 "files": {
  "data.py": "def load_rows(path):\n    rows = []\n    with open(path) as f:\n        header = f.readline().strip().split(',')\n        for line in f:\n            rows.append(dict(zip(header, line.strip().split(','))))\n    return rows\n",
  "people.csv": "name,city,note\nAda,London,\"first programmer, arguably\"\n\"Hopper, Grace\",New York,COBOL\n",
  "test_task.py": "from data import load_rows\nr = load_rows('people.csv')\nassert len(r) == 2\nassert r[0]['note'] == 'first programmer, arguably', r[0]\nassert r[1]['name'] == 'Hopper, Grace' and r[1]['city'] == 'New York', r[1]\nprint('ok')\n"}},
}

if __name__ == "__main__":
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for name, t in TASKS.items():
        d = ROOT / name
        d.mkdir(parents=True)
        for fn, content in t["files"].items():
            (d / fn).write_text(content, encoding="utf-8")
        (d / "PROMPT.txt").write_text(t["prompt"], encoding="utf-8")
    (ROOT / "index.json").write_text(json.dumps({k: v["prompt"] for k, v in TASKS.items()}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(TASKS), "tasks ->", ROOT)
