#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_analysis.py — DESeq2 风格的两组差异表达分析（TCGA-KIRC：Tumor vs Normal）

方法概述
--------
1. 读入原始 read counts（整数）、样本分组信息与基因注释。
2. 预过滤：仅保留所有样本中总 counts >= min_total 的基因，降低多重检验负担并
   剔除不可靠的低表达基因。
3. 归一化：采用 DESeq2 的 "median-of-ratios" 方法估计每个样本的 size factor。
4. 离散度估计（negative binomial 的 alpha）：
   a. 基因水平 MLE：给定设计矩阵（截距 + 组别），在 beta 与 alpha 之间交替优化
      直至收敛，得到每基因的 (beta, alpha) 联合极大似然估计。
   b. 趋势拟合：将基因按表达均值分箱，取每箱 log(alpha) 的中位数，再用分段线性
      插值得到 "均值—离散度" 趋势曲线。
   c. MAP 收缩：以趋势值为先验中心，按 "基因 Fisher 信息" 与 "残差方差" 加权，
      将基因水平 log(alpha) 向趋势收缩，得到最终离散度。
5. 显著性检验：在最终离散度下重新用 IRLS 拟合负二项 GLM，得到组别系数的
   log2FoldChange 及其标准误，用 Wald 检验计算 P 值。
6. 多重检验校正：Benjamini–Hochberg (BH) 方法得到 padj。
7. 输出：差异基因结果表 (TSV/CSV)、火山图 (PNG) 与简短文字说明。

比较方向：Tumor（处理组）vs Normal（参照组）。
log2FoldChange > 0 表示在肿瘤中上调，< 0 表示在肿瘤中下调。

