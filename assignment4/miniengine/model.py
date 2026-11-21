"""Qwen3 的 numpy 前向（CPU, fp32）。只依赖 numpy；权重从 safetensors 文件直接读取（bf16 → fp32）。"""
import json, struct
from pathlib import Path
import numpy as np


def load_safetensors(path):
    """读 safetensors：8 字节头长度 + JSON 头 + 原始数据。bf16 是 fp32 的高 16 位，左移 16 位即可还原。"""
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        header = json.loads(f.read(n))
        data = np.fromfile(f, dtype=np.uint8)
    out = {}
    for name, meta in header.items():
        if name == "__metadata__":
            continue
        a, b = meta["data_offsets"]
        raw = data[a:b]
        if meta["dtype"] == "BF16":
            arr = (raw.view(np.uint16).astype(np.uint32) << 16).view(np.float32)
        elif meta["dtype"] in ("F32", "F16"):
            arr = raw.view(np.float32 if meta["dtype"] == "F32" else np.float16).astype(np.float32)
        else:
            raise ValueError(f"不支持的 dtype {meta['dtype']}")
        out[name] = arr.reshape(meta["shape"])
    return out


# ---------------- 前向的四个基本块（L4 第 1 步要你实现） ----------------

def rmsnorm(x, w, eps):
    """x: [..., d]；返回 x / sqrt(mean(x^2) + eps) * w"""
    # TODO(L4-1): 注意保持 float32（NEP 50：np.float64 标量会把整个数组提升成 float64，之后每次矩阵乘都要把权重转成 float64，慢一个数量级）
    raise NotImplementedError("rmsnorm")


def rope(x, pos, theta):
    """x: [T, H, hd]，pos: [T] 绝对位置。Qwen 用 rotate-half 形式：前一半和后一半成对旋转。"""
    # TODO(L4-1): inv_freq = 1/theta^(2i/hd)，角度 = pos × inv_freq；x 的前一半和后一半成对旋转
    raise NotImplementedError("rope")


def attention(q, k, v, start):
    """q: [T, Hq, hd] 是本步新 token（位置 start..start+T-1）；k, v: [S, Hkv, hd] 是缓存里全部 S=start+T 个位置。
    GQA：每 Hq/Hkv 个查询头共用一个 KV 头。因果掩码：位置 i 只能看 ≤ i 的 key。返回 [T, Hq*hd]。"""
    # TODO(L4-1): 先把 q 分组成 [Hkv, g, T, hd] 和 k/v 对齐；打分乘 1/sqrt(hd)（用 Python float）；位置 start+i 只能看 ≤ start+i 的 key
    raise NotImplementedError("attention")


def mlp(x, w_gate, w_up, w_down):
    """SwiGLU：down( silu(x·gate) * (x·up) )。权重已转置成 [in, out]。"""
    # TODO(L4-1): silu(z) = z * sigmoid(z)
    raise NotImplementedError("mlp")


# ---------------- 模型 ----------------

class Qwen3:
    def __init__(self, model_dir):
        d = Path(model_dir)
        c = json.loads((d / "config.json").read_text())
        self.cfg = c
        self.L, self.D = c["num_hidden_layers"], c["hidden_size"]
        self.Hq, self.Hkv, self.hd = c["num_attention_heads"], c["num_key_value_heads"], c["head_dim"]
        self.eps, self.theta = c["rms_norm_eps"], float(c["rope_theta"])
        W = load_safetensors(d / "model.safetensors")
        self.embed = W["model.embed_tokens.weight"]                       # [V, D]
        self.lm_head = W.get("lm_head.weight", self.embed)               # 文件里没有 lm_head 时用词嵌入（tie_word_embeddings）
        self.norm = W["model.norm.weight"]
        t = lambda n: np.ascontiguousarray(W[n].T)                       # nn.Linear 存的是 [out, in]
        self.layers = []
        for i in range(self.L):
            p = f"model.layers.{i}."
            self.layers.append(dict(
                ln1=W[p + "input_layernorm.weight"], ln2=W[p + "post_attention_layernorm.weight"],
                q=t(p + "self_attn.q_proj.weight"), k=t(p + "self_attn.k_proj.weight"),
                v=t(p + "self_attn.v_proj.weight"), o=t(p + "self_attn.o_proj.weight"),
                qn=W[p + "self_attn.q_norm.weight"], kn=W[p + "self_attn.k_norm.weight"],
                gate=t(p + "mlp.gate_proj.weight"), up=t(p + "mlp.up_proj.weight"), down=t(p + "mlp.down_proj.weight")))

    def forward(self, kvs, chunks):
        """一步前向，同时处理一批序列。kvs[i] 是第 i 条序列的 KV 缓存（有 .num_tokens / write / read），
        chunks[i] 是它本步的新 token（预填充时是整段提示，解码时是 1 个 token）。
        所有序列的新 token 拼成一个 [T_total, D] 矩阵做矩阵乘（批处理的收益就在这里），注意力按序列分别算。
        调用前引擎必须已经为每条序列 ensure(num_tokens + len(chunk)) 好空间。返回每条序列最后一个位置的 logits。"""
        lens = [len(c) for c in chunks]
        starts = [kv.num_tokens for kv in kvs]
        pos = np.concatenate([np.arange(s, s + n) for s, n in zip(starts, lens)])
        x = self.embed[np.concatenate([np.asarray(c, dtype=np.int64) for c in chunks])]
        offs = np.cumsum([0] + lens)
        for li, w in enumerate(self.layers):
            h = rmsnorm(x, w["ln1"], self.eps)
            q = rmsnorm((h @ w["q"]).reshape(-1, self.Hq, self.hd), w["qn"], self.eps)
            k = rmsnorm((h @ w["k"]).reshape(-1, self.Hkv, self.hd), w["kn"], self.eps)
            v = (h @ w["v"]).reshape(-1, self.Hkv, self.hd)
            q, k = rope(q, pos, self.theta), rope(k, pos, self.theta)
            outs = []
            for i, kv in enumerate(kvs):
                a, b = offs[i], offs[i + 1]
                # TODO(L4-1): 把本序列新 token 的 k/v（k[a:b], v[a:b]）写进它的缓存（从位置 starts[i] 开始），
                # 再读出全部 starts[i]+lens[i] 个位置的 K/V，调用 attention，把结果 append 到 outs
                raise NotImplementedError("forward 里的 KV 追加 + 注意力")
            x = x + np.concatenate(outs) @ w["o"]
            x = x + mlp(rmsnorm(x, w["ln2"], self.eps), w["gate"], w["up"], w["down"])
        for kv, n in zip(kvs, lens):
            kv.num_tokens += n
        last = rmsnorm(x[offs[1:] - 1], self.norm, self.eps)
        return last @ self.lm_head.T
