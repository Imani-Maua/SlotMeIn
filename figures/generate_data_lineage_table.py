"""
Data lineage table for SlotMeIn thesis.
Run from the figures/ directory: python generate_data_lineage_table.py
Saves: data_lineage_table.png
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

rows = [
    # (Source, Records, Period, Role in thesis, Colour)
    ('Hotel Booking System\n(Budapest, anonymised)',
     '119,390 bookings\n→ daily occupancy\%',
     'Dec 2023 – Apr 2026',
     'Primary demand driver;\nOLS feature; classifier input',
     '#D0E8FF'),
    ('F\\&B Covers Ledger\n(anonymised)',
     '294 daily cover\ncounts (lunch + dinner)',
     'Jan 2024 – Oct 2024',
     'Ground-truth demand;\nOLS target; tier thresholds',
     '#D0F0D0'),
    ('Open-Meteo API\n(Budapest, lat 47.5°N)',
     '1,008 daily records\n(temp\\_mean, temp\\_max)',
     'Dec 2023 – Apr 2026',
     'Weather features;\nOLS + classifier input',
     '#FFF3CC'),
    ('Hungarian Public\nHoliday Calendar',
     '25 statutory holidays\n(2023 – 2026)',
     'Rolling',
     'is\\_special\\_day binary\nfeature; hard constraint',
     '#FFE0CC'),
    ('Row-sampling Synthesis\n(demand\\_model.ipynb)',
     '2,000 synthetic days\n(KS p = 0.408)',
     'Derived',
     'Classifier training set;\ncorrelation-preserving',
     '#EDD5F7'),
    ('Real Hotel Operations\n(train\\_tier\\_model.ipynb)',
     '1,676 labelled rows\n(840 unique dates)',
     'Dec 2023 – Apr 2026',
     'Final model evaluation;\ntemporal 70/15/15 split',
     '#F5D5D5'),
]

COL_WIDTHS = [0.22, 0.20, 0.18, 0.27, 0.13]
HEADERS    = ['Source', 'Volume', 'Period', 'Role', 'Colour Key']
COLOURS    = ['#D0E8FF', '#D0F0D0', '#FFF3CC', '#FFE0CC', '#EDD5F7', '#F5D5D5']

fig_h = 0.55 * (len(rows) + 1.5)
fig, ax = plt.subplots(figsize=(14, fig_h))
ax.axis('off')

n_cols = 4
x_starts = [0.0, 0.28, 0.50, 0.68]
col_w    = [0.28, 0.22, 0.18, 0.32]

header_labels = ['Source', 'Volume / Records', 'Coverage Period', 'Role in Analysis']
header_bg = '#2C3E50'
row_height = 0.12

# Header
for j, (x, w, label) in enumerate(zip(x_starts, col_w, header_labels)):
    rect = mpatches.FancyBboxPatch((x, 1 - row_height), w - 0.005, row_height,
                                   boxstyle='square,pad=0',
                                   facecolor=header_bg, edgecolor='white', linewidth=0.8,
                                   transform=ax.transAxes, clip_on=False)
    ax.add_patch(rect)
    ax.text(x + (w - 0.005) / 2, 1 - row_height / 2, label,
            ha='center', va='center', fontsize=9.5, fontweight='bold',
            color='white', transform=ax.transAxes)

for i, (src, vol, period, role, colour) in enumerate(rows):
    y_top = 1 - row_height * (i + 2)
    cells = [src, vol, period, role]
    for j, (x, w, cell) in enumerate(zip(x_starts, col_w, cells)):
        bg = colour if j == 0 else ('#FAFAFA' if i % 2 == 0 else '#F0F0F0')
        if j == 0:
            bg = colour
        rect = mpatches.FancyBboxPatch((x, y_top), w - 0.005, row_height,
                                       boxstyle='square,pad=0',
                                       facecolor=bg, edgecolor='#CCCCCC', linewidth=0.5,
                                       transform=ax.transAxes, clip_on=False)
        ax.add_patch(rect)
        ax.text(x + 0.01, y_top + row_height / 2, cell,
                ha='left', va='center', fontsize=8.0, color='#1a1a1a',
                transform=ax.transAxes, linespacing=1.35)

ax.text(0.5, 0.98, 'Data Lineage — SlotMeIn Training Pipeline',
        ha='center', va='top', fontsize=12, fontweight='bold',
        color='#1a1a1a', transform=ax.transAxes)

plt.tight_layout(pad=0.1)
bottom = 1 - row_height * (len(rows) + 2) - 0.02
fig.text(0.5, bottom,
         'Source colours reflect dataset origin: blue=bookings, green=covers, '
         'yellow=weather, orange=calendar, purple=synthetic, red=real eval set.',
         ha='center', va='top', fontsize=7.5, color='#555555')

plt.savefig('data_lineage_table.png', dpi=180, bbox_inches='tight', facecolor='white')
print('Saved data_lineage_table.png')
