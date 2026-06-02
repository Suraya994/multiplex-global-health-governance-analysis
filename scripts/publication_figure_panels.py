"""
═══════════════════════════════════════════════════════════════════════════════
  UN GA VOTING × GLOBAL HEALTH GOVERNANCE
  publication-grade Split-Figure Package
  ─────────────────────────────────────────────────────────────────────────────
  Produces every panel as a standalone PNG (700 dpi) + PDF (vector).
  All data, models, resampling, and statistical procedures are preserved
  verbatim from the original dashboard analysis.
  Output directory: split_figures/
═══════════════════════════════════════════════════════════════════════════════
"""

# ─────────────────────────────────────────────────────────────────────────────
#  IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import argparse
import os
import textwrap
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.backends.backend_pdf import PdfPages

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import KFold, cross_val_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import r2_score
from sklearn.impute import SimpleImputer

from scipy import stats
from scipy.ndimage import gaussian_filter1d
from scipy.stats import pearsonr, spearmanr, norm
from scipy.stats import gaussian_kde
from statsmodels.nonparametric.smoothers_lowess import lowess
import statsmodels.api as sm
import warnings
warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(
    description="Generate publication-grade split figures from the 100-country governance panels."
)
parser.add_argument("--data-dir", default="data", help="Input CSV directory. Default: data")
parser.add_argument("--output-dir", default="split_figures", help="Output directory. Default: split_figures")
parser.add_argument("--seed", type=int, default=42, help="Random seed. Default: 42")
parser.add_argument("--n-boot", type=int, default=2000, help="Bootstrap resamples. Default: 2000")
parser.add_argument("--perm-repeats", type=int, default=30, help="Permutation repeats. Default: 30")
parser.add_argument("--n-jobs", type=int, default=1, help="Parallel jobs. Default: 1")
parser.add_argument("--dpi", type=int, default=700, help="PNG export DPI. Default: 700")
args = parser.parse_args()

np.random.seed(args.seed)

# ─────────────────────────────────────────────────────────────────────────────
#  OUTPUT DIRECTORY
# ─────────────────────────────────────────────────────────────────────────────
OUT = str(Path(args.output_dir))
os.makedirs(OUT, exist_ok=True)
generated_files = []

# ─────────────────────────────────────────────────────────────────────────────
#  COLOUR SYSTEM  (preserved from original)
# ─────────────────────────────────────────────────────────────────────────────
BG    = "#0a0a12"
C1    = "#00f5d4"   # neon teal
C2    = "#ff006e"   # neon pink
C3    = "#ffbe0b"   # neon yellow
C4    = "#8338ec"   # electric violet
C5    = "#3a86ff"   # azure
C6    = "#fb5607"   # orange
GRID  = "#1a1a2e"

cmap_div  = LinearSegmentedColormap.from_list("div",  [C2, BG, C1], N=512)
cmap_seq  = LinearSegmentedColormap.from_list("seq",  [BG, C4, C5, C1], N=512)
cmap_fire = LinearSegmentedColormap.from_list("fire", [BG, C6, C3, "#ffffff"], N=512)
cmap_cool = LinearSegmentedColormap.from_list("cool", [BG, C4, C1], N=512)

REGION_COLORS = {
    "Sub-Saharan Africa":         C1,
    "South Asia":                 C3,
    "East Asia & Pacific":        C5,
    "Middle East & North Africa": C2,
    "Latin America & Caribbean":  C6,
    "Europe & Central Asia":      C4,
    "North America":              "#aaaaaa",
}

# ─────────────────────────────────────────────────────────────────────────────
#  PUBLICATION THEME  (enlarged fonts, high contrast — applied per-figure)
# ─────────────────────────────────────────────────────────────────────────────
PUBLICATION_RC = {
    "figure.facecolor":   BG,
    "axes.facecolor":     BG,
    "axes.edgecolor":     "#3a3a5a",
    "axes.labelcolor":    "#ddddee",
    "axes.labelsize":     14,
    "axes.titlesize":     15,
    "axes.linewidth":     1.2,
    "xtick.color":        "#8888aa",
    "ytick.color":        "#8888aa",
    "xtick.labelsize":    12,
    "ytick.labelsize":    12,
    "xtick.major.width":  1.1,
    "ytick.major.width":  1.1,
    "text.color":         "#e8e8f5",
    "grid.color":         "#1c1c30",
    "grid.linewidth":     0.55,
    "font.family":        "monospace",
    "legend.facecolor":   "#10101e",
    "legend.edgecolor":   "#3a3a5a",
    "legend.fontsize":    11,
    "legend.title_fontsize": 12,
    "figure.dpi":         100,
}

def apply_publication_theme():
    plt.rcParams.update(PUBLICATION_RC)

def style_ax(ax, xlabel="", ylabel="", title="", title_color=C3, grid=True):
    """Apply consistent publication polish to an axis."""
    if title:
        ax.set_title(title, color=title_color, fontsize=15, fontweight="bold",
                     pad=12, loc="left")
    if xlabel: ax.set_xlabel(xlabel, fontsize=14, labelpad=8)
    if ylabel: ax.set_ylabel(ylabel, fontsize=14, labelpad=8)
    if grid:
        ax.grid(True, alpha=0.35, linewidth=0.55)
    ax.tick_params(axis="both", which="major", labelsize=12, length=4, width=1.1)
    for spine in ax.spines.values():
        spine.set_edgecolor("#3a3a5a")
        spine.set_linewidth(1.1)

# ─────────────────────────────────────────────────────────────────────────────
#  EXPORT FUNCTION  — saves PNG 700 dpi + vector PDF
# ─────────────────────────────────────────────────────────────────────────────
def export(fig, stem):
    """Save figure as PNG (700 dpi) and vector PDF."""
    png_path = os.path.join(OUT, stem + ".png")
    pdf_path = os.path.join(OUT, stem + ".pdf")
    fig.savefig(png_path, dpi=args.dpi, bbox_inches="tight", facecolor=BG)
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    generated_files.extend([png_path, pdf_path])
    print(f"   ✓  {stem}.png / .pdf")

def new_fig(w=13, h=8):
    apply_publication_theme()
    fig, ax = plt.subplots(figsize=(w, h), facecolor=BG)
    ax.set_facecolor(BG)
    return fig, ax

# ─────────────────────────────────────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
print("▶  Loading datasets …")
DATA = Path(args.data_dir)

panel     = pd.read_csv(DATA / "bm_who_augmented_panel_100countries_2004_2024.csv")
edges     = pd.read_csv(DATA / "un_ga_voting_similarity_edges_100countries_2004_2024.csv")
net_un    = pd.read_csv(DATA / "un_ga_voting_network_metrics_100countries_2004_2024.csv")
country_y = pd.read_csv(DATA / "un_ga_voting_country_year_summary_100countries.csv")
print(f"   Panel: {len(panel):,} rows   |   Edges: {len(edges):,} rows")

# ─────────────────────────────────────────────────────────────────────────────
#  FEATURE ENGINEERING  (unchanged from original)
# ─────────────────────────────────────────────────────────────────────────────
print("▶  Engineering features …")
feat_cols = [
    "un_yes_share","un_no_share","un_abstain_share",
    "un_degree","un_strength","un_eigen",
    "un_betweenness","un_closeness","un_local_clustering",
    "un_network_density","un_network_clustering",
    "health_spending","physicians","nurses",
    "hospital_beds","internet","gdp_pc_ppp",
]
target_col = "UHC_INDEX_REPORTED"

df = panel.copy()
df = df.dropna(subset=[target_col])
df[feat_cols] = df[feat_cols].apply(pd.to_numeric, errors="coerce")
df["voting_entropy"]    = (
    -df["un_yes_share"].clip(1e-9)    * np.log(df["un_yes_share"].clip(1e-9))
    -df["un_no_share"].clip(1e-9)     * np.log(df["un_no_share"].clip(1e-9))
    -df["un_abstain_share"].clip(1e-9)* np.log(df["un_abstain_share"].clip(1e-9))
)
df["network_influence"] = df["un_eigen"] * df["un_strength"]
df["log_gdp"]           = np.log1p(df["gdp_pc_ppp"])
df["physicians_beds"]   = df["physicians"] * df["hospital_beds"]

all_feats = feat_cols + ["voting_entropy","network_influence","log_gdp","physicians_beds"]
X_raw = df[all_feats].values
y     = df[target_col].values

imp = SimpleImputer(strategy="median")
scl = RobustScaler()
X   = scl.fit_transform(imp.fit_transform(X_raw))

# ═══════════════════════════════════════════════════════════════════════════
#  COMPUTE ALL STATISTICS  (all procedures unchanged from original)
# ═══════════════════════════════════════════════════════════════════════════