依赖：numpy, pandas, scipy, matplotlib（均可离线使用）。
"""
from __future__ import annotations

import argparse
import os
from typing import Tuple

import numpy as np
import pandas as pd
from scipy import special
from scipy import optimize

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

GAMMALN = special.gammaln
LOG = np.log


# --------------------------------------------------------------------------- #
# 负二项模型工具函数
# --------------------------------------------------------------------------- #
def nb_loglike(y: np.ndarray, mu: np.ndarray, alpha: float) -> float:
    """负二项对数似然（mean = mu, dispersion = alpha，即 Var = mu + alpha*mu^2）。"""
    a = 1.0 / alpha
    mu = np.clip(mu, 1e-300, None)
    ll = (GAMMALN(y + a) - GAMMALN(a) - GAMMALN(y + 1.0)
          + y * LOG(alpha) + y * LOG(mu) - (y + a) * LOG(1.0 + alpha * mu))
    return float(ll.sum())


def irls_nb(y: np.ndarray, s: np.ndarray, X: np.ndarray, alpha: float,
            beta_init: np.ndarray | None = None,
            max_iter: int = 60, tol: float = 1e-10) -> np.ndarray:
    """固定 alpha 下用 IRLS 拟合负二项 GLM（log 链接），返回 beta。"""
    p = X.shape[1]
    beta = (beta_init if beta_init is not None
            else np.zeros(p))
    for _ in range(max_iter):
        eta = X @ beta
        mu = s * np.exp(eta)
        mu = np.clip(mu, 1e-300, None)
        w = mu / (1.0 + alpha * mu)          # Fisher 权重
        z = eta + (y - mu) / mu              # 工作响应
        Xw = X * w[:, None]
        A = X.T @ Xw
        b = X.T @ (w * z)
        try:
            beta_new = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            beta_new = np.linalg.lstsq(A, b, rcond=None)[0]
        if not np.all(np.isfinite(beta_new)):
            break
        if np.max(np.abs(beta_new - beta)) < tol:
            beta = beta_new
            break
        beta = beta_new
    return beta


def beta_se(y: np.ndarray, s: np.ndarray, X: np.ndarray, alpha: float,
            beta: np.ndarray) -> np.ndarray:
    """由 (X'WX)^-1 对角线得到 beta 的标准误（伪逆 + 岭正则，防止奇异矩阵）。"""
    eta = X @ beta
    mu = np.clip(s * np.exp(eta), 1e-300, None)
    w = mu / (1.0 + alpha * mu)
    Xw = X * w[:, None]
    A = X.T @ Xw
    # 岭正则：仅在近奇异时稳定求逆，不影响正常基因结果
    ridge = np.eye(A.shape[0]) * 1e-12 * max(1.0, float(np.trace(A)))
    cov = np.linalg.pinv(A + ridge)
    return np.sqrt(np.clip(np.diag(cov), 0, None))


def alpha_mle_given_mu(y: np.ndarray, mu: np.ndarray) -> float:
    """给定 mu，一维最大化 alpha 的似然（有界优化）。"""
    neg = lambda a: -nb_loglike(y, mu, float(a))          # noqa: E731
    res = optimize.minimize_scalar(neg, bounds=(1e-8, 1e6), method="bounded")
    return float(res.x)


def alpha_fisher(y: np.ndarray, mu: np.ndarray, alpha: float) -> float:
    """alpha 在 MLE 处的观测 Fisher 信息（对 log(alpha) 数值二阶导）。"""
    x0 = LOG(alpha)
    h = 0.01
    f = lambda x: nb_loglike(y, mu, float(np.exp(x)))     # noqa: E731
    lp = f(x0 + h)
    lm = f(x0 - h)
    l0 = f(x0)
    d2 = (lp - 2.0 * l0 + lm) / (h * h)
    return float(max(-d2, 1e-12))


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def estimate_size_factors(counts: pd.DataFrame) -> np.ndarray:
    """DESeq2 median-of-ratios 归一化。"""
    C = counts.values.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        logc = np.log(C)
        logc[C == 0] = np.nan
        geom = np.exp(np.nanmean(logc, axis=1))           # 每基因几何均值
    geom = geom[:, None]
    ratio = C / geom
    ratio[~np.isfinite(ratio)] = np.nan
    sf = np.nanmedian(ratio, axis=0)
    sf = np.where(sf > 0, sf, 1.0)
    return sf / np.exp(np.mean(np.log(sf)))               # 中心化到 1


def estimate_dispersion(C: np.ndarray, s: np.ndarray, X: np.ndarray,
                        beta_init: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """基因水平 MLE -> 趋势拟合 -> MAP 收缩，返回 (alpha_mle, alpha_trend, alpha_final)。"""
    n_genes = C.shape[0]
    alpha_mle = np.zeros(n_genes)
    beta_mle = np.zeros((n_genes, X.shape[1]))
    mu_all = np.zeros_like(C, dtype=float)

    for g in range(n_genes):
        y = C[g]
        if y.sum() == 0:
            alpha_mle[g] = 1e-8
            continue
        beta = beta_init[g].copy()
        # 方法矩初始 alpha
        nrm = y / s
        m = nrm.mean()
        v = nrm.var()
        alpha = float(np.clip((v - m) / (m * m), 1e-8, 1e6))
        for _ in range(3):                                # 交替优化 beta/alpha
            beta = irls_nb(y, s, X, alpha, beta)
            mu = np.clip(s * np.exp(X @ beta), 1e-300, None)
            alpha = alpha_mle_given_mu(y, mu)
        alpha = float(np.clip(alpha, 1e-8, 1e6))
        if not np.isfinite(alpha):
            alpha = 1e-8
        alpha_mle[g] = alpha
        beta_mle[g] = beta
        mu_all[g] = np.clip(s * np.exp(X @ beta), 1e-300, None)

    base_mean = mu_all.mean(axis=1)

    # --- 趋势拟合：分箱取中位数 + 分段线性插值 ---
    keep = (base_mean > 0) & np.isfinite(alpha_mle) & (alpha_mle > 1e-8)
    lm = np.log10(base_mean[keep])
    la = np.log10(alpha_mle[keep])
    order = np.argsort(lm)
    lm_s, la_s = lm[order], la[order]
    n_bins = 30
    edges = np.linspace(0, len(lm_s), n_bins + 1).astype(int)
    bx, by = [], []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        if hi <= lo:
            continue
        seg = la_s[lo:hi]
        if len(seg) >= 3:
            bx.append(np.median(lm_s[lo:hi]))
            by.append(np.median(seg))
    bx = np.array(bx)
    by = np.array(by)
    trend_log10 = np.interp(np.log10(np.clip(base_mean, 1e-6, None)), bx, by,
                            left=by[0], right=by[-1])
    alpha_trend = np.power(10.0, trend_log10)

    # --- MAP 收缩（正态先验 on log(alpha)） ---
    x_mle = np.log(np.clip(alpha_mle, 1e-8, None))
    x_tr = np.log(np.clip(alpha_trend, 1e-8, None))
    resid = x_mle[keep] - x_tr[keep]
    v_prior = float(max(np.var(resid), 1e-3))
    v_gene = np.zeros(n_genes)
    for g in range(n_genes):
        if alpha_mle[g] <= 1e-8 or C[g].sum() == 0:
            v_gene[g] = 1e-3
            continue
        v_gene[g] = 1.0 / alpha_fisher(C[g], mu_all[g], alpha_mle[g])

    x_map = (x_mle / v_gene + x_tr / v_prior) / (1.0 / v_gene + 1.0 / v_prior)
    alpha_final = np.clip(np.exp(x_map), 1e-8, 1e4)

    return alpha_mle, alpha_trend, alpha_final


def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini–Hochberg 校正。"""
    n = len(pvals)
    order = np.argsort(pvals)
    ranked = pvals[order]
    adj = ranked * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0.0, 1.0)
    out = np.empty(n)
    out[order] = adj
    return out


def run_analysis(counts_path: str, info_path: str, annot_path: str,
                 out_dir: str, min_total: int = 10):
    os.makedirs(out_dir, exist_ok=True)

    counts = pd.read_csv(counts_path, sep="\t", index_col=0)
    info = pd.read_csv(info_path)
    annot = pd.read_csv(annot_path, sep="\t")

    # 样本顺序与分组对齐
    info = info.set_index("sample_id").loc[counts.columns].reset_index()
    group = info["group"].to_numpy()                       # "Normal" / "Tumor"
    assert set(group) == {"Normal", "Tumor"}, f"分组应为 Normal/Tumor，实际：{set(group)}"
    tumor_ind = (group == "Tumor").astype(float)

    # 预过滤
    keep_genes = counts.sum(axis=1) >= min_total
    counts = counts.loc[keep_genes]
    C = counts.values.astype(float)

    n, m = C.shape
    X = np.column_stack([np.ones(m), tumor_ind])           # 截距 + 组别

    # size factors
    s = estimate_size_factors(counts)

    # 初始 beta：log(组均值 + 伪计数)
    beta_init = np.zeros((n, 2))
    norm = C / s[None, :]
    beta_init[:, 0] = np.log(norm[:, tumor_ind == 0].mean(axis=1) + 0.5)
    d1 = np.log(norm[:, tumor_ind == 1].mean(axis=1) + 0.5)
    beta_init[:, 1] = d1 - beta_init[:, 0]

    alpha_mle, alpha_trend, alpha_final = estimate_dispersion(C, s, X, beta_init)

    # 用最终离散度重拟合并做 Wald 检验
    log2fc = np.zeros(n)
    se = np.zeros(n)
    pval = np.zeros(n)
    group_total = np.column_stack([C[:, tumor_ind == 0].sum(axis=1),
                                   C[:, tumor_ind == 1].sum(axis=1)])
    for g in range(n):
        b = irls_nb(C[g], s, X, alpha_final[g], beta_init[g])
        sd = beta_se(C[g], s, X, alpha_final[g], b)
        lfc = b[1] / LOG(2.0)
        if np.isfinite(lfc) and np.isfinite(sd[1]) and sd[1] > 0:
            log2fc[g] = lfc
            se[g] = sd[1] / LOG(2.0)
            pval[g] = 2.0 * (1.0 - special.ndtr(np.abs(b[1] / sd[1])))
        else:
            # 退化情形：某一组全部为 0，log2FC 发散，判为极端差异表达
            if group_total[g, 1] > 0 and group_total[g, 0] == 0:
                log2fc[g] = 15.0          # 肿瘤中专属表达 -> 上限值
                se[g] = np.nan
                pval[g] = 1e-300
            elif group_total[g, 0] > 0 and group_total[g, 1] == 0:
                log2fc[g] = -15.0         # 正常组织专属表达 -> 下限值
                se[g] = np.nan
                pval[g] = 1e-300
            else:
                log2fc[g] = 0.0
                se[g] = np.nan
                pval[g] = 1.0
    # 下界设为极小正值，避免 z 统计量过大时数值下溢产生 pvalue/padj 恰好为 0
    pval = np.clip(pval, 1e-300, 1.0)
    padj = bh_fdr(pval)

    res = pd.DataFrame({
        "gene_id": counts.index,
        "baseMean": C.mean(axis=1),
        "log2FoldChange": log2fc,
        "lfcSE": se,
        "pvalue": pval,
        "padj": padj,
        "dispersion": alpha_final,
    })
    res = res.merge(annot, on="gene_id", how="left")
    res = res.sort_values("padj", kind="stable").reset_index(drop=True)

    res.to_csv(os.path.join(out_dir, "deg_results.tsv"), sep="\t", index=False)
    res.to_csv(os.path.join(out_dir, "deg_results.csv"), index=False)

    sig_up = res[(res["padj"] < 0.05) & (res["log2FoldChange"] >= 1.0)]
    sig_dn = res[(res["padj"] < 0.05) & (res["log2FoldChange"] <= -1.0)]
    summary = {
        "n_genes_after_filter": int(n),
        "n_up": int(len(sig_up)),
        "n_down": int(len(sig_dn)),
        "n_sig": int(len(sig_up) + len(sig_dn)),
        "direction": "Tumor vs Normal (log2FoldChange>0 为肿瘤上调)",
        "criteria": "|log2FoldChange| >= 1 且 padj < 0.05",
    }

    # 火山图
    plot_volcano(res, os.path.join(out_dir, "volcano_plot.png"))

    # 简要文字说明
    top_up = sig_up.head(10)
    top_dn = sig_dn.head(10)
    lines = []
    lines.append("差异表达分析简要说明")
    lines.append("=" * 40)
    lines.append(f"数据集：TCGA-KIRC（肾透明细胞癌）")
    lines.append(f"比较方向：{summary['direction']}")
    lines.append(f"方法：DESeq2 风格负二项模型（median-of-ratios 归一化 + "
                 f"离散度趋势/MAP 收缩 + Wald 检验 + BH 校正）")
    lines.append(f"筛选标准：{summary['criteria']}")
    lines.append(f"预过滤后基因数：{summary['n_genes_after_filter']}")
    lines.append(f"显著上调基因数：{summary['n_up']}")
    lines.append(f"显著下调基因数：{summary['n_down']}")
    lines.append("")
    lines.append("上调 Top10（按 padj）：")
    for _, r in top_up.iterrows():
        lines.append(f"  {r['gene_name']:<14} {r['gene_id']:<18} "
                     f"log2FC={r['log2FoldChange']:+.2f}  padj={r['padj']:.2e}")
    lines.append("下调 Top10（按 padj）：")
    for _, r in top_dn.iterrows():
        lines.append(f"  {r['gene_name']:<14} {r['gene_id']:<18} "
                     f"log2FC={r['log2FoldChange']:+.2f}  padj={r['padj']:.2e}")
    with open(os.path.join(out_dir, "deg_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))
    print("\n结果文件：")
    print("  deg_results.tsv / deg_results.csv")
    print("  volcano_plot.png")
    print("  deg_summary.txt")
    return res, summary


def plot_volcano(res: pd.DataFrame, path: str):
    fc = res["log2FoldChange"].to_numpy()
    padj = res["padj"].to_numpy()
    y = -np.log10(np.clip(padj, 1e-300, None))

    up = (padj < 0.05) & (fc >= 1.0)
    dn = (padj < 0.05) & (fc <= -1.0)
    ns = ~(up | dn)

    fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=150)
    ax.scatter(fc[ns], y[ns], s=6, c="#bdbdbd", alpha=0.55, label="Not significant",
               rasterized=True)
    ax.scatter(fc[up], y[up], s=7, c="#d62728", alpha=0.8, label="Up in Tumor",
               rasterized=True)
    ax.scatter(fc[dn], y[dn], s=7, c="#1f77b4", alpha=0.8, label="Down in Tumor",
               rasterized=True)

    ax.axhline(-np.log10(0.05), color="k", lw=0.8, ls="--")
    ax.axvline(1.0, color="k", lw=0.8, ls="--")
    ax.axvline(-1.0, color="k", lw=0.8, ls="--")

    # 标注上/下调各 Top8
    for mask in (up, dn):
        sub = res[mask].sort_values("padj").head(8)
        for _, r in sub.iterrows():
            ax.annotate(r["gene_name"],
                        (r["log2FoldChange"], -np.log10(max(r["padj"], 1e-300))),
                        fontsize=7, xytext=(3, 3), textcoords="offset points")

    ax.set_xlabel("log2 Fold Change (Tumor / Normal)")
    ax.set_ylabel("-log10 adjusted P value")
    ax.set_title("TCGA-KIRC: Tumor vs Normal")
    ax.legend(loc="best", fontsize=8, frameon=False)
    ax.set_xlim(fc.min() - 0.5, fc.max() + 0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="DESeq2-style two-group DE analysis")
    ap.add_argument("--counts", required=True)
    ap.add_argument("--info", required=True)
    ap.add_argument("--annot", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-total", type=int, default=10)
    args = ap.parse_args()
    run_analysis(args.counts, args.info, args.annot, args.out, args.min_total)


if __name__ == "__main__":
    main()
