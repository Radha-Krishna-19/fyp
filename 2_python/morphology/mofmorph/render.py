import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

COLORS = {"{111}+": "#E45756", "{111}-": "#F4A6A6", "{211}+": "#B279A2", "{211}-": "#D9B8D0", "{100}": "#4C78A8", "{111}": "#E45756", "{110}": "#54A24B", "{211}": "#B279A2",
          "{310}": "#F2CF5B", "{311}": "#9D755D", "{221}": "#FF9DA6", "rough": "#D9D9D9"}


def draw(ax, shape, title=None, view=(22, 35)):
    for f in shape.faces:
        c = COLORS.get(f["tag"], "#BAB0AC")
        lw = 0.0 if f["tag"] == "rough" else 0.6
        ax.add_collection3d(Poly3DCollection([f["poly"]], facecolor=c, edgecolor="k", linewidth=lw, alpha=0.95))
    r = np.abs(shape.V).max()
    for s in (ax.set_xlim, ax.set_ylim, ax.set_zlim):
        s(-r, r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(*view); ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=9)


def row(shapes, titles, path, caption=None, size=2.5):
    fig = plt.figure(figsize=(size * len(shapes), size + 0.6))
    for i, (s, t) in enumerate(zip(shapes, titles)):
        draw(fig.add_subplot(1, len(shapes), i + 1, projection="3d"), s, t)
    if caption:
        fig.text(0.5, 0.01, caption, ha="center", fontsize=8.5)
    plt.savefig(path, dpi=200, bbox_inches="tight"); plt.close(fig)