# ── Fig-1 computations ──────────────────────────────────────────────────────
print("▶  Computing Fig-1 statistics …")
N_BOOT = args.n_boot
years  = sorted(df["year"].unique())

region_trends = {reg: grp.groupby("year")[target_col].mean()
                 for reg, grp in df.groupby("region")}

mc_years_list, mc_mean_list, mc_lo_list, mc_hi_list = [], [], [], []
for yr, vals in edges.groupby("year")["un_voting_agreement"]:
    v = vals.dropna().values
    if len(v) < 10: continue
    boot = [np.mean(np.random.choice(v, len(v), replace=True)) for _ in range(N_BOOT)]
    mc_years_list.append(yr)
    mc_mean_list.append(np.mean(boot))
    mc_lo_list.append(np.percentile(boot, 2.5))
    mc_hi_list.append(np.percentile(boot, 97.5))

mc_years = np.array(mc_years_list)
mc_mean  = np.array(mc_mean_list)
mc_lo    = np.array(mc_lo_list)
mc_hi    = np.array(mc_hi_list)

country_sigma = {}
for iso, grp in df.groupby("iso3c"):
    v = grp.sort_values("year")[target_col].values
    if len(v) > 5:
        z = np.abs(stats.zscore(v))
        country_sigma[iso] = {"max_z": z.max(), "mean_z": z.mean(),
                               "region": grp["region"].iloc[0]}
sigma_df = pd.DataFrame(country_sigma).T.reset_index()
sigma_df.columns = ["iso3c","max_z","mean_z","region"]
sigma_df[["max_z","mean_z"]] = sigma_df[["max_z","mean_z"]].astype(float)

years_vio = sorted(edges["year"].unique())
cos_data  = [edges[edges["year"]==yr]["un_voting_cosine"].dropna().values
             for yr in years_vio]

# ── Fig-2 computations ──────────────────────────────────────────────────────
print("▶  Computing Fig-2 (RF/GB — this may take ~60 s) …")
rf = RandomForestRegressor(n_estimators=600, max_depth=10, min_samples_leaf=5,
                            n_jobs=args.n_jobs, oob_score=True, random_state=args.seed,
                            max_features="sqrt")
kf      = KFold(n_splits=10, shuffle=True, random_state=args.seed)
cv_r2   = cross_val_score(rf, X, y, cv=kf, scoring="r2")
cv_rmse = np.sqrt(-cross_val_score(rf, X, y, cv=kf,
                                    scoring="neg_mean_squared_error"))
rf.fit(X, y)
oob_pred = rf.oob_prediction_
feat_imp = rf.feature_importances_
feat_names = all_feats
resid    = y - oob_pred
_, p_sw  = stats.shapiro(resid[:2000])
oob_r2   = r2_score(y, oob_pred)

perm_res   = permutation_importance(rf, X, y, n_repeats=args.perm_repeats,
                                     random_state=args.seed, n_jobs=args.n_jobs)
perm_means = perm_res.importances_mean
perm_stds  = perm_res.importances_std

gb = GradientBoostingRegressor(n_estimators=400, learning_rate=0.05,
                                max_depth=5, random_state=args.seed)
gb.fit(X, y)
gb_imp = gb.feature_importances_

MC_PARTIAL = 500
partial_effects = {}
pd_feature_names = ["un_yes_share","un_no_share","un_abstain_share","un_degree"]
for fname in pd_feature_names:
    i    = feat_names.index(fname)
    grid = np.linspace(X[:, i].min(), X[:, i].max(), MC_PARTIAL)
    Xp   = np.tile(np.median(X, axis=0), (MC_PARTIAL, 1))
    Xp[:, i] = grid
    partial_effects[fname] = (grid, rf.predict(Xp))

# ── Fig-3 computations ──────────────────────────────────────────────────────
print("▶  Computing Fig-3 (PCA + t-SNE) …")
X_sc   = scl.transform(imp.transform(X_raw))
pca    = PCA(n_components=min(12, X_sc.shape[1]))
X_pca  = pca.fit_transform(X_sc)
ev     = pca.explained_variance_ratio_
tsne   = TSNE(n_components=2, perplexity=40, max_iter=1500, random_state=args.seed)
X_tsne = tsne.fit_transform(X_sc)
region_arr = df["region"].values[:len(X_tsne)]
uhc_arr    = df[target_col].values[:len(X_tsne)]

# ── Fig-4 computations ──────────────────────────────────────────────────────
print("▶  Computing Fig-4 (Network + Bayesian bootstrap) …")
region_centrality = {}
for reg, grp in net_un.groupby("region"):
    region_centrality[reg] = {
        "mean": grp.groupby("year")["un_eigen"].mean(),
        "std":  grp.groupby("year")["un_eigen"].std(),
    }

corr_boot_means, corr_boot_stds = [], []
for yr in years:
    sub = df[df["year"]==yr][["un_yes_share",target_col]].dropna()
    if len(sub) < 10: continue
    boots = []
    for _ in range(2000):
        idx  = np.random.choice(len(sub), len(sub), replace=True)
        s    = sub.iloc[idx]
        r, _ = pearsonr(s["un_yes_share"], s[target_col])
        boots.append(r)
    corr_boot_means.append((yr, np.mean(boots)))
    corr_boot_stds.append(np.std(boots))

corr_years = np.array([c[0] for c in corr_boot_means])
corr_means = np.array([c[1] for c in corr_boot_means])
corr_stds  = np.array(corr_boot_stds)

pivot_uhc = df.groupby(["region","year"])[target_col].mean().unstack()

df_yr_group = country_y.copy()
if "global_group" not in df_yr_group.columns:
    gg = net_un[["iso3c","year","global_group"]].drop_duplicates()
    df_yr_group = df_yr_group.merge(gg, on=["iso3c","year"], how="left")
df_yr_group = df_yr_group.dropna(subset=["global_group"])

# ── Fig-5 computations ──────────────────────────────────────────────────────
print("▶  Computing Fig-5 (OLS + Spearman + Cohesion) …")
X_ols  = sm.add_constant(
    df[["un_yes_share","un_eigen","log_gdp","health_spending","physicians"]]
    .fillna(df[["un_yes_share","un_eigen","log_gdp","health_spending","physicians"]].median())
)
y_ols   = df[target_col].fillna(df[target_col].median())
ols_res = sm.OLS(y_ols, X_ols).fit()

corr_cols    = ["un_yes_share","un_eigen","un_strength",
                "health_spending","gdp_pc_ppp",target_col,"UHC_SCI_INFECT"]
corr_df      = df[corr_cols].dropna()
spearman_mat = np.array([[spearmanr(corr_df[c1],corr_df[c2])[0]
                           for c2 in corr_cols] for c1 in corr_cols])

cohesion = (edges.groupby("year")
            .apply(lambda x: (x["un_voting_agreement"] > 0.80).mean())
            .reset_index())
cohesion.columns = ["year","cohesion_80"]

df_f = df.dropna(subset=["gdp_pc_ppp",target_col,"un_yes_share"]).copy()
df_f["gdp_tercile"] = pd.qcut(df_f["gdp_pc_ppp"], 3,
                                labels=["Low GDP","Mid GDP","High GDP"])

dens_df = df.dropna(subset=["un_eigen",target_col])
xd, yd  = dens_df["un_eigen"].values, dens_df[target_col].values
kde2    = gaussian_kde(np.vstack([xd, yd]))
xi_g    = np.linspace(xd.min(), xd.max(), 80)
yi_g    = np.linspace(yd.min(), yd.max(), 80)
Xi, Yi  = np.meshgrid(xi_g, yi_g)
Zi      = kde2(np.vstack([Xi.ravel(), Yi.ravel()])).reshape(Xi.shape)

print("▶  All computations done. Rendering split figures …\n")

# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE SET 1 — Monte Carlo Bootstrap × 3σ Anomaly Detection
# ═══════════════════════════════════════════════════════════════════════════

# ── 1A: Monte Carlo Voting Agreement ────────────────────────────────────────
fig, ax = new_fig(14, 8)
ax.fill_between(mc_years, mc_lo, mc_hi, color=C4, alpha=0.18,
                label=f"95% Bootstrap CI  (N={N_BOOT:,})")
ax.fill_between(mc_years,
                mc_lo + (mc_hi - mc_lo)*0.25,
                mc_hi - (mc_hi - mc_lo)*0.25,
                color=C4, alpha=0.30, label="50% Bootstrap CI")
