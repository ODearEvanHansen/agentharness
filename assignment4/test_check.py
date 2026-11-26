"""check.py 抄袭判定的单元测试。运行：python3 -m pytest assignment4/test_check.py 或 python3 assignment4/test_check.py"""
import copy, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check import looks_copied, is_measured  # noqa: E402


def ref(e):
    return json.loads((HERE / "reference" / f"{e}.json").read_text(encoding="utf-8"))


def honest(e, scale=0.5):
    """模拟诚实重跑：确定性字段（token/草稿计数、接受率）和参考相同，测量值不同。"""
    d = copy.deepcopy(ref(e))
    d["threads"], d["seconds"] = 8, d["seconds"] * 3

    def walk(x, path=""):
        for k, v in (x.items() if isinstance(x, dict) else []):
            p = f"{path}/{k}"
            if isinstance(v, dict):
                walk(v, p)
            elif isinstance(v, (int, float)) and not isinstance(v, bool) and is_measured(p):
                x[k] = round(v * scale + 0.01, 2)
    walk(d["results"])
    return d


def test_honest_runs_not_copied():
    for e in ("E1", "E2", "E3", "E4", "E5"):
        assert not looks_copied(honest(e), ref(e)), e


def test_student_run_E2_E3_not_copied():
    # 真实学员 8 线程实测值：计数字段与参考逐位相同，耗时/速度不同
    e2 = ref("E2")
    e2["results"]["cache_off"].update(first_prompt_ms=140018, second_prompt_ms=139878)
    e2["results"]["cache_on"].update(first_prompt_ms=139739, second_prompt_ms=1445)
    assert not looks_copied(e2, ref("E2"))
    e3 = ref("E3")
    for k, v in (("baseline", 9.38), ("draft_n3", 9.77), ("draft_n16", 4.52)):
        e3["results"][k]["tg_tok_s"] = v
    assert not looks_copied(e3, ref("E3"))


def test_verbatim_copy_detected():
    for e in ("E1", "E2", "E3", "E4", "E5"):
        r = ref(e)
        assert looks_copied(copy.deepcopy(r), r), e
        # 只改机器信息也算复制
        d = copy.deepcopy(r)
        d["cpu"], d["threads"], d["seconds"] = "my cpu", 8, 999
        assert looks_copied(d, r), e


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
