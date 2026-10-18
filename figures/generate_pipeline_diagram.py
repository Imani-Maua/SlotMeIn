"""
Pipeline diagram for SlotMeIn thesis.
Run from the figures/ directory: python generate_pipeline_diagram.py
Saves: pipeline_diagram.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(16, 5))
ax.set_xlim(0, 16)
ax.set_ylim(0, 5)
ax.axis('off')

BLUE   = '#00539C'
GREEN  = '#2E7D32'
ORANGE = '#E65100'
GREY   = '#455A64'
ARROW  = '#546E7A'

boxes = [
    (0.2,  1.3, 2.2, 2.4,  BLUE,   'Raw Data',
     'Covers (294 days)\nBookings (119,390)\nWeather (Budapest)\nHolidays (HU)'),
    (2.8,  1.3, 2.2, 2.4,  GREEN,  'EDA &\nOLS Regression',
     '$R^2 = 0.43$\n6 significant features\nTier thresholds\n(182 / 305 covers)'),
    (5.4,  1.3, 2.2, 2.4,  GREEN,  'Synthetic Data\nGeneration',
     'Row sampling\n+ real residuals\n$N = 2{,}000$ days\nKS $p = 0.408$'),
    (8.0,  1.3, 2.2, 2.4,  ORANGE, 'Classifier\nTraining',
     'RF / XGBoost\n/ LightGBM\nTemporal 70/15/15\nsplit'),
    (10.6, 1.3, 2.2, 2.4,  ORANGE, 'Tier\nPrediction',
     'Morning: RF 98.4\%\nAfternoon: LGBM\n92.9\%\nLOW/MED/HIGH'),
    (13.2, 1.3, 2.2, 2.4,  GREY,   'CP-SAT\nScheduler',
     'Labour-law hard\nconstraints\nWeighted objective\nFair assignments'),
]

for (x, y, w, h, colour, title, subtitle) in boxes:
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle='round,pad=0.05',
                          facecolor=colour, edgecolor='white',
                          linewidth=1.5, alpha=0.92, zorder=2)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h - 0.35, title,
            ha='center', va='top', fontsize=9.5, fontweight='bold',
            color='white', zorder=3)
    ax.text(x + w/2, y + h/2 - 0.15, subtitle,
            ha='center', va='center', fontsize=7.8,
            color='white', linespacing=1.5, zorder=3)

arrow_y = 2.5
for xi in [2.4, 5.0, 7.6, 10.2, 12.8]:
    ax.annotate('', xy=(xi + 0.4, arrow_y), xytext=(xi, arrow_y),
                arrowprops=dict(arrowstyle='->', color=ARROW,
                                lw=2.0, mutation_scale=20),
                zorder=4)

ax.text(8.0, 4.65,
        'SlotMeIn — AI-Powered Predictive Analytics Pipeline',
        ha='center', va='top', fontsize=13, fontweight='bold', color='#1a1a1a')

plt.tight_layout(pad=0.3)
plt.savefig('pipeline_diagram.png', dpi=180, bbox_inches='tight',
            facecolor='white')
print('Saved pipeline_diagram.png')