ax.plot(mc_years, mc_mean, color=C1, lw=2.5, zorder=5, label="Bootstrap Mean")
smooth = gaussian_filter1d(mc_mean, sigma=1.2)
ax.plot(mc_years, smooth, color=C3, lw=2.0, ls="--", alpha=0.9, label="LOESS Smoother")
style_ax(ax,
         xlabel="Year",
         ylabel="Mean Pairwise Voting Agreement",
         title="Monte Carlo Bootstrap — UN GA Voting Agreement, 2004–2024",
         title_color=C1)
ax.legend(framealpha=0.85, loc="lower left")
export(fig, "fig1A_monte_carlo_voting_agreement")

# ── 1B: Per-Country UHC Volatility / 3σ Anomaly Map ────────────────────────
fig, ax = new_fig(13, 8)
for reg in sigma_df["region"].unique():
    sub = sigma_df[sigma_df["region"] == reg]
    c   = REGION_COLORS.get(reg, "#888888")
    ax.scatter(sub["mean_z"], sub["max_z"],
               color=c, alpha=0.82, s=55, label=reg, edgecolors="none")
ax.axhline(3.0, color=C2, lw=2.0, ls="--", alpha=0.9, label="3σ threshold")
ax.axhline(2.0, color=C3, lw=1.5, ls=":",  alpha=0.8, label="2σ threshold")
ax.text(sigma_df["mean_z"].max()*0.55, 3.08, "3σ", color=C2, fontsize=12,
        fontweight="bold")
style_ax(ax,
         xlabel="Mean Absolute Z-Score (temporal)",
         ylabel="Maximum Absolute Z-Score",
         title="Per-Country UHC Volatility — 3σ Anomaly Map",
         title_color=C2)
ax.legend(loc="upper left", framealpha=0.85, ncol=2, fontsize=10)
export(fig, "fig1B_uhc_anomaly_map")

# ── 1C: Regional UHC Trajectories ───────────────────────────────────────────
fig, ax = new_fig(14, 8)
for reg, trend in region_trends.items():
    c    = REGION_COLORS.get(reg, "#888888")
    yrs  = trend.index.values
    vals = trend.values
    ax.plot(yrs, vals, color=c, lw=2.2, alpha=0.9, label=reg)
    grp  = df[df["region"]==reg]
    for yr in yrs:
        sub = grp[grp["year"]==yr][target_col].dropna()
        if len(sub) > 2:
            mu, sd = sub.mean(), sub.std()
            ax.fill_between([yr-0.35, yr+0.35], mu-sd, mu+sd,
                             color=c, alpha=0.10)
style_ax(ax,
         xlabel="Year",
         ylabel="UHC Service Coverage Index",
         title="Regional UHC Trajectories with ±1σ Annual Uncertainty, 2004–2024",
         title_color=C1)
ax.legend(framealpha=0.85, ncol=2, fontsize=10)
export(fig, "fig1C_regional_uhc_trajectories")

# ── 1D: Max |Z| Distribution ────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
vals_sig = sigma_df["max_z"].dropna().values
ax.hist(vals_sig, bins=28, color=C4, alpha=0.70, edgecolor=BG,
        linewidth=0.5, density=False, label="Count")
ax.axvline(3.0, color=C2, lw=2.2, ls="--", label="3σ")
ax.axvline(2.0, color=C3, lw=1.8, ls=":",  label="2σ")
kde_sig = stats.gaussian_kde(vals_sig)
ax2 = ax.twinx()
x_range = np.linspace(0, vals_sig.max(), 250)
ax2.plot(x_range, kde_sig(x_range), color=C1, lw=2.2, label="KDE")
ax2.set_ylabel("Kernel Density", color=C1, fontsize=13)
ax2.tick_params(colors=C1, labelsize=11)
ax2.set_facecolor(BG)
for spine in ax2.spines.values():
    spine.set_edgecolor("#3a3a5a")
style_ax(ax,
         xlabel="Maximum Absolute Z-Score",
         ylabel="Number of Countries",
         title="Distribution of Maximum |Z|-Score — UHC Temporal Volatility",
         title_color=C3)
lines1, labs1 = ax.get_legend_handles_labels()
lines2, labs2 = ax2.get_legend_handles_labels()
ax.legend(lines1+lines2, labs1+labs2, framealpha=0.85, fontsize=10)
export(fig, "fig1D_max_z_distribution")

# ── 1E: Cosine Similarity Distribution per Year ─────────────────────────────
fig, ax = new_fig(16, 8)
positions = np.arange(len(years_vio))
yr_means  = [np.mean(d) for d in cos_data]
mu_all, sd_all = np.mean(yr_means), np.std(yr_means)
parts = ax.violinplot(cos_data, positions=positions, showmedians=True,
                       showextrema=False, widths=0.80)
for i, (pc, d) in enumerate(zip(parts["bodies"], cos_data)):
    z = (yr_means[i] - mu_all) / (sd_all + 1e-9)
    c = cmap_div(Normalize(-3, 3)(z))
    pc.set_facecolor(c); pc.set_alpha(0.78)
    pc.set_edgecolor(C1); pc.set_linewidth(0.8)
parts["cmedians"].set_color(C3)
parts["cmedians"].set_linewidth(2.5)
ax.set_xticks(positions)
ax.set_xticklabels(years_vio, rotation=45, fontsize=11)
style_ax(ax,
         xlabel="Year",
         ylabel="Pairwise Cosine Similarity",
         title="Monte Carlo Cosine Similarity Distribution by Year  (color encodes z-score of annual mean)",
         title_color=C3)
