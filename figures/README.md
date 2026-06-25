# Blog figure generator

Reusable Matplotlib toolkit for the blog figures, matching the existing house
style (DejaVu Sans, `tab10` colours, despined axes, faint dotted grid,
~9.2x3.8in SVG).

## Files

- `figlib.py` -- the toolkit: shared style (`use_style`), `save`, and the two
  figure builders.
- `build.py` -- figure definitions + renderer. Each entry in `FIGURES` maps an
  output path to a builder.
- `examples/` -- rendered reference output (one of each archetype).

## Usage

```bash
pip install matplotlib            # only dependency
python figures/build.py           # render every figure to its path
python figures/build.py /tmp/out  # render under /tmp/out instead (preview)
```

## Archetypes

**`family_timeline(points, families, ...)`** -- scatter of methods over a year
axis; marker shape + colour keyed by "family"; per-point text labels; optional
dotted baseline reference lines. Used by `gp-family-timeline`,
`pac-bayes-trends`, `rl-method-timeline`, and the other `*-timeline` figures.

```python
families = {"deepgp": {"color": TAB10["green"], "marker": "D", "label": "deep-gp"}}
points   = [{"x": 2017, "y": 2.81, "family": "deepgp", "label": "DSVI 3L"}]
fig, ax  = family_timeline(points, families, title="...", ylabel="...",
                           invert_y=True, baselines=[{"y": 2.97, "text": "baseline"}])
```

**`landscape(points, bands, ...)`** -- 2D conceptual map with pastel horizontal
bands, labelled points, and an optional curved trend arrow. Used by
`inference-tractability-landscape` and `ot-feasibility-fidelity`.

```python
bands  = [{"ymin": 0.66, "ymax": 1.0, "color": BAND["green"], "label": "Exact posterior"}]
points = [{"x": 0.08, "y": 0.93, "label": "Conjugate Bayes"}]
fig, ax = landscape(points, bands, title="...", xlabel="...", ylabel="...",
                    arrow={"start": (0.1, 0.9), "end": (0.9, 0.2), "rad": 0.28})
```

## Adding a figure

1. Write a builder in `build.py` that returns `family_timeline(...)` /
   `landscape(...)` (or a custom plot using `use_style()`).
2. Register it in `FIGURES` with its output path
   (e.g. `blogs/<topic>/figures/<name>.svg`).
3. Run `python figures/build.py`.

The builders return `(fig, ax)`, so you can tweak the axes before saving for
anything the helpers don't cover.

> Note: these are kept separate from the site build (`python -m builder`), which
> does not need Matplotlib. Figures are regenerated only when you run
> `build.py`, and the pre-commit hook does not rebuild them.
