import json, os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(H, 'spectrum_vs_shape_MOF5.json')))
fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
cx = [r['diameter'] for r in d['cubes']]; cy = [r['width_mean'] for r in d['cubes']]
ax[0].plot(cx, cy, 'o-', color='#555', label='cubes, 2 to 6 cells per side')
xx = np.linspace(min(cx), 80, 50); t = d['trend']
ax[0].plot(xx, t['a'] + t['b'] * np.log(xx), '--', color='#999', label='cube trend, extended')
col = {'cube 4x4x4': '#1f4e9c', 'slab 8x4x2': '#2e8b57', 'plate 8x8x1': '#c27c0e', 'rod 16x2x2': '#b91c1c'}
for r in d['shapes']:
    ax[0].errorbar(r['diameter'], r['width_mean'], yerr=r['width_sd'], fmt='s', color=col[r['label']], ms=8, label=r['label'])
ax[0].set_xlabel('diameter of the particle graph (steps)'); ax[0].set_ylabel('spectrum width  Δα')
ax[0].set_title('Same size trend? No: plates and rods fall below it', fontsize=10); ax[0].legend(fontsize=7.5, frameon=False)
lab = [r['label'] for r in d['shapes']]; val = [r['width_mean'] for r in d['shapes']]
ax[1].bar(range(len(lab)), val, color=[col[l] for l in lab], yerr=[r['width_sd'] for r in d['shapes']], capsize=3)
ax[1].set_xticks(range(len(lab))); ax[1].set_xticklabels([l.replace(' ', '\n') for l in lab], fontsize=8)
ax[1].set_ylim(1.2, 1.8); ax[1].set_ylabel('spectrum width  Δα')
ax[1].set_title('64 unit cells (2048 blocks) in every shape', fontsize=10)
for s in ('top', 'right'):
    for a in ax: a.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(H, 'spectrum_vs_shape_figure.png'), dpi=150)
