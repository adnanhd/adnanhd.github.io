"""Regenerate the blog figures from their source generators.

Each generator lives in figures/src/<stem>.py (extracted verbatim from the
roam2/informatics org sources, with a deterministic RNG seed) and saves to a
relative ``figures/<stem>.svg``. We run it with cwd set to the figure's blog
directory, so the SVG lands in blogs/<blog>/figures/<stem>.svg.

    python figures/build.py                 # rebuild every figure
    python figures/build.py gp-family-timeline ssl-family-timeline   # subset

For authoring brand-new figures from scratch, see figures/figlib.py (a small
style + archetype helper); the generators here are the existing ones, kept
faithful to their original source.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = Path(__file__).resolve().parent / "src"

# generator stem -> blog directory (under blogs/) the SVG belongs to
FIGURES = {
    "cnn-detection-timeline": "computer-vision",
    "ar-causal-masking": "generative-models",
    "dgm-taxonomy": "generative-models",
    "col-family-timeline": "optimization",
    "ot-family-timeline": "optimization",
    "ot-feasibility-fidelity": "optimization",
    "gp-family-timeline": "probabilistic-deep-learning",
    "inference-tractability-landscape": "probabilistic-deep-learning",
    "qat-family-timeline": "quantization-aware-training",
    "rl-method-timeline": "reinforcement-learning",
    "kd-family-timeline": "self-supervised-learning",
    "ssl-family-timeline": "self-supervised-learning",
    "classical-trends": "statistical-deep-learning",
    "pac-bayes-trends": "statistical-deep-learning",
}


def main():
    selection = set(sys.argv[1:])
    env = {**os.environ, "MPLBACKEND": "Agg"}
    failures = 0
    for stem, blog in FIGURES.items():
        if selection and stem not in selection:
            continue
        script = SRC / f"{stem}.py"
        cwd = REPO / "blogs" / blog
        (cwd / "figures").mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [sys.executable, str(script)], cwd=cwd, env=env,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            failures += 1
            print(f"FAIL  {stem}\n{result.stderr.strip()}", file=sys.stderr)
        else:
            print(f"ok    blogs/{blog}/figures/{stem}.svg")
    if failures:
        sys.exit(f"{failures} figure(s) failed")


if __name__ == "__main__":
    main()
