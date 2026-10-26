# 分析方法（DESeq2 风格）

RNA-seq 原始 counts 服从负二项（Negative Binomial, NB）分布，因为计数数据同时存在
采样方差与生物学过度离散（overdispersion）。本 Skill 复现 DESeq2 的核心流程。

## 1. 预过滤
- 仅保留所有样本总 counts >= `min_total`（默认 10）的基因。
- 目的：剔除几乎不表达的基因，降低多重检验负担，提高统计功效。

## 2. 归一化（median-of-ratios）
- 对每个基因计算跨样本的几何均值（忽略 0）。
- 每个样本的 size factor = 该样本 counts 与几何均值之比的**中位数**。
- 全体 size factor 中心化到均值为 1。
- 意义：校正不同样本测序深度（library size）差异。

## 3. 离散度估计
对每个基因建立负二项模型：

    Var(Y_ij) = mu_ij + alpha_g * mu_ij^2
    mu_ij     = s_j * exp(X_j @ beta_g)

其中 `s_j` 为样本 size factor，`X` 为设计矩阵（截距 + 组别），`alpha_g` 为基因离散度。

1. **基因水平 MLE**：在 `beta_g` 与 `alpha_g` 之间交替优化直至收敛。
   - 固定 `alpha`，用 IRLS 拟合 `beta`（负二项 GLM，log 链接）。
   - 固定 `mu`，用一维有界优化最大化 `alpha` 的对数似然。
2. **趋势拟合**：将基因按表达均值分箱，取每箱 `log10(alpha)` 中位数，
   用分段线性插值得到"均值—离散度"趋势曲线（对应 DESeq2 的 local/parametric fit）。
3. **MAP 收缩**：以趋势值为先验中心，按"基因 Fisher 信息"与"残差方差"加权，
   将 `log(alpha)` 向趋势收缩，得到最终离散度（对应 DESeq2 的经验贝叶斯收缩）。
   收缩能稳定低表达基因的离散度估计，避免极端值导致假阳性/假阴性。

## 4. 显著性检验
- 在最终离散度下重新用 IRLS 拟合负二项 GLM。
- 组别系数 `beta_group` 的 MLE 即 log2FoldChange（自然对数），
  `/ ln2` 换算为 log2 尺度。
- 标准误取自 Fisher 信息矩阵 `(X'WX)^-1` 的对角线。
- Wald 统计量 `z = beta_group / SE`，双侧正态近似得 P 值。

## 5. 多重检验校正
- Benjamini–Hochberg (BH) 方法控制 FDR，得到校正后 P 值 `padj`。

## 比较方向
- 设计矩阵中 `group` 编码为：Normal=0（参照组），Tumor=1（处理组）。
- `log2FoldChange > 0`：基因在肿瘤中上调；`< 0`：在肿瘤中下调。
- 本实验比较方向为 **Tumor vs Normal**。

## 极端差异表达基因的处理
- 当某基因在**某一组的全部样本中 counts 均为 0**（另一组有表达）时，负二项 GLM 的
  组别系数在数值上发散（log2FC → ±∞），Fisher 信息矩阵近奇异。
- 对这类基因，脚本将其判为极端差异表达：`log2FoldChange` 截断为 ±15，
  并赋予最小 P 值（记为 1e-300），它们在结果表中自然排在最显著位置。
- 标准误计算采用伪逆 + 岭正则（1e-12 量级）防止奇异矩阵，正常基因结果不受影响。

## 局限与说明
- 本实现未纳入样本配对信息（10 对 tumor–normal 来自同一患者），采用标准的
  非配对两组比较；若需控制患者间差异，可扩展为 `~ patient + group` 的配对设计。
- 未做 log2FoldChange 收缩（lfcShrink），报告的 log2FC 为 MLE。
