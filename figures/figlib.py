"""Reusable Matplotlib toolkit for the blog figures.

The blog figures fall into two archetypes, both in plain Matplotlib style
(DejaVu Sans, tab10 colours, despined axes, faint dotted grid, ~9.2x3.8in):

  * family_timeline -- scatter of methods over a year axis; marker shape+colour
    keyed by "family"; per-point text labels; optional baseline reference lines.
    (gp-family-timeline, pac-bayes-trends, rl-method-timeline, ...)

  * landscape -- a 2D conceptual map with pastel horizontal bands, labelled
    points, and an optional curved trend arrow.
    (inference-tractability-landscape, ot-feasibility-fidelity)

Author a figure by calling one of these with plain data (lists of dicts) and
passing the result to save(). See figures/build.py for worked examples.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: render straight to file
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch

# Wide aspect matching the existing figures (664.9 x 272.5 pt / 72).
FIGSIZE = (9.2, 3.8)

# Matplotlib's default tab10 cycle, named for readable figure definitions.
TAB10 = {
    "blue": "#1f77b4", "orange": "#ff7f0e", "green": "#2ca02c",
    "red": "#d62728", "purple": "#9467bd", "brown": "#8c564b",
    "pink": "#e377c2", "gray": "#7f7f7f", "olive": "#bcbd22", "cyan": "#17becf",
}

# Pastel band fills used by the landscape figures.
BAND = {"green": "#d4ecd4", "blue": "#d6e8f5", "tan": "#f5e6d0"}

LABEL_COLOR = "#333333"


def use_style():
    """Apply the shared rcParams. Idempotent; call at the top of each builder."""
    plt.rcParams.update({
        "figure.figsize": FIGSIZE,
        "figure.dpi": 110,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.12,
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.axisbelow": True,
        "axes.grid": True,
        "grid.color": "#b0b0b0",
        "grid.alpha": 0.3,
        "grid.linewidth": 0.8,
        "grid.linestyle": ":",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8,
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "#cccccc",
        "svg.fonttype": "path",  # text as paths -> no font dependency in the SVG
    })


def save(fig, path):
    """Write fig to an SVG at path (parent dirs created) and close it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Archetype 1: family timeline
# ---------------------------------------------------------------------------

def family_timeline(points, families, *, title="", xlabel="year", ylabel="",
                    invert_y=False, baselines=None, xlim=None, ylim=None,
                    label_fontsize=8, legend_loc="lower left", legend_ncol=2,
                    figsize=None):
    """Scatter of methods over a numeric (year) axis.

    points    : list of dicts -- x, y, family, [label], [dx], [dy], [ha], [va]
                dx/dy are the label offset in points (default 7, 0).
    families  : ordered dict family_key -> {color, marker, label, [size]}
                drives both the marker styling and the legend.
    baselines : list of dicts -- y, [text], [text_ha] -- dotted reference lines.
    """
    use_style()
    fig, ax = plt.subplots(figsize=figsize or FIGSIZE)

    for key, fam in families.items():
        pts = [p for p in points if p.get("family") == key]
        ax.scatter(
            [p["x"] for p in pts], [p["y"] for p in pts],
            color=fam["color"], marker=fam.get("marker", "o"),
            s=fam.get("size", 55), edgecolors="white", linewidths=0.6,
            label=fam.get("label", key), zorder=3,
        )

    for p in points:
        if p.get("label"):
            ax.annotate(
                p["label"], (p["x"], p["y"]),
                xytext=(p.get("dx", 7), p.get("dy", 0)),
                textcoords="offset points",
                fontsize=label_fontsize, color=LABEL_COLOR,
                ha=p.get("ha", "left"), va=p.get("va", "center"),
            )

    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    if invert_y:
        ax.invert_yaxis()

    for b in (baselines or []):
        ax.axhline(b["y"], ls=":", lw=1.0, color="#888888", zorder=1)
        if b.get("text"):
            ha = b.get("text_ha", "right")
            x = ax.get_xlim()[1] if ha == "right" else ax.get_xlim()[0]
            ax.annotate(
                b["text"], (x, b["y"]), xytext=(-4 if ha == "right" else 4, -8),
                textcoords="offset points", fontsize=7.5, color="#777777",
                ha=ha, va="top",
            )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc=legend_loc, ncol=legend_ncol, handletextpad=0.4,
              columnspacing=1.1, borderaxespad=0.5)
    fig.tight_layout()
    return fig, ax


# ---------------------------------------------------------------------------
# Archetype 2: landscape map
# ---------------------------------------------------------------------------

def landscape(points, bands, *, title="", xlabel="", ylabel="", arrow=None,
              legend=None, xlim=(0, 1), ylim=(0, 1), point_color="#2b5d34",
              label_fontsize=7.5, figsize=None):
    """2D conceptual map: pastel horizontal bands + labelled points + arrow.

    bands  : list of dicts -- ymin, ymax, color, [label], [label_x]
    points : list of dicts -- x, y, label, [dx], [dy], [ha], [va]
    arrow  : dict -- start (x,y), end (x,y), [rad] (curvature, default 0.25)
    legend : list of dicts -- color, label (drawn as soft patch swatches)
    """
    use_style()
    fig, ax = plt.subplots(figsize=figsize or FIGSIZE)
    ax.grid(False)

    for band in bands:
        ax.axhspan(band["ymin"], band["ymax"], color=band["color"],
                   alpha=band.get("alpha", 0.5), zorder=0, linewidth=0)
        if band.get("label"):
            ax.text(band.get("label_x", 0.012),
                    band["ymax"] - 0.03 * (ylim[1] - ylim[0]),
                    band["label"], style="italic", fontsize=8.5,
                    color="#555555", va="top", ha="left")

    ax.scatter([p["x"] for p in points], [p["y"] for p in points],
               color=point_color, s=42, zorder=3, edgecolors="white",
               linewidths=0.5)
    for p in points:
        ax.annotate(p["label"], (p["x"], p["y"]),
                    xytext=(p.get("dx", 6), p.get("dy", 4)),
                    textcoords="offset points", fontsize=label_fontsize,
                    color="#222222", ha=p.get("ha", "left"),
                    va=p.get("va", "bottom"))

    if arrow:
        ax.add_patch(FancyArrowPatch(
            arrow["start"], arrow["end"],
            connectionstyle=f"arc3,rad={arrow.get('rad', 0.25)}",
            arrowstyle="-|>", mutation_scale=18, lw=1.6,
            color="#555555", zorder=4,
        ))

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if legend:
        handles = [Patch(facecolor=l["color"], edgecolor="none", alpha=0.7,
                         label=l["label"]) for l in legend]
        ax.legend(handles=handles, loc="lower left", fontsize=7.5,
                  borderaxespad=0.5)
    fig.tight_layout()
    return fig, ax
