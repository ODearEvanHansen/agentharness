"""任务执行环境（已提供，无需修改）。

agent 只通过 Env 接触任务：
  env.bash(cmd, timeout) -> (output, exit_code)     在任务目录 / 容器 /testbed 中执行
  env.read(path) -> str
  env.write(path, content)

两种实现：
  LocalEnv(dir)          课程小题：在本地临时目录执行（run.py 会在 Docker 里运行整套小题，见 README）
  ContainerEnv(name)     SWE-bench：在已启动的任务容器里执行（docker exec），工作目录 /testbed
"""
import json
import subprocess
from pathlib import Path

MAX_OUT = 8000


class Env:
    workdir = "."

    def bash(self, cmd: str, timeout: int = 120) -> tuple[str, int]:
        raise NotImplementedError

    def read(self, path: str) -> str:
        raise NotImplementedError

    def write(self, path: str, content: str) -> None:
        raise NotImplementedError


class LocalEnv(Env):
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.workdir = str(self.root)

    def bash(self, cmd, timeout=120):
        try:
            p = subprocess.run(cmd, shell=True, cwd=self.root, capture_output=True, text=True, timeout=timeout)
            return (p.stdout + p.stderr)[-MAX_OUT:], p.returncode
        except subprocess.TimeoutExpired:
            return f"[timed out after {timeout}s]", 124

    def _p(self, path):
        p = (self.root / path).resolve()
        if self.root not in p.parents and p != self.root:
            raise PermissionError(f"path escapes task dir: {path}")
        return p

    def read(self, path):
        return self._p(path).read_text(encoding="utf-8")

    def write(self, path, content):
        p = self._p(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


class ContainerEnv(Env):
    PRE = "source /opt/miniconda3/bin/activate testbed 2>/dev/null; cd /testbed; "

    def __init__(self, container: str):
        self.ctr = container
        self.workdir = "/testbed"

    def bash(self, cmd, timeout=120):
        try:
            p = subprocess.run(["docker", "exec", self.ctr, "bash", "-lc", self.PRE + cmd],
                               capture_output=True, text=True, timeout=timeout)
            return (p.stdout + p.stderr)[-MAX_OUT:], p.returncode
        except subprocess.TimeoutExpired:
            return f"[timed out after {timeout}s]", 124

    def read(self, path):
        p = subprocess.run(["docker", "exec", self.ctr, "cat", "--", self._abs(path)], capture_output=True, text=True)
        if p.returncode != 0:
            raise FileNotFoundError(p.stderr.strip())
        return p.stdout

    def write(self, path, content):
        code = "import json,sys,pathlib;a=json.load(sys.stdin);f=pathlib.Path(a['p']);f.parent.mkdir(parents=True,exist_ok=True);f.write_text(a['c'])"
        p = subprocess.run(["docker", "exec", "-i", self.ctr, "python3", "-c", code],
                           input=json.dumps({"p": self._abs(path), "c": content}), capture_output=True, text=True)
        if p.returncode != 0:
            raise OSError(p.stderr.strip()[-300:])

    @staticmethod
    def _abs(path):
        return path if path.startswith("/") else "/testbed/" + path
