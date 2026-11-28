"""
Pareto chart of the confirmed defects by category.

    python reports/api/make_pareto.py      -> reports/api/pareto.png

The categories are assigned in docs/defects/pareto.md; keep the two in step.
"""
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import MaxNLocator, PercentFormatter  # noqa: E402

DEFECTS = {
    'N1': 'Error reporting',
    'N2': 'Input validation',
    'N3': 'Error reporting',
    'N4': 'Idempotency / repeats',
    'N5': 'Input validation',
    'N6': 'Input validation',
    'N7': 'Input validation',
    'N8': 'Error reporting',
}


def main():
    counts = {}
    for category in DEFECTS.values():
        counts[category] = counts.get(category, 0) + 1
    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    total = sum(values)
    cumulative, running = [], 0
    for v in values:
        running += v
        cumulative.append(100 * running / total)

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    bars = ax.bar(labels, values, color='#3b6ea5', width=0.6)
    ax.bar_label(bars, padding=2)
    ax.set_ylabel('Defects')
    ax.set_ylim(0, max(values) + 1)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_title(f'Defects by category, N1–N8 (Sale + Void sale, n = {total})')
    ax.spines[['top']].set_visible(False)

    ax2 = ax.twinx()
    ax2.plot(labels, cumulative, color='#c0392b', marker='o')
    for x, y in zip(labels, cumulative):
        ax2.annotate(f'{y:.0f}%', (x, y), textcoords='offset points', xytext=(14, -4),
                     ha='left', color='#c0392b',
                     bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none'))
    ax2.axhline(80, color='#999999', linestyle='--', linewidth=0.8)
    ax2.set_ylim(0, 110)
    ax2.yaxis.set_major_formatter(PercentFormatter())
    ax2.set_ylabel('Cumulative %')
    ax2.spines[['top']].set_visible(False)

    fig.tight_layout()
    out = Path(__file__).with_name('pareto.png')
    fig.savefig(out, metadata={'Software': None})
    for label, value, cum in zip(labels, values, cumulative):
        print(f'{label}: {value} ({cum:.1f}% cumulative)')
    print(f'-> {out}')


if __name__ == '__main__':
    main()
