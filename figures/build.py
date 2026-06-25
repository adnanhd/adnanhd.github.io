"""Figure definitions + renderer.

Each entry in FIGURES maps an output path (relative to the repo root) to a
builder that returns (fig, ax) from figlib. Run:

    python figures/build.py              # write all figures to their paths
    python figures/build.py <out_dir>    # write under <out_dir> instead (preview)

Add a new figure by writing a builder and registering it in FIGURES.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import BAND, TAB10, family_timeline, landscape, save  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Example 1 -- family timeline (Gaussian-process methods over time)
# ---------------------------------------------------------------------------

def gp_family_timeline():
    families = {
        "exact":  {"color": TAB10["blue"],   "marker": "o", "label": "exact"},
        "fullgp": {"color": TAB10["orange"], "marker": "s", "label": "full GP"},
        "deepgp": {"color": TAB10["green"],  "marker": "D", "label": "deep-gp"},
        "dkl":    {"color": TAB10["red"],    "marker": "v", "label": "dkl"},
        "nngp":   {"color": TAB10["purple"], "marker": "^", "label": "nngp-ntk"},
    }
    points = [
        {"x": 2006,   "y": 2.965, "family": "exact"},
        {"x": 2006,   "y": 2.955, "family": "fullgp", "label": "Full GP", "dx": 9, "dy": -2},
        {"x": 2009,   "y": 2.910, "family": "fullgp", "label": "VFE/Titsias", "dx": 9},
        {"x": 2013,   "y": 2.885, "family": "deepgp", "label": "SVGP", "dx": 9, "dy": 7},
        {"x": 2013,   "y": 2.895, "family": "deepgp", "label": "Deep GP 2L", "dx": 9, "dy": -7},
        {"x": 2017,   "y": 2.810, "family": "deepgp", "label": "DSVI 3L", "dx": 9, "dy": 5},
        {"x": 2017,   "y": 2.820, "family": "deepgp", "label": "DSVI 5L", "dx": 9, "dy": -9},
        {"x": 2017.6, "y": 2.830, "family": "dkl",    "label": "Salimbeni-orth DKL", "dx": 9},
        {"x": 2021,   "y": 2.792, "family": "deepgp", "label": "Dutordoir DGP", "dx": 9},
        {"x": 2021,   "y": 2.850, "family": "dkl",    "label": "Bayesian DKL", "dx": 9},
        {"x": 2018,   "y": 2.930, "family": "nngp",   "label": "Jacot NTK", "dx": -9, "ha": "right"},
        {"x": 2019,   "y": 2.922, "family": "nngp",   "label": "Novak NTK", "dx": 9},
        {"x": 2018,   "y": 2.955, "family": "nngp",   "label": "Lee NNGP", "dx": 9},
        {"x": 2020,   "y": 2.900, "family": "nngp",   "label": "Yang TT", "dx": -9, "ha": "right"},
        {"x": 2020.3, "y": 2.905, "family": "nngp",   "label": "Hron TransNNGP", "dx": 9},
        {"x": 2020.3, "y": 2.915, "family": "nngp",   "label": "Novak Myrtle NTK", "dx": 9, "dy": -8},
        {"x": 2020,   "y": 2.928, "family": "nngp",   "label": "NN-NNGP", "dx": 9, "dy": -11},
    ]
    return family_timeline(
        points, families,
        title="GP family evolution: UCI NLL vs publication year",
        xlabel="year",
        ylabel="regression NLL (averaged over 9 splits, lower)",
        invert_y=True,
        baselines=[{"y": 2.97, "text": "Full-GP UCI baseline (NLL 2.97)"}],
        xlim=(2005, 2022.5), ylim=(2.75, 3.0), legend_ncol=3,
    )


# ---------------------------------------------------------------------------
# Example 2 -- landscape (inference tractability vs model generality)
# ---------------------------------------------------------------------------

def inference_landscape():
    bands = [
        {"ymin": 0.66, "ymax": 1.00, "color": BAND["green"], "alpha": 0.55,
         "label": "Exact posterior"},
        {"ymin": 0.33, "ymax": 0.66, "color": BAND["blue"], "alpha": 0.55,
         "label": "Deterministic approximate"},
        {"ymin": 0.00, "ymax": 0.33, "color": BAND["tan"], "alpha": 0.55,
         "label": "Stochastic / implicit"},
    ]
    points = [
        {"x": 0.08, "y": 0.93, "label": "Conjugate\nBayes (Beta-Bernoulli)"},
        {"x": 0.17, "y": 0.83, "label": "Kalman\nfilter (Lin-Gauss)"},
        {"x": 0.30, "y": 0.71, "label": "VB / mean-field"},
        {"x": 0.42, "y": 0.55, "label": "MacKay\nLaplace BNN", "ha": "right", "dx": -6},
        {"x": 0.50, "y": 0.50, "label": "BBB\nmean-field"},
        {"x": 0.60, "y": 0.55, "label": "SPEN\n(grad-desc inference)", "dy": 6},
        {"x": 0.66, "y": 0.44, "label": "HMC BNN", "dy": -12},
        {"x": 0.72, "y": 0.40, "label": "amortized VI"},
        {"x": 0.82, "y": 0.27, "label": "Flow NF\n(change-of-var.)"},
        {"x": 0.90, "y": 0.22, "label": "Score /\nDiffusion (implicit)"},
        {"x": 0.92, "y": 0.12, "label": "EBM\n(NCE / PCD)"},
    ]
    legend = [
        {"color": BAND["green"], "label": "Exact inference (conjugate / chain topology)"},
        {"color": BAND["blue"],  "label": "Deterministic approximate (Laplace, ELBO, mean-field)"},
        {"color": BAND["tan"],   "label": "Stochastic / implicit (HMC, amortized VI, score matching)"},
    ]
    return landscape(
        points, bands,
        title="Inference tractability vs model generality",
        xlabel="Model generality  (structural constraints → arbitrary neural architectures)",
        ylabel="Inference tractability (exact → approximate → implicit)",
        arrow={"start": (0.10, 0.90), "end": (0.90, 0.18), "rad": 0.28},
        legend=legend, point_color="#2b5d34",
    )


FIGURES = {
    "figures/examples/gp-family-timeline.svg": gp_family_timeline,
    "figures/examples/inference-tractability-landscape.svg": inference_landscape,
}


def main():
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO
    for rel, builder in FIGURES.items():
        fig, _ = builder()
        out = save(fig, base / rel)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