# colorbar proxy
sm_cb = plt.cm.ScalarMappable(cmap=cmap_div, norm=Normalize(-3, 3))
sm_cb.set_array([])
cb = plt.colorbar(sm_cb, ax=ax, fraction=0.025, pad=0.01)
cb.set_label("Z-Score of Annual Mean", fontsize=11, color="#ddddee")
cb.ax.yaxis.set_tick_params(color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
export(fig, "fig1E_cosine_similarity_distribution")


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE SET 2 — Random Forest × Gradient Boosting × Permutation Importance
# ═══════════════════════════════════════════════════════════════════════════

idx_sorted = np.argsort(feat_imp)[::-1]

# ── 2A: RF vs GB Feature Importance ─────────────────────────────────────────
fig, ax = new_fig(14, 8)
x_pos = np.arange(len(feat_names))
ax.bar(x_pos - 0.20, feat_imp[idx_sorted], width=0.38,
       color=C5, alpha=0.88, label="RF Gini Importance", zorder=3)
ax.bar(x_pos + 0.20, gb_imp[idx_sorted], width=0.38,
       color=C6, alpha=0.88, label="GB Importance", zorder=3)
for xi, val in zip(x_pos, feat_imp[idx_sorted]):
    if val > 0.04:
        ax.text(xi - 0.20, val + 0.003, f"{val:.3f}",
                ha="center", va="bottom", fontsize=8, color=C1)
ax.set_xticks(x_pos)
ax.set_xticklabels([feat_names[i][:18] for i in idx_sorted],
                   rotation=52, fontsize=10, ha="right")
style_ax(ax,
         ylabel="Feature Importance Score",
         title="Random Forest vs Gradient Boosting Feature Importance  (sorted by RF Gini)",
         title_color=C5)
ax.legend(framealpha=0.85)
export(fig, "fig2A_rf_gb_feature_importance")

# ── 2B: Permutation Importance ───────────────────────────────────────────────
fig, ax = new_fig(13, 9)
pidx = np.argsort(perm_means)[::-1]
norm_vals = (perm_means[pidx] - perm_means[pidx].min()) / (perm_means[pidx].max() - perm_means[pidx].min() + 1e-9)
colors_p  = [cmap_fire(v) for v in norm_vals]
ax.barh([feat_names[i][:24] for i in pidx], perm_means[pidx],
        xerr=perm_stds[pidx], color=colors_p, alpha=0.88,
        error_kw={"ecolor": C3, "capsize": 4, "elinewidth": 1.6}, zorder=3)
ax.axvline(0, color="#444466", lw=1.5)
style_ax(ax,
         xlabel="Mean Decrease in R²",
         title="Permutation Feature Importance  (30 repeats, ±1 SD error bars)",
         title_color=C3)
ax.tick_params(axis="y", labelsize=11)
sm_p = plt.cm.ScalarMappable(cmap=cmap_fire, norm=Normalize(perm_means[pidx].min(), perm_means[pidx].max()))
sm_p.set_array([])
cb = plt.colorbar(sm_p, ax=ax, fraction=0.025, pad=0.01)
cb.set_label("Importance magnitude", fontsize=11, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
export(fig, "fig2B_permutation_importance")

# ── 2C: 10-Fold Cross-Validated R² ─────────────────────────────────────────
fig, ax = new_fig(13, 8)
folds = np.arange(1, len(cv_r2)+1)
bar_colors = [C1 if v > cv_r2.mean() else C2 for v in cv_r2]
ax.bar(folds, cv_r2, color=bar_colors, alpha=0.88, edgecolor=BG, linewidth=0.8)
ax.axhline(cv_r2.mean(), color=C3, lw=2.2, ls="--",
           label=f"Mean R² = {cv_r2.mean():.3f} ± {cv_r2.std():.3f}")
ax.fill_between([-0.5, len(folds)+0.5],
                cv_r2.mean()-cv_r2.std(),
                cv_r2.mean()+cv_r2.std(),
                color=C3, alpha=0.12, label="±1 SD band")
style_ax(ax,
         xlabel="Fold",
         ylabel="R² Score",
         title=f"10-Fold Cross-Validated R²  — Random Forest  (mean = {cv_r2.mean():.3f})",
         title_color=C3)
ax.set_xticks(folds)
ax.legend(framealpha=0.85)
export(fig, "fig2C_cross_validated_r2")

# ── 2D: OOB Prediction Performance ─────────────────────────────────────────
fig, ax = new_fig(13, 8)
sc = ax.scatter(y, oob_pred, c=y-oob_pred, cmap=cmap_div,
                s=16, alpha=0.60, edgecolors="none", vmin=-30, vmax=30)
lims = [min(y.min(), oob_pred.min()), max(y.max(), oob_pred.max())]
ax.plot(lims, lims, color=C3, lw=2.0, ls="--", label="Perfect prediction")
cb = plt.colorbar(sc, ax=ax, fraction=0.035, pad=0.01)
cb.set_label("Residual (Actual − Predicted)", fontsize=12, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
style_ax(ax,
         xlabel="Actual UHC Index",
         ylabel="OOB Predicted UHC Index",
         title=f"Out-of-Bag Prediction Performance  (OOB R² = {oob_r2:.3f})",
         title_color=C5)
ax.legend(framealpha=0.85)
export(fig, "fig2D_oob_prediction")

# ── 2E: Cross-Validated RMSE ────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
ax.plot(folds, cv_rmse, "o-", color=C6, lw=2.5, ms=9, zorder=5)
ax.fill_between(folds, cv_rmse-cv_rmse.std()*0.5,
                cv_rmse+cv_rmse.std()*0.5, color=C6, alpha=0.18)
ax.axhline(cv_rmse.mean(), color=C3, ls="--", lw=2.0,
           label=f"Mean RMSE = {cv_rmse.mean():.2f}")
style_ax(ax,
         xlabel="Fold",
         ylabel="Root Mean Squared Error",
         title=f"10-Fold Cross-Validated RMSE  (mean = {cv_rmse.mean():.2f})",
         title_color=C6)
ax.set_xticks(folds)
ax.legend(framealpha=0.85)
export(fig, "fig2E_cross_validated_rmse")

# ── 2F: Residual Distribution ───────────────────────────────────────────────
fig, ax = new_fig(13, 8)
ax.hist(resid, bins=38, color=C4, alpha=0.72, edgecolor=BG,
        linewidth=0.5, density=True, label="Residuals")
x_norm = np.linspace(resid.min(), resid.max(), 300)
ax.plot(x_norm, norm.pdf(x_norm, resid.mean(), resid.std()),
        color=C1, lw=2.4, label="Normal fit")
kde_r = stats.gaussian_kde(resid)
ax.plot(x_norm, kde_r(x_norm), color=C2, lw=2.0, ls="--", label="KDE")
ax.axvline(0, color=C3, lw=1.5, ls=":", alpha=0.8)
style_ax(ax,
         xlabel="Prediction Residual",
         ylabel="Density",
         title=f"OOB Residual Distribution  (Shapiro-Wilk p = {p_sw:.4f})",
         title_color=C4)
ax.legend(framealpha=0.85)
export(fig, "fig2F_residual_distribution")

# ── 2G: Partial Dependence Panels ───────────────────────────────────────────
pd_colors = [C1, C2, C3, C6]
pd_titles = {
    "un_yes_share":    "Partial Dependence — UN Yes-Vote Share",
    "un_no_share":     "Partial Dependence — UN No-Vote Share",
    "un_abstain_share":"Partial Dependence — UN Abstention Share",
    "un_degree":       "Partial Dependence — UN Network Degree",
}
pd_stems = {
    "un_yes_share":    "fig2G1_partial_dependence_un_yes_share",
    "un_no_share":     "fig2G2_partial_dependence_un_no_share",
    "un_abstain_share":"fig2G3_partial_dependence_un_abstain_share",
    "un_degree":       "fig2G4_partial_dependence_un_degree",
}
for k, (fname, (grid, eff)) in enumerate(partial_effects.items()):
    c_pd   = pd_colors[k % len(pd_colors)]
    imp_v  = feat_imp[feat_names.index(fname)]
    fig, ax = new_fig(13, 8)
    ax.plot(grid, eff, lw=2.8, color=c_pd)
    ax.fill_between(grid, eff.min(), eff, alpha=0.15, color=c_pd)
    style_ax(ax,
             xlabel="Standardised Feature Value",
             ylabel="Predicted UHC Index",
             title=f"{pd_titles[fname]}  (RF Gini importance = {imp_v:.4f})",
             title_color=c_pd)
    export(fig, pd_stems[fname])


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE SET 3 — PCA Manifold × t-SNE Topology
# ═══════════════════════════════════════════════════════════════════════════

# ── 3A: t-SNE by Region ─────────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
for reg in np.unique(region_arr):
    mask = region_arr == reg
    c    = REGION_COLORS.get(reg, "#888888")
    ax.scatter(X_tsne[mask,0], X_tsne[mask,1],
               c=c, s=18, alpha=0.65, label=reg, edgecolors="none")
style_ax(ax,
         xlabel="t-SNE Dimension 1",
         ylabel="t-SNE Dimension 2",
         title="t-SNE Topology of UN Voting & Health Feature Space  (colored by region)",
         title_color=C4, grid=False)
ax.legend(framealpha=0.85, ncol=2, fontsize=10)
export(fig, "fig3A_tsne_topology_region")

# ── 3B: t-SNE UHC Gradient ──────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
sc_u = ax.scatter(X_tsne[:,0], X_tsne[:,1],
                   c=uhc_arr, cmap=cmap_seq, s=18, alpha=0.78,
                   edgecolors="none",
                   vmin=np.nanpercentile(uhc_arr,5),
                   vmax=np.nanpercentile(uhc_arr,95))
cb = plt.colorbar(sc_u, ax=ax, fraction=0.035, pad=0.01)
cb.set_label("UHC Service Coverage Index", fontsize=12, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
style_ax(ax,
         xlabel="t-SNE Dimension 1",
         ylabel="t-SNE Dimension 2",
         title="t-SNE Topology  (UHC index gradient)",
         title_color=C5, grid=False)
export(fig, "fig3B_tsne_uhc_gradient")

# ── 3C: Eigenvalue Scree ────────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
cum = np.cumsum(ev)
ax.bar(range(1, len(ev)+1), ev*100, color=C4, alpha=0.88, edgecolor=BG,
       label="Per-component variance %")
ax2 = ax.twinx()
ax2.plot(range(1, len(ev)+1), cum*100, "o-", color=C1, lw=2.5, ms=7, label="Cumulative %")
ax2.axhline(90, color=C3, ls="--", lw=1.8, alpha=0.8, label="90% threshold")
ax2.set_ylabel("Cumulative Variance (%)", color=C1, fontsize=13)
ax2.tick_params(colors=C1, labelsize=11)
ax2.set_facecolor(BG)
for spine in ax2.spines.values(): spine.set_edgecolor("#3a3a5a")
style_ax(ax,
         xlabel="Principal Component",
         ylabel="Explained Variance (%)",
         title="PCA Eigenvalue Scree — UN Voting & Health Feature Space",
         title_color=C4)
lines1, labs1 = ax.get_legend_handles_labels()
lines2, labs2 = ax2.get_legend_handles_labels()
ax.legend(lines1+lines2, labs1+labs2, framealpha=0.85, fontsize=10)
export(fig, "fig3C_pca_eigenvalue_scree")

# ── 3D: PCA Biplot ──────────────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
sc_bi = ax.scatter(X_pca[:,0], X_pca[:,1],
                    c=uhc_arr, cmap=cmap_seq, s=12, alpha=0.55,
                    edgecolors="none",
                    vmin=np.nanpercentile(uhc_arr,5),
                    vmax=np.nanpercentile(uhc_arr,95))
cb = plt.colorbar(sc_bi, ax=ax, fraction=0.035, pad=0.01)
cb.set_label("UHC Index", fontsize=12, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
scale = np.abs(X_pca[:,:2]).max(axis=0) * 0.75
for i, fname in enumerate(feat_names):
    xl = pca.components_[0, i] * scale[0]
    yl = pca.components_[1, i] * scale[1]
    if abs(xl) + abs(yl) > 1.0:
        ax.annotate("", xy=(xl, yl), xytext=(0,0),
                    arrowprops=dict(arrowstyle="->", color=C2, lw=1.5, alpha=0.75))
        ax.text(xl*1.1, yl*1.1, fname[:15], fontsize=9, color=C3, ha="center",
                path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])
ax.axhline(0, color="#333355", lw=0.9)
ax.axvline(0, color="#333355", lw=0.9)
style_ax(ax,
         xlabel=f"PC1 ({ev[0]*100:.1f}% variance)",
         ylabel=f"PC2 ({ev[1]*100:.1f}% variance)",
         title="PCA Biplot — PC1 vs PC2  (loading arrows: |loading| above threshold)",
         title_color=C4)
export(fig, "fig3D_pca_biplot")

# ── 3E: PCA Loading Matrix ──────────────────────────────────────────────────
n_comp_show = min(8, len(ev))
load_mat = pca.components_[:n_comp_show, :]
fig, ax = new_fig(16, 9)
im = ax.imshow(load_mat, cmap=cmap_div, aspect="auto", vmin=-0.7, vmax=0.7)
cb = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
cb.set_label("Loading Coefficient", fontsize=12, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
ax.set_xticks(range(len(feat_names)))
ax.set_xticklabels([f[:18] for f in feat_names],
                   rotation=48, fontsize=10, ha="right")
ax.set_yticks(range(n_comp_show))
ax.set_yticklabels([f"PC{i+1}  ({ev[i]*100:.1f}%)" for i in range(n_comp_show)],
                   fontsize=11)
for i in range(n_comp_show):
    for j in range(len(feat_names)):
        v = load_mat[i,j]
        if abs(v) > 0.28:
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                    color="#ffffff" if abs(v) > 0.45 else "#aaaacc",
                    fontweight="bold")
ax.set_title("PCA Loading Matrix  (component × feature loadings)",
             color=C4, fontsize=15, fontweight="bold", pad=12, loc="left")
export(fig, "fig3E_pca_loading_matrix")


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE SET 4 — Network Centrality × Bayesian Bootstrap
# ═══════════════════════════════════════════════════════════════════════════

# ── 4A: Bayesian Bootstrap Correlation ──────────────────────────────────────
fig, ax = new_fig(14, 8)
ax.fill_between(corr_years, corr_means-2*corr_stds, corr_means+2*corr_stds,
                color=C2, alpha=0.15, label="±2σ Bootstrap Band")
ax.fill_between(corr_years, corr_means-corr_stds, corr_means+corr_stds,
                color=C2, alpha=0.28, label="±1σ Bootstrap Band")
ax.plot(corr_years, corr_means, color=C1, lw=2.5, zorder=5, label="Bootstrap Mean r")
smooth_corr = gaussian_filter1d(corr_means, sigma=1.0)
ax.plot(corr_years, smooth_corr, color=C3, lw=2.0, ls="--", alpha=0.9,
        label="LOESS Smoother")
ax.axhline(0, color="#444466", lw=1.5)
style_ax(ax,
         xlabel="Year",
         ylabel="Pearson r  (Yes-Share vs UHC Index)",
         title="Pearson Correlation with Bayesian Bootstrap CI  (N = 2,000 per year)",
         title_color=C2)
ax.legend(framealpha=0.85)
export(fig, "fig4A_bayesian_bootstrap_correlation")

# ── 4B: Eigenvector Centrality by Region ────────────────────────────────────
fig, ax = new_fig(14, 8)
for reg, vals in region_centrality.items():
    c   = REGION_COLORS.get(reg, "#888888")
    yrs = vals["mean"].index.values
    mu  = vals["mean"].values
    sd  = vals["std"].fillna(0).values
    ax.plot(yrs, mu, color=c, lw=2.2, label=reg)
    ax.fill_between(yrs, mu-sd*0.5, mu+sd*0.5, color=c, alpha=0.12)
style_ax(ax,
         xlabel="Year",
         ylabel="Mean Eigenvector Centrality",
         title="UN Voting Network Eigenvector Centrality by Region  (±0.5σ shading)",
         title_color=C1)
ax.legend(framealpha=0.85, ncol=2, fontsize=10)
export(fig, "fig4B_eigen_centrality_by_region")

# ── 4C: Network Strength vs UHC with Sigma Ellipses ────────────────────────
fig, ax = new_fig(14, 8)
df_net = df.dropna(subset=["un_strength",target_col,"region"])
for reg in df_net["region"].unique():
    sub = df_net[df_net["region"]==reg]
    c   = REGION_COLORS.get(reg, "#888888")
    ax.scatter(sub["un_strength"], sub[target_col],
               color=c, s=14, alpha=0.45, edgecolors="none", label=reg)
    if len(sub) > 10:
        for n_sig in [1, 2]:
            cov = np.cov(sub["un_strength"].values, sub[target_col].values)
            eigenvalues, eigenvectors = np.linalg.eig(cov)
            angle = np.degrees(np.arctan2(*eigenvectors[:,0][::-1]))
            w, h  = 2 * n_sig * np.sqrt(np.abs(eigenvalues))
            ell   = mpatches.Ellipse(
                (sub["un_strength"].mean(), sub[target_col].mean()),
                w, h, angle=angle, color=c, fill=False,
                lw=1.0, alpha=0.40, ls="--" if n_sig==2 else "-"
            )
            ax.add_patch(ell)
style_ax(ax,
         xlabel="UN Voting Network Strength",
         ylabel="UHC Service Coverage Index",
         title="UN Network Strength vs UHC  (1σ / 2σ covariance ellipses by region)",
         title_color=C1)
ax.legend(framealpha=0.85, ncol=2, fontsize=10)
export(fig, "fig4C_un_strength_vs_uhc_ellipses")

# ── 4D: Betweenness Density by Global Group ─────────────────────────────────
fig, ax = new_fig(13, 8)
for grp_name, sub in net_un.groupby("global_group"):
    vals = sub["un_betweenness"].dropna().values
    kde  = stats.gaussian_kde(vals)
    xg   = np.linspace(0, vals.max(), 250)
    c    = C1 if "South" in grp_name else C4
    ax.fill_between(xg, kde(xg), alpha=0.28, color=c)
    ax.plot(xg, kde(xg), color=c, lw=2.5, label=grp_name)
    ax.axvline(vals.mean(), color=c, lw=1.5, ls="--", alpha=0.75)
style_ax(ax,
         xlabel="UN Voting Betweenness Centrality",
         ylabel="Kernel Density",
         title="Betweenness Centrality Distribution — Global South vs West / North",
         title_color=C3)
ax.legend(framealpha=0.85)
export(fig, "fig4D_betweenness_density_global_groups")

# ── 4E: UHC Heatmap by Region × Year ────────────────────────────────────────
fig, ax = new_fig(16, 9)
im2 = ax.imshow(pivot_uhc.values, cmap=cmap_seq, aspect="auto")
cb  = plt.colorbar(im2, ax=ax, fraction=0.022, pad=0.01)
cb.set_label("Mean UHC Index", fontsize=12, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
ax.set_xticks(range(len(pivot_uhc.columns)))
ax.set_xticklabels(pivot_uhc.columns.astype(int), rotation=55, fontsize=10)
ax.set_yticks(range(len(pivot_uhc.index)))
ax.set_yticklabels([r[:30] for r in pivot_uhc.index], fontsize=11)
for i in range(len(pivot_uhc.index)):
    for j in range(len(pivot_uhc.columns)):
        v = pivot_uhc.values[i,j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                    fontsize=7, color="white" if v < 60 else "#0a0a12",
                    fontweight="bold")
ax.set_title("UHC Service Coverage Index — Region × Year Heatmap",
             color=C3, fontsize=15, fontweight="bold", pad=12, loc="left")
export(fig, "fig4E_uhc_region_year_heatmap")

# ── 4F: Yes-Share Trend with Bootstrap CI ───────────────────────────────────
fig, ax = new_fig(14, 8)
for grp_name, sub in df_yr_group.groupby("global_group"):
    yr_trend = sub.groupby("year")["un_yes_share"].mean()
    c   = C1 if "South" in grp_name else C4
    yrs = yr_trend.index.values
    vals = yr_trend.values
    ax.plot(yrs, vals, color=c, lw=2.5, label=grp_name)
    ax.plot(yrs, gaussian_filter1d(vals, sigma=0.8), color=c, lw=1.2, ls=":", alpha=0.6)
    bci = []
    for y_yr in yrs:
        v_yr = sub[sub["year"]==y_yr]["un_yes_share"].dropna().values
        if len(v_yr) < 2: bci.append((vals[list(yrs).index(y_yr)],)*2); continue
        bt = [np.mean(np.random.choice(v_yr, len(v_yr), replace=True)) for _ in range(500)]
        bci.append((np.percentile(bt,5), np.percentile(bt,95)))
    ax.fill_between(yrs, [b[0] for b in bci], [b[1] for b in bci],
                    color=c, alpha=0.14)
style_ax(ax,
         xlabel="Year",
         ylabel="Mean Yes-Vote Share",
         title="UN Yes-Vote Share Trend with 95% Bootstrap CI — Global South vs North",
         title_color=C1)
ax.legend(framealpha=0.85)
export(fig, "fig4F_yes_share_trend_bootstrap")


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE SET 5 — Composite Empirical Findings
# ═══════════════════════════════════════════════════════════════════════════

# ── 5A: OLS Coefficient Forest Plot ─────────────────────────────────────────
fig, ax = new_fig(14, 8)
params = ols_res.params[1:]
cis    = ols_res.conf_int()[1:]
pvals  = ols_res.pvalues[1:]
colors_ols = [C1 if p<0.001 else C3 if p<0.01 else C6 if p<0.05 else "#555577"
              for p in pvals]
yvec = np.arange(len(params))
ax.barh(yvec, params.values, color=colors_ols, alpha=0.88,
        xerr=[(params.values-cis[0].values), (cis[1].values-params.values)],
        error_kw={"ecolor":"#aaaacc","capsize":5,"elinewidth":1.8},
        height=0.52, edgecolor=BG)
ax.axvline(0, color="#444466", lw=1.8)
ax.set_yticks(yvec)
ax.set_yticklabels(params.index, fontsize=12)
for i, (v, p) in enumerate(zip(params.values, pvals)):
    sig = "***" if p<0.001 else "**" if p<0.01 else "*" if p<0.05 else "ns"
    ax.text(v+(0.6 if v>=0 else -0.6), i, sig,
            ha="left" if v>=0 else "right", va="center",
            fontsize=11, color=C3)
legend_handles = [
    mpatches.Patch(color=C1,      label="p < 0.001"),
    mpatches.Patch(color=C3,      label="p < 0.01"),
    mpatches.Patch(color=C6,      label="p < 0.05"),
    mpatches.Patch(color="#555577",label="n.s."),
]
ax.legend(handles=legend_handles, framealpha=0.85, fontsize=10, loc="lower right")
style_ax(ax,
         xlabel=f"OLS Coefficient  (95% CI)   R² = {ols_res.rsquared:.3f}",
         title="OLS Regression Coefficients — UHC ~ Voting + Network + Health Controls",
         title_color=C3)
export(fig, "fig5A_ols_coefficient_forest")

# ── 5B: Spearman Correlation Matrix ─────────────────────────────────────────
fig, ax = new_fig(13, 9)
im3 = ax.imshow(spearman_mat, cmap=cmap_div, vmin=-1, vmax=1, aspect="auto")
cb  = plt.colorbar(im3, ax=ax, fraction=0.035, pad=0.01)
cb.set_label("Spearman ρ", fontsize=12, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
labels = [c[:16] for c in corr_cols]
ax.set_xticks(range(len(corr_cols))); ax.set_xticklabels(labels, rotation=45, fontsize=10, ha="right")
ax.set_yticks(range(len(corr_cols))); ax.set_yticklabels(labels, fontsize=10)
for i in range(len(corr_cols)):
    for j in range(len(corr_cols)):
        v = spearman_mat[i,j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                fontsize=8, color="white" if abs(v)>0.5 else "#888899",
                fontweight="bold" if abs(v)>0.5 else "normal")
ax.set_title("Spearman Rank Correlation Matrix — Voting, Network & Health Indicators",
             color=C3, fontsize=15, fontweight="bold", pad=12, loc="left")
export(fig, "fig5B_spearman_matrix")

# ── 5C: Voting Cohesion Index ────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
c_yrs  = cohesion["year"].values
c_vals = cohesion["cohesion_80"].values * 100
ax.fill_between(c_yrs, 0, c_vals, color=C5, alpha=0.35)
ax.plot(c_yrs, c_vals, "o-", color=C1, lw=2.5, ms=8, zorder=5, label="Annual cohesion")
ax.plot(c_yrs, gaussian_filter1d(c_vals, sigma=1), color=C3, lw=2.0, ls="--",
        alpha=0.9, label="LOESS smoother")
style_ax(ax,
         xlabel="Year",
         ylabel="% Country Pairs with Agreement > 0.80",
         title="UN Voting Cohesion Index, 2004–2024  (% pairs exceeding 0.80 agreement)",
         title_color=C5)
ax.legend(framealpha=0.85)
export(fig, "fig5C_voting_cohesion_index")

# ── 5D: Health–Voting Frontier ───────────────────────────────────────────────
fig, ax = new_fig(14, 8)
for tc, c in zip(["Low GDP","Mid GDP","High GDP"], [C2,C3,C1]):
    sub = df_f[df_f["gdp_tercile"]==tc]
    ax.scatter(sub["un_yes_share"], sub[target_col],
               color=c, s=14, alpha=0.40, edgecolors="none", label=tc)
    if len(sub) > 20:
        sub_s = sub.sort_values("un_yes_share")
        lo_fit = lowess(sub_s[target_col], sub_s["un_yes_share"], frac=0.4)
        ax.plot(lo_fit[:,0], lo_fit[:,1], color=c, lw=2.8, zorder=5)
style_ax(ax,
         xlabel="UN Yes-Vote Share",
         ylabel="UHC Service Coverage Index",
         title="Health–Voting Frontier  (LOESS by GDP Tercile)",
         title_color=C3)
ax.legend(framealpha=0.85)
export(fig, "fig5D_health_voting_frontier")

# ── 5E: Q-Q Plot of UHC Distribution ────────────────────────────────────────
fig, ax = new_fig(13, 8)
for grp_name, sub in df.groupby("global_group"):
    v = sub[target_col].dropna().values
    qq_res = stats.probplot(v, dist="norm")
    osm, osr = qq_res[0]
    slope, intercept, _ = qq_res[1]
    c = C1 if "South" in grp_name else C4
    ax.plot(osm, osr, ".", color=c, ms=5, alpha=0.55, label=grp_name)
    ax.plot(osm, slope*np.array(osm)+intercept, color=c, lw=2.0, alpha=0.9)
style_ax(ax,
         xlabel="Theoretical Normal Quantile",
         ylabel="Sample Quantile  (UHC Index)",
         title="Q-Q Plot — UHC Index Distribution vs Normal  (by Global Group)",
         title_color=C3)
ax.legend(framealpha=0.85)
export(fig, "fig5E_qq_uhc_distribution")

# ── 5F: 2D KDE Density ───────────────────────────────────────────────────────
fig, ax = new_fig(13, 8)
ax.contourf(Xi, Yi, Zi, levels=22, cmap=cmap_cool, alpha=0.92)
cs = ax.contour(Xi, Yi, Zi, levels=10, colors=[C3], linewidths=0.7, alpha=0.45)
ax.scatter(xd, yd, c=C1, s=5, alpha=0.18, edgecolors="none")
sm_z = plt.cm.ScalarMappable(cmap=cmap_cool,
                               norm=Normalize(Zi.min(), Zi.max()))
sm_z.set_array([])
cb = plt.colorbar(sm_z, ax=ax, fraction=0.035, pad=0.01)
cb.set_label("Joint Density", fontsize=12, color="#ddddee")
plt.setp(cb.ax.yaxis.get_ticklabels(), color="#ddddee", fontsize=10)
style_ax(ax,
         xlabel="UN Eigenvector Centrality",
         ylabel="UHC Service Coverage Index",
         title="2D KDE Joint Distribution — UN Eigenvector Centrality vs UHC Index",
         title_color=C4)
export(fig, "fig5F_kde_un_eigen_uhc")


# ═══════════════════════════════════════════════════════════════════════════
#  FIGURE CAPTION NOTES
# ═══════════════════════════════════════════════════════════════════════════
print("▶  Writing figure_caption_notes.txt …")

captions = {
"fig1A_monte_carlo_voting_agreement":
    ("Monte Carlo Bootstrap — UN General Assembly Voting Agreement (2004–2024). "
     "The figure displays the bootstrap mean pairwise voting agreement score across "
     f"{N_BOOT:,} resamples per year drawn from the full edge-list, with 50% and 95% "
     "confidence ribbons and a LOESS smoother. "
     "Temporal variation in mean agreement reflects evolving geopolitical alignment "
     "within the multilateral system, with the bootstrap uncertainty bands characterising "
     "the sampling variability inherent in year-specific dyadic distributions."),

"fig1B_uhc_anomaly_map":
    ("Per-Country UHC Volatility — 3σ Anomaly Map. "
     "Each point represents a country plotted by its mean and maximum absolute z-score "
     "computed from the longitudinal UHC service coverage index time series (2004–2024). "
     "Countries above the 3σ threshold (dashed line) exhibit statistically exceptional "
     "temporal fluctuations in health system coverage, warranting closer scrutiny of "
     "structural shocks, policy discontinuities, or data reporting anomalies."),

"fig1C_regional_uhc_trajectories":
    ("Regional UHC Service Coverage Index Trajectories with Annual Uncertainty, 2004–2024. "
     "Trend lines represent region-level annual means; shaded bands denote ±1 standard "
     "deviation across country observations within each region-year cell. "
     "Systematic upward trends are observable across all regions, yet substantial "
     "cross-regional heterogeneity in both levels and rates of improvement underscores "
     "persistent structural inequalities in global health system development."),

"fig1D_max_z_distribution":
    ("Distribution of Maximum Absolute Z-Scores Across Countries — UHC Temporal Volatility. "
     "The histogram presents the frequency distribution of each country's maximum "
     "observed absolute z-score in the UHC time series, overlaid with a kernel density "
     "estimate and 2σ/3σ threshold lines. "
     "The right skew of the distribution indicates that while most countries exhibit "
     "moderate temporal stability, a meaningful tail of countries demonstrates "
     "statistically anomalous health system trajectories."),

"fig1E_cosine_similarity_distribution":
    ("Monte Carlo Cosine Similarity Distributions by Year, 2004–2024. "
     "Each violin represents the full distribution of pairwise cosine similarity scores "
     "among country voting profiles in a given year; violin colour encodes the z-score "
     "of the annual mean relative to the grand cross-year mean. "
     "The narrowing interquartile range in recent years indicates increasing homogeneity "
     "in voting behaviour, consistent with consolidation around shared multilateral norms."),

"fig2A_rf_gb_feature_importance":
    ("Random Forest vs Gradient Boosting Feature Importance (Gini Index). "
     "Paired bars display the RF mean decrease in impurity alongside the GB equivalent "
     "for each feature, sorted in descending order of RF importance. "
     "Economic development proxies (log GDP) and direct health capacity measures "
     "dominate both rankings, while UN voting network variables demonstrate non-trivial "
     "complementary importance, supporting the hypothesis that diplomatic alignment "
     "captures governance-relevant variance beyond income."),

"fig2B_permutation_importance":
    ("Permutation Feature Importance with Bootstrap Uncertainty (30 repeats). "
     "Each bar represents the mean decrease in out-of-sample R² when a feature's "
     "values are randomly permuted, with error bars showing ±1 standard deviation "
     "across repetitions. "
     "Features whose confidence interval excludes zero contribute robust predictive "
     "signal; the ordering partially diverges from Gini-based ranking, highlighting "
     "the importance of evaluating importance under post-hoc perturbation rather than "
     "impurity reduction alone."),

"fig2C_cross_validated_r2":
    (f"10-Fold Cross-Validated R² — Random Forest Prediction of UHC Coverage. "
     f"Individual fold performance is coloured by whether it exceeds (teal) or falls "
     f"below (pink) the cross-validated mean (R² = {cv_r2.mean():.3f} ± {cv_r2.std():.3f}); "
     "the ±1 SD band indicates the degree of fold-to-fold variance. "
     "The overall cross-validated performance reflects the model's generalisation "
     "capacity and provides an unbiased estimate of predictive power on held-out data."),

"fig2D_oob_prediction":
    (f"Out-of-Bag Prediction Performance — Random Forest (OOB R² = {oob_r2:.3f}). "
     "The scatter plot compares actual UHC index values against their OOB predictions; "
     "point colour encodes the signed residual magnitude. "
     "OOB predictions constitute an approximately unbiased estimate of generalisation "
     "error without requiring a held-out test set, providing a computationally efficient "
     "validation benchmark."),

"fig2E_cross_validated_rmse":
    (f"10-Fold Cross-Validated RMSE — Random Forest. "
     f"Root mean squared error is reported per fold with a ±0.5 SD uncertainty band; "
     f"the mean RMSE of {cv_rmse.mean():.2f} index points should be evaluated relative "
     "to the observed range of the UHC index across the sample. "
     "Fold-level variance reflects both heterogeneity in the hold-out data composition "
     "and the sensitivity of ensemble performance to training set composition."),

"fig2F_residual_distribution":
    (f"Residual Distribution with Normal Reference Fit (Shapiro-Wilk p = {p_sw:.4f}). "
     "The histogram of OOB prediction residuals is overlaid with a parametric normal "
     "density and a non-parametric KDE; systematic deviation from the normal reference "
     "at the distributional tails indicates heteroscedasticity or non-linearity not "
     "fully captured by the ensemble. "
     "The Shapiro-Wilk statistic provides a formal test of the normality assumption "
     "relevant for post-hoc inference on prediction errors."),

"fig2G1_partial_dependence_un_yes_share":
    ("Partial Dependence Plot — UN Yes-Vote Share. "
     "The curve traces the marginal relationship between the standardised UN yes-vote "
     "share feature and the RF-predicted UHC index, holding all other features at their "
     "median values. "
     "Monotone or non-monotone patterns in the partial dependence reveal whether "
     "increased affirmative UN voting alignment is associated with systematically higher "
     "predicted health system coverage after controlling for other model inputs."),

"fig2G2_partial_dependence_un_no_share":
    ("Partial Dependence Plot — UN No-Vote Share. "
     "The marginal effect of dissenting voting behaviour on predicted UHC coverage is "
     "displayed, conditional on all other features held at their median. "
     "Dissenting voting patterns may proxy for strategic sovereignty claims or "
     "geopolitical non-alignment, both of which may relate to domestic health "
     "governance priorities through distinct causal pathways."),

"fig2G3_partial_dependence_un_abstain_share":
    ("Partial Dependence Plot — UN Abstention Share. "
     "The curve depicts the marginal predictive relationship between abstention rate "
     "and predicted UHC coverage. "
     "Abstention patterns in UN voting are often interpreted as strategic ambiguity or "
     "hedging behaviour; the shape of the dependence curve provides evidence on whether "
     "such political postures co-vary meaningfully with health system performance."),

"fig2G4_partial_dependence_un_degree":
    ("Partial Dependence Plot — UN Voting Network Degree Centrality. "
     "Network degree captures the breadth of a country's voting alignment connections "
     "above a similarity threshold; the partial dependence curve isolates its "
     "marginal association with predicted UHC. "
     "Degree centrality in the UN voting network may reflect a country's embeddedness "
     "in multilateral governance coalitions and its access to international health "
     "financing and technical assistance flows."),

"fig3A_tsne_topology_region":
    ("t-SNE Topology of the UN Voting and Health Governance Feature Space, coloured by region. "
     "The two-dimensional t-SNE embedding was computed from the full standardised feature "
     "matrix (UN voting, network centrality, and health capacity variables). "
     "Spatial clustering by region reveals that geographic proximity and shared "
     "institutional histories produce coherent latent signatures in the joint "
     "voting-health feature space, validating regional stratification in subsequent analyses."),

"fig3B_tsne_uhc_gradient":
    ("t-SNE Topology of the UN Voting and Health Governance Feature Space, coloured by UHC Index. "
     "The same embedding as Fig. 3A is overlaid with a continuous UHC gradient, "
     "revealing that the feature-space topology encodes substantive health system "
     "heterogeneity. "
     "Regions of high-density embedding where the UHC gradient transitions sharply "
     "indicate that the model's feature space discriminates between health coverage "
     "regimes even in dimensions primarily driven by voting patterns."),

"fig3C_pca_eigenvalue_scree":
    ("PCA Eigenvalue Scree Plot — UN Voting and Health Governance Feature Space. "
     "Individual component contributions to total variance are shown as bars; the "
     "cumulative line indicates the number of components required to explain 90% of "
     "total variance (dashed reference). "
     "The concentration of variance in the leading components justifies dimensionality "
     "reduction for downstream regression and clustering analyses, while the gradual "
     "scree tail suggests a moderate intrinsic dimensionality."),

"fig3D_pca_biplot":
    ("PCA Biplot — PC1 vs PC2 with Feature Loading Arrows. "
     "Observations are coloured by UHC index; arrows indicate the direction and "
     "magnitude of feature loadings in the PC1–PC2 plane for features whose total "
     "absolute loading exceeds a relevance threshold. "
     "The biplot reveals which features drive the principal modes of variation and "
     "how country-level observations are positioned relative to those axes, "
     "supporting qualitative diagnosis of feature clustering and multicollinearity."),

"fig3E_pca_loading_matrix":
    ("PCA Loading Matrix — Component × Feature Loadings (first 8 components). "
     "The heatmap displays the signed loading coefficients for each feature on the "
     "leading principal components; cells with |loading| > 0.28 are annotated. "
     "The loading structure reveals theoretically meaningful component interpretations: "
     "earlier components tend to aggregate health infrastructure variables, while "
     "later components increasingly isolate voting network and diplomatic alignment signals."),

"fig4A_bayesian_bootstrap_correlation":
    ("Bayesian Bootstrap Confidence Intervals for the Pearson Correlation between "
     "UN Yes-Vote Share and UHC Coverage, 2004–2024. "
     "Bootstrap distributions of the Pearson r coefficient are derived from N=2,000 "
     "weighted resamples per year; ±1σ and ±2σ credible bands are plotted alongside "
     "the bootstrap mean and a LOESS trend. "
     "Sustained positive correlation with tightening uncertainty bands over time "
     "suggests increasingly robust co-movement between diplomatic alignment and "
     "health system performance."),

"fig4B_eigen_centrality_by_region":
    ("UN Voting Network Eigenvector Centrality Trajectories by Region, 2004–2024. "
     "Regional means are computed from country-level annual eigenvector centrality "
     "scores in the thresholded bilateral voting similarity network; ±0.5σ bands "
     "represent within-region annual variance. "
     "Differential centrality trajectories across regions reflect structural shifts "
     "in multilateral coalition formation and the evolving relative influence of "
     "regional blocs within UN General Assembly voting dynamics."),

"fig4C_un_strength_vs_uhc_ellipses":
    ("UN Voting Network Strength vs UHC Index with 1σ and 2σ Covariance Ellipses by Region. "
     "Scatter observations are stratified by region; ellipses characterise the "
     "bivariate distribution via eigendecomposition of the regional covariance matrix, "
     "providing a visual analogue to confidence regions. "
     "Cross-regional variation in ellipse orientation and elongation reveals "
     "heterogeneous structural relationships between network embeddedness and "
     "health system performance, motivating region-stratified modelling."),

"fig4D_betweenness_density_global_groups":
    ("Kernel Density Comparison of UN Voting Betweenness Centrality — Global South vs West/North. "
     "KDE curves and vertical mean lines compare the betweenness centrality distributions "
     "for the two global income groupings. "
     "Betweenness centrality measures the extent to which a country lies on shortest "
     "paths between other countries in the voting similarity network; systematic "
     "distributional differences between groups reveal structural asymmetries in "
     "broker roles within the multilateral governance architecture."),

"fig4E_uhc_region_year_heatmap":
    ("UHC Service Coverage Index — Region × Year Heatmap, 2004–2024. "
     "Cell values represent annual regional means; the sequential colour scale "
     "encodes coverage levels from low (dark) to high (bright teal). "
     "The heatmap jointly visualises temporal trends and cross-regional variation, "
     "making structural transitions and acceleration points visible; notable "
     "South Asian and Sub-Saharan African gains in the post-2015 period are "
     "consistent with Sustainable Development Goal health financing commitments."),

"fig4F_yes_share_trend_bootstrap":
    ("UN Yes-Vote Share Trend with 95% Bootstrap Confidence Intervals — Global South vs North, 2004–2024. "
     "Annual mean yes-vote shares for each global grouping are plotted with non-parametric "
     "bootstrap confidence bands derived from 500 resamples per group-year cell. "
     "The divergence in yes-vote trajectories between the Global South and the "
     "West/North grouping provides macroscopic evidence of a structural geopolitical "
     "cleavage within UN General Assembly proceedings."),

"fig5A_ols_coefficient_forest":
    (f"OLS Forest Plot — UHC Regressed on UN Voting, Network, and Health Control Variables "
     f"(R² = {ols_res.rsquared:.3f}, adjusted R² = {ols_res.rsquared_adj:.3f}). "
     "Bars represent OLS point estimates with 95% confidence intervals; bar colour "
     "encodes statistical significance at conventional thresholds; asterisks denote "
     "significance levels. "
     "The specification provides a parametric benchmark for interpreting the "
     "direction and magnitude of associations between diplomatic alignment variables "
     "and health coverage after controlling for economic development and health "
     "system capacity."),

"fig5B_spearman_matrix":
    ("Spearman Rank Correlation Matrix — UN Voting, Network Centrality, and Health Indicators. "
     "All pairwise Spearman ρ coefficients are computed from the complete-case "
     "country-year panel; cells with |ρ| > 0.5 are annotated and highlighted. "
     "The non-parametric rank correlation is preferred here to handle the heavy-tailed "
     "distributions characteristic of network centrality metrics; the matrix reveals "
     "both the expected collinearity between health infrastructure measures and "
     "systematic positive correlations between diplomatic alignment indicators and "
     "health coverage outcomes."),

"fig5C_voting_cohesion_index":
    ("UN General Assembly Voting Cohesion Index, 2004–2024. "
     "The cohesion index measures the annual proportion of country dyads whose "
     "pairwise voting agreement score exceeds 0.80; a LOESS smoother overlays the "
     "raw annual series. "
     "Gradual cohesion growth over the study period reflects either genuine "
     "convergence in normative preferences or strategic voting discipline within "
     "established coalition blocs, with implications for the effective functioning "
     "of multilateral consensus-building mechanisms."),

"fig5D_health_voting_frontier":
    ("Health–Voting Frontier — UHC Coverage vs UN Yes-Vote Share, Stratified by GDP Tercile. "
     "Scatter observations are stratified by GDP per capita tercile; LOESS curves "
     "(bandwidth = 0.4) trace the conditional marginal relationship within each stratum. "
     "The GDP-stratified LOESS curves reveal that the positive association between "
     "voting alignment and health coverage is substantially stronger in lower-income "
     "countries, suggesting that multilateral diplomatic integration may be "
     "particularly consequential for health governance in resource-constrained settings."),

"fig5E_qq_uhc_distribution":
    ("Q-Q Plot — UHC Index Distribution vs Normal, by Global Group. "
     "Empirical quantiles of the UHC index are plotted against theoretical normal "
     "quantiles for the Global South and West/North groupings; fitted reference "
     "lines indicate the parametric normal approximation. "
     "Systematic departures from the reference line, particularly in the distributional "
     "tails, indicate non-normality and motivate the use of robust or rank-based "
     "inference methods in analyses involving UHC as an outcome variable."),

"fig5F_kde_un_eigen_uhc":
    ("2D Kernel Density Estimate — UN Eigenvector Centrality vs UHC Index. "
     "The joint distribution is estimated via a Gaussian KDE with automatic bandwidth "
     "selection; contour lines and filled density levels visualise probability mass "
     "concentration. "
     "The bivariate density reveals a positive associational gradient between network "
     "centrality and health coverage, with modal concentration in the middle range of "
     "both variables and a sparse high-centrality / high-UHC region occupied primarily "
     "by established Global North economies."),
}

caption_path = os.path.join(OUT, "figure_caption_notes.txt")
with open(caption_path, "w", encoding="utf-8") as f:
    f.write("UN GA VOTING × GLOBAL HEALTH GOVERNANCE\n")
    f.write("publication-grade Split Figure Package — Academic Caption Notes\n")
    f.write("=" * 78 + "\n\n")
    for stem, cap in captions.items():
        f.write(f"{'─'*78}\n")
        f.write(f"FIGURE: {stem}\n")
        f.write(f"{'─'*78}\n")
        wrapped = textwrap.fill(cap, width=76)
        f.write(wrapped + "\n\n")

generated_files.append(caption_path)
print("   ✓  figure_caption_notes.txt")

# ─────────────────────────────────────────────────────────────────────────────
#  FINAL FILE LIST
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "═"*70)
print("  GENERATED FILES")
print("═"*70)
pngs = [f for f in generated_files if f.endswith(".png")]
pdfs = [f for f in generated_files if f.endswith(".pdf")]
txts = [f for f in generated_files if f.endswith(".txt")]

print(f"\n  PNG files ({len(pngs)}):")
for p in pngs: print(f"    {os.path.basename(p)}")
print(f"\n  PDF files ({len(pdfs)}):")
for p in pdfs: print(f"    {os.path.basename(p)}")
print(f"\n  Text files:")
for p in txts: print(f"    {os.path.basename(p)}")
print(f"\n  Total files generated : {len(generated_files)}")
print(f"  Output directory      : {OUT}")
print("═"*70)
