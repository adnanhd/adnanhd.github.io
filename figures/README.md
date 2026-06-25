# Blog figures

In-repo, reproducible generators for every figure used by the blogs.

## Layout

- `src/<name>.py` -- one generator per blog figure (14 total), each extracted
  verbatim from its `~/org/roam2/informatics` org source and given a fixed RNG
  seed so re-runs don't churn. Each saves a relative `figures/<name>.svg`.
- `build.py` -- runs the generators with the right working directory so each
  SVG lands in `blogs/<blog>/figures/<name>.svg`. Holds the figure -> blog map.
- `figlib.py` -- a small style + archetype helper (`family_timeline`,
  `landscape`) for authoring *new* figures in the house style.

## Usage

```bash
pip install matplotlib                          # only dependency
python figures/build.py                         # rebuild every figure
python figures/build.py gp-family-timeline      # rebuild a subset
```

Each generated SVG matches its committed counterpart (same source); a re-render
differs only in matplotlib's per-run element IDs / timestamp.

## The figures

| figure | blog | kind |
|---|---|---|
| cnn-detection-timeline | computer-vision | timeline |
| ar-causal-masking | generative-models | custom |
| dgm-taxonomy | generative-models | custom |
| col-family-timeline | optimization | timeline |
| ot-family-timeline | optimization | timeline |
| ot-feasibility-fidelity | optimization | landscape |
| gp-family-timeline | probabilistic-deep-learning | timeline |
| inference-tractability-landscape | probabilistic-deep-learning | landscape |
| qat-family-timeline | quantization-aware-training | timeline |
| rl-method-timeline | reinforcement-learning | timeline |
| kd-family-timeline | self-supervised-learning | timeline |
| ssl-family-timeline | self-supervised-learning | timeline |
| classical-trends | statistical-deep-learning | timeline |
| pac-bayes-trends | statistical-deep-learning | timeline |

## Adding a new figure

1. Write `src/<name>.py` (a plain Matplotlib script saving `figures/<name>.svg`;
   use `figlib.py` for the timeline/landscape archetypes if it fits).
2. Add `"<name>": "<blog-dir>"` to `FIGURES` in `build.py`.
3. `python figures/build.py <name>`.

> Kept separate from the site build (`python -m builder`), which does not need
> Matplotlib. The pre-commit hook does not regenerate figures.
