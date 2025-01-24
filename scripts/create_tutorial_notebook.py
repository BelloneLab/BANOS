# scripts/create_tutorial_notebook.py
"""Generate demo/tutorial_python.ipynb with two sections:
  Section 1 — Classic BANOS usage
  Section 2 — Frame-based F1 vs BANOS: our approach and why it differs from CalMS21

Run from the project root:
    python scripts/create_tutorial_notebook.py
"""

from pathlib import Path

import nbformat

nb = nbformat.v4.new_notebook()

cells = [
    # ── Intro ──────────────────────────────────────────────────────────────
    nbformat.v4.new_markdown_cell(
        "# BANOS Tutorial — Python\n\n"
        "**BANOS** (Behavior ANnOtation Score) evaluates how well algorithmic annotations "
        "match human ground truth for animal behavior studies.\n\n"
        "This tutorial has two sections:\n"
        "1. **Classic BANOS usage** — score annotations with `banos.score()`, interpret metrics\n"
        "2. **Frame-based F1 vs BANOS** — why BANOS differs from CalMS21 frame F1, and why intentionally\n\n"
        "Dataset: CalMS21-derived, 10 recordings, behaviors: "
        "`attack`, `investigation`, `mount` (dropping `other`)."
    ),
    # ── Section 1 ──────────────────────────────────────────────────────────
    nbformat.v4.new_markdown_cell("---\n## Section 1 — Classic BANOS Usage"),
    nbformat.v4.new_markdown_cell("### 1.1 Setup"),
    nbformat.v4.new_code_cell(
        "from pathlib import Path\n"
        "import math\n\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n\n"
        "import banos\n\n"
        'print(f"banos version: {banos.__version__}")\n\n'
        'DATASET = Path("../data/dataset_human_vs_human")\n'
        'BEHAVIORS = ["attack", "investigation", "mount"]'
    ),
    nbformat.v4.new_markdown_cell(
        "### 1.2 Single Recording\n\n"
        "Recording_1, behaviors `attack`/`investigation`/`mount` (dropping `other`).\n\n"
        "> **Note (v0.2.0 absent-behavior rule):**  \n"
        "> - GT has no bouts AND machine predicts nothing \u2192 all metrics = **1.0** (correct absence)  \n"
        "> - GT has no bouts BUT machine predicts bouts \u2192 all metrics = **0.0** (false detection)"
    ),
    nbformat.v4.new_code_cell(
        'pred = pd.read_csv(DATASET / "Recording_1" / "humanAnnotation_2.csv")[BEHAVIORS]\n'
        'gt   = pd.read_csv(DATASET / "Recording_1" / "humanAnnotation_1.csv")[BEHAVIORS]\n\n'
        'print(f"Frames: {len(pred)}  |  Behaviors: {BEHAVIORS}")\n'
        'print("GT bouts per behavior:")\n'
        "for b in BEHAVIORS:\n"
        "    n_bouts = (gt[b].diff().fillna(gt[b]) == 1).sum()\n"
        '    print(f"  {b}: {n_bouts} bouts")'
    ),
    nbformat.v4.new_code_cell(
        "metrics = banos.score(pred, gt)\n\n"
        'metrics_df = pd.DataFrame(metrics).T.rename(columns={"f1_score": "DA (F1)"})\n'
        'print("Per-behavior metrics \u2014 Recording 1")\n'
        "print(metrics_df.round(4).to_string())"
    ),
    nbformat.v4.new_code_cell(
        "fig, ax = plt.subplots(figsize=(9, 2.5))\n"
        'plot_df = pd.DataFrame(metrics).T[["f1_score", "so", "tp", "ic", "precision", "recall"]]\n'
        'plot_df.columns = ["DA (F1)", "SO", "TP", "IC", "Precision", "Recall"]\n'
        "sns.heatmap(\n"
        "    plot_df.astype(float),\n"
        '    annot=True, fmt=".3f", cmap="RdYlGn", vmin=0, vmax=1,\n'
        '    ax=ax, linewidths=0.5, cbar_kws={"shrink": 0.8},\n'
        ")\n"
        'ax.set_title("Per-Behavior Metrics \u2014 Recording 1")\n'
        'ax.set_xlabel("Metric")\n'
        'ax.set_ylabel("Behavior")\n'
        "plt.tight_layout()\n"
        "plt.show()"
    ),
    nbformat.v4.new_markdown_cell(
        "### 1.3 Multi-Recording Batch\n\n"
        "Pass a dict of `{name: (pred, gt)}` \u2014 returns `(group_metrics, overall_metrics)`."
    ),
    nbformat.v4.new_code_cell(
        "data = {}\n"
        "for n in range(1, 11):\n"
        '    rec_dir = DATASET / f"Recording_{n}"\n'
        '    p = pd.read_csv(rec_dir / "humanAnnotation_2.csv")[BEHAVIORS]\n'
        '    g = pd.read_csv(rec_dir / "humanAnnotation_1.csv")[BEHAVIORS]\n'
        '    data[f"Recording_{n}"] = (p, g)\n\n'
        "group_metrics, overall_metrics = banos.score(data)\n\n"
        'print("Overall metrics \u2014 10 recordings (nanmean across behaviors and recordings)")\n'
        "for metric, value in overall_metrics.items():\n"
        '    v = f"{value:.4f}" if value is not None and not math.isnan(value) else "NaN"\n'
        '    print(f"  {metric:<12} {v}")'
    ),
    nbformat.v4.new_code_cell(
        'group_df = pd.DataFrame(group_metrics).T[["f1_score", "so", "tp", "ic", "precision", "recall"]]\n'
        'group_df.columns = ["DA (F1)", "SO", "TP", "IC", "Precision", "Recall"]\n\n'
        "fig, ax = plt.subplots(figsize=(9, 2.5))\n"
        "sns.heatmap(\n"
        "    group_df.astype(float),\n"
        '    annot=True, fmt=".3f", cmap="RdYlGn", vmin=0, vmax=1,\n'
        '    ax=ax, linewidths=0.5, cbar_kws={"shrink": 0.8},\n'
        ")\n"
        'ax.set_title("Group Metrics \u2014 10 Recordings (nanmean per behavior)")\n'
        'ax.set_xlabel("Metric")\n'
        'ax.set_ylabel("Behavior")\n'
        "plt.tight_layout()\n"
        "plt.show()"
    ),
    nbformat.v4.new_markdown_cell(
        "### 1.4 Metric Explanations\n\n"
        "| Metric | Full name | What it captures |\n"
        "|--------|-----------|------------------|\n"
        "| **DA** | Detection Accuracy (F1) | Bout-level F1 \u2014 did the system find the right bouts? |\n"
        "| **SO** | Segment Overlap | Temporal IoU \u2014 how well do detected bouts overlap GT? |\n"
        "| **TP** | Temporal Precision | Are bout boundaries (start/end frames) accurate? |\n"
        "| **IC** | Intra-bout Continuity | Is each detected bout clean, without label fragmentation? |\n\n"
        "**Absent-behavior rule (v0.2.0):**\n"
        "- GT has no bouts **and** machine predicts nothing \u2192 all metrics = **1.0** (correct absence)  \n"
        "- GT has no bouts **but** machine predicts bouts \u2192 all metrics = **0.0** (false detection)"
    ),
    # ── Section 2 ──────────────────────────────────────────────────────────
    nbformat.v4.new_markdown_cell(
        "---\n"
        "## Section 2 \u2014 Frame-based F1 vs BANOS: our approach and why it differs from CalMS21"
    ),
    nbformat.v4.new_markdown_cell(
        "### 2a. Frame-based F1: our implementation\n\n"
        "We compute per-recording frame F1 for each behavior, macro-average across behaviors, "
        "then mean across recordings.\n\n"
        "Absent-behavior scoring (explicit):\n"
        "- GT=0 bouts and machine=0 bouts \u2192 **1.0** (correct absence)  \n"
        "- GT=0 bouts and machine has bouts \u2192 **0.0** (false detection)"
    ),
    nbformat.v4.new_code_cell(
        "def frame_f1(pred_col, gt_col):\n"
        '    """Frame-level F1 with explicit absent-behavior scoring.\n\n'
        "    GT=0 bouts and machine=0 bouts -> 1.0 (correct absence)\n"
        "    GT=0 bouts and machine has bouts -> 0.0 (false detection)\n"
        "    Otherwise: standard precision/recall/F1.\n"
        '    """\n'
        "    if gt_col.sum() == 0 and pred_col.sum() == 0:\n"
        "        return 1.0\n"
        "    if gt_col.sum() == 0 and pred_col.sum() > 0:\n"
        "        return 0.0\n"
        "    tp = ((pred_col == 1) & (gt_col == 1)).sum()\n"
        "    fp = ((pred_col == 1) & (gt_col == 0)).sum()\n"
        "    fn = ((pred_col == 0) & (gt_col == 1)).sum()\n"
        '    p  = tp / (tp + fp) if (tp + fp) > 0 else float("nan")\n'
        '    r  = tp / (tp + fn) if (tp + fn) > 0 else float("nan")\n'
        '    return 2*p*r/(p+r) if (p+r) > 0 else float("nan")\n\n\n'
        "# Per-recording F1 per behavior, then macro-average, then mean across recordings\n"
        "per_rec_f1 = []\n"
        "for rec_name, (p, g) in data.items():\n"
        "    f1s = [frame_f1(p[b].values, g[b].values) for b in BEHAVIORS]\n"
        "    per_rec_f1.append(np.nanmean(f1s))\n\n"
        "frame_f1_score = np.nanmean(per_rec_f1)\n"
        'print(f"Frame-based F1 (our approach): {frame_f1_score:.3f}")  # Expected: ~0.791'
    ),
    nbformat.v4.new_markdown_cell("### 2b. BANOS metrics: same recordings, same behaviors"),
    nbformat.v4.new_code_cell(
        "group_metrics_all, overall_metrics_all = banos.score(data)\n\n"
        'banos_da = overall_metrics_all["f1_score"]\n'
        'banos_so = overall_metrics_all["so"]\n'
        'banos_tp = overall_metrics_all["tp"]\n'
        'banos_ic = overall_metrics_all["ic"]\n\n'
        'print(f"BANOS DA (F1): {banos_da:.3f}")\n'
        'print(f"BANOS SO:      {banos_so:.3f}")\n'
        'print(f"BANOS TP:      {banos_tp:.3f}")\n'
        'print(f"BANOS IC:      {banos_ic:.3f}")'
    ),
    nbformat.v4.new_markdown_cell("### 2c. Side-by-side comparison"),
    nbformat.v4.new_code_cell(
        "comparison = [\n"
        '    ("Frame-based F1", frame_f1_score, "Frame overlap; correct absence = 1"),\n'
        '    ("BANOS DA (F1)",  banos_da,       "Bout-level detection (did system find right bouts?)"),\n'
        '    ("BANOS SO",       banos_so,       "Temporal quality of overlapping bouts"),\n'
        '    ("BANOS TP",       banos_tp,       "Boundary precision"),\n'
        '    ("BANOS IC",       banos_ic,       "Label stability within detected bouts"),\n'
        "]\n\n"
        'print(f\'{"Metric":<20} {"Value":>7}  What it captures\')\n'
        'print("-" * 70)\n'
        "for name, val, desc in comparison:\n"
        '    v = f"{val:.3f}" if val is not None and not math.isnan(val) else "NaN"\n'
        '    print(f"{name:<20} {v:>7}  {desc}")'
    ),
    nbformat.v4.new_markdown_cell(
        "### 2d. Why our approach differs from CalMS21 \u2014 and why intentionally\n\n"
        "**CalMS21 official frame-based F1 (Task 1):**\n"
        "- Pool all frames from all recordings \u2192 one global F1 per behavior\n"
        "- No explicit absent-behavior handling (relies on pooling \u2014 behaviors appear somewhere in the full dataset)\n"
        "- Macro-average across 3 behaviors (attack/investigation/mount)\n\n"
        "**Our approach differs in two ways:**\n\n"
        "1. **Per-recording then averaged**: we treat each recording equally; CalMS21 weights by recording length. "
        "Per-recording aggregation preserves recording-level variability \u2014 which is scientifically meaningful for ethological studies.\n\n"
        "2. **Explicit absent-behavior scoring**: we explicitly reward correct absence (score 1) and penalize false detection (score 0). "
        "CalMS21\u2019s pooled approach implicitly handles this by having behaviors present in at least some videos.\n\n"
        "We do **not** align with CalMS21\u2019s pooled approach because BANOS\u2019s purpose is to quantify annotation quality "
        "**per recording**, not globally. Collapsing all recordings into one global pool hides per-recording variability "
        "that is central to BANOS\u2019s value.\n\n"
        "> For direct comparison with CalMS21 leaderboard numbers, use the CalMS21 dataset with their exact metric.  \n"
        "> For publications, state both the frame F1 methodology and the BANOS metrics explicitly."
    ),
    nbformat.v4.new_markdown_cell(
        "### 2e. Thought experiment \u2014 the shifted annotator\n\n"
        "Synthetic 100-frame example demonstrating why frame F1 alone is insufficient."
    ),
    nbformat.v4.new_code_cell(
        "N = 100\n\n"
        "# Ground truth: bouts at frames 20-29 and 60-69\n"
        "gt_s = np.zeros(N, dtype=int)\n"
        "gt_s[20:30] = 1\n"
        "gt_s[60:70] = 1\n\n"
        "# Prediction A: identical to GT\n"
        "pred_a = gt_s.copy()\n\n"
        "# Prediction B: same bouts shifted 15 frames forward (no frame overlap)\n"
        "pred_b = np.zeros(N, dtype=int)\n"
        "pred_b[35:45] = 1\n"
        "pred_b[75:85] = 1\n\n"
        "# Prediction C: shifted only 2 frames (small overlap)\n"
        "pred_c = np.zeros(N, dtype=int)\n"
        "pred_c[22:32] = 1\n"
        "pred_c[62:72] = 1\n\n\n"
        "def frame_f1_raw(pred_col, gt_col):\n"
        "    tp = ((pred_col == 1) & (gt_col == 1)).sum()\n"
        "    fp = ((pred_col == 1) & (gt_col == 0)).sum()\n"
        "    fn = ((pred_col == 0) & (gt_col == 1)).sum()\n"
        "    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0\n"
        "    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0\n"
        "    return 2*p*r/(p+r) if (p+r) > 0 else 0.0\n\n\n"
        "def _fmt(v):\n"
        '    return f"{v:.3f}" if v is not None and not (isinstance(v, float) and math.isnan(v)) else "NaN"\n\n\n'
        "gt_ser = pd.Series(gt_s)\n"
        'for label, pred_arr in [("A (identical)", pred_a), ("B (shift 15f)", pred_b), ("C (shift 2f)", pred_c)]:\n'
        "    pred_ser = pd.Series(pred_arr)\n"
        "    ff1 = frame_f1_raw(pred_arr, gt_s)\n"
        '    b_m = banos.score(pred_ser.to_frame("beh"), gt_ser.to_frame("beh"))["beh"]\n'
        "    print(\n"
        '        f"Pred {label}: Frame F1={ff1:.2f}  "\n'
        "        f\"BANOS DA={_fmt(b_m['f1_score'])}  \"\n"
        "        f\"SO={_fmt(b_m['so'])}  \"\n"
        "        f\"TP={_fmt(b_m['tp'])}\"\n"
        "    )"
    ),
    nbformat.v4.new_markdown_cell(
        "**Interpretation:**\n"
        "- **Frame F1** tells you how many frames overlap \u2014 a 15-frame shift collapses the score to 0.\n"
        "- **BANOS DA** tells you whether the system found the right *bouts* (count-level matching). "
        "Both shifted predictions still detect 2 bouts matching 2 GT bouts, so DA=1.0.\n"
        "- **BANOS TP** quantifies the temporal shift magnitude \u2014 a small shift gives high TP (~1.0), "
        "a large shift gives low TP.\n"
        "- **BANOS SO** measures fractional temporal IoU of matched bouts.\n\n"
        "Frame F1 says \u201cshifted by 15 frames is equally wrong as completely missing\u201d.  \n"
        "BANOS tells you *how* the system is wrong \u2014 and by how much."
    ),
]

nb.cells = cells
nb.metadata["kernelspec"] = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}
nb.metadata["language_info"] = {"name": "python", "version": "3.12.0"}

out = Path("demo/tutorial_python.ipynb")
out.parent.mkdir(exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"Created {out}")
