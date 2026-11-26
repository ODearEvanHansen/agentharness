"""迷你推理引擎：请求队列 + 调度器（静态 / 连续批处理）+ KV 缓存（连续预留 / 分页）。"""
import time
import numpy as np


class Request:
    def __init__(self, rid, prompt, max_new_tokens, eos=None):
        self.rid, self.prompt, self.max_new, self.eos = rid, list(prompt), max_new_tokens, eos
        self.out, self.kv = [], None
        self.t_first = self.t_done = None          # 墙钟时间（秒，相对 run 开始）
        self.step_first = self.step_done = None    # 第几步产出首 token / 完成

    @property
    def done(self):
        return len(self.out) >= self.max_new or (self.eos is not None and self.out and self.out[-1] == self.eos)


# ---------------- KV 缓存 ----------------

class ContiguousKV:
    """朴素做法：每条序列一上来就按 max_len 预留一整块连续内存（不管它最后用多少）。"""
    def __init__(self, L, Hkv, hd, max_len):
        self.k = np.zeros((L, max_len, Hkv, hd), np.float32)
        self.v = np.zeros_like(self.k)
        self.max_len, self.num_tokens = max_len, 0

    def ensure(self, n):
        if n > self.max_len:
            raise MemoryError(f"序列长度 {n} 超过预留的 {self.max_len}")

    def write(self, layer, start, k, v):
        self.k[layer, start:start + len(k)] = k
        self.v[layer, start:start + len(v)] = v

    def read(self, layer, n):
        return self.k[layer, :n], self.v[layer, :n]

    def reserved_tokens(self):
        return self.max_len

    def release(self):
        self.k = self.v = None


class BlockAllocator:
    """固定大小块的物理池 + 空闲链表。pool_k/pool_v: [L, num_blocks, block_size, Hkv, hd]。"""
    def __init__(self, L, Hkv, hd, num_blocks, block_size):
        self.block_size, self.num_blocks = block_size, num_blocks
        self.pool_k = np.zeros((L, num_blocks, block_size, Hkv, hd), np.float32)
        self.pool_v = np.zeros_like(self.pool_k)
        self.free = list(range(num_blocks - 1, -1, -1))

    def alloc(self):
        # TODO(L4-2): 从空闲链表取一个物理块号；没有就抛 MemoryError
        raise NotImplementedError("BlockAllocator.alloc")

    def release(self, blocks):
        # TODO(L4-2): 把这些块号还回空闲链表
        raise NotImplementedError("BlockAllocator.release")

    def num_free(self):
        return len(self.free)

    def num_used(self):
        return self.num_blocks - len(self.free)


class PagedKV:
    """一条序列的逻辑 KV：block_table[i] 是第 i 个逻辑块对应的物理块号。按需分配，结束时归还。"""
    def __init__(self, alloc):
        self.a, self.block_table, self.num_tokens = alloc, [], 0

    def ensure(self, n):
        # TODO(L4-2): 块表里的块不够装 n 个 token 时，向分配器要新块（只要不多要）
        raise NotImplementedError("PagedKV.ensure")

    def _slots(self, start, n):
        p = np.arange(start, start + n)
        bs = self.a.block_size
        return np.asarray(self.block_table)[p // bs], p % bs

    def write(self, layer, start, k, v):
        # TODO(L4-2): 位置 p 在物理块 block_table[p // bs] 的第 p % bs 格；写进 pool_k/pool_v[layer]
        raise NotImplementedError("PagedKV.write")

    def read(self, layer, n):
        # TODO(L4-2): 按块表把前 n 个位置的 K/V 拼回 [n, Hkv, hd]
        raise NotImplementedError("PagedKV.read")

    def reserved_tokens(self):
        return len(self.block_table) * self.a.block_size

    def release(self):
        self.a.release(self.block_table)
        self.block_table = []


# ---------------- 引擎 ----------------

class Engine:
    def __init__(self, model, max_batch=4, kv="paged", block_size=16, num_blocks=512, max_len=1024):
        self.model, self.max_batch, self.kv_mode, self.max_len = model, max_batch, kv, max_len
        L, Hkv, hd = model.L, model.Hkv, model.hd
        self.shape = (L, Hkv, hd)
        self.alloc = BlockAllocator(L, Hkv, hd, num_blocks, block_size) if kv == "paged" else None
        self.bytes_per_token = 2 * L * Hkv * hd * 4
        self.waiting, self.running, self.finished = [], [], []
        self.steps, self.peak_used, self.peak_reserved = 0, 0, 0

    def add(self, req):
        self.waiting.append(req)

    def new_kv(self):
        return PagedKV(self.alloc) if self.kv_mode == "paged" else ContiguousKV(*self.shape, self.max_len)

    def blocks_for(self, req):
        return -(-(len(req.prompt) + req.max_new) // self.alloc.block_size)

    def can_admit(self, req):
        """分页：物理块按需分配；但准入时按最坏长度（提示 + max_new）“承诺”块数，保证跑到一半不会缺块。
        （vLLM 的做法是超额准入、缺块时抢占重算；这里为了简单不做抢占。）"""
        if self.kv_mode != "paged":
            return True
        promised = sum(self.blocks_for(r) for r in self.running if not r.done)
        return promised + self.blocks_for(req) <= self.alloc.num_blocks

    def admit(self, mode):
        """静态批处理：只有当前批全部结束才接新的一批；连续批处理：每一步都把空出来的槽位补上。"""
        # TODO(L4-3): static：running 非空就不接新请求；continuous：每步都补满 max_batch。用 can_admit 判断 KV 够不够；新请求要 r.kv = self.new_kv() 并放进 running。返回本步新接纳的请求列表
        raise NotImplementedError("Engine.admit")

    def step(self, mode="continuous"):
        new = self.admit(mode)
        active = [r for r in self.running if not r.done]
        if not active:
            return
        chunks = [r.prompt if r in new else [r.out[-1]] for r in active]
        for r, c in zip(active, chunks):
            r.kv.ensure(r.kv.num_tokens + len(c))
        self.track()
        logits = self.model.forward([r.kv for r in active], chunks)
        self.steps += 1
        now = time.perf_counter() - self.t0
        for r, lg in zip(active, logits):
            r.out.append(int(np.argmax(lg)))
            if r.t_first is None:
                r.t_first, r.step_first = now, self.steps
            if r.done:
                r.t_done, r.step_done = now, self.steps
                r.kv.release()              # 分页：块立即归还；静态批处理下槽位仍被占到整批结束
        if mode == "continuous" or all(r.done for r in self.running):
            self.finished += [r for r in self.running if r.done]
            self.running = [r for r in self.running if not r.done]

    def track(self):
        used = sum(r.kv.num_tokens + (len(r.prompt) if r.kv.num_tokens == 0 else 1) for r in self.running if not r.done)
        res = sum(r.kv.reserved_tokens() for r in self.running if not r.done)
        self.peak_used, self.peak_reserved = max(self.peak_used, used), max(self.peak_reserved, res)

    def run(self, requests, mode="continuous"):
        self.t0 = time.perf_counter()
        for r in requests:
            self.add(r)
        while self.waiting or self.running:
            n = self.steps
            self.step(mode)
            if self.steps == n and not self.running:
                raise RuntimeError("调度卡住：有请求在等待，但一个都放不进来（KV 块不够？）")
        return requests
