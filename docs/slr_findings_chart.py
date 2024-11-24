import matplotlib.pyplot as plt
from matplotlib.patches import Patch

data = [
    {'type': 'Top Journal Paper', 'count': 6, 'subset_grey_literature': 0},
    {'type': 'Journal Paper', 'count': 30, 'subset_grey_literature': 0},
    {'type': 'Buch', 'count': 1, 'subset_grey_literature': 0},
    {'type': 'Pressemitteilung', 'count': 5, 'subset_grey_literature': 5},
    {'type': 'Zeitschrift', 'count': 6, 'subset_grey_literature': 3},
    {'type': 'White Paper/ Herstelldokument', 'count': 6, 'subset_grey_literature': 4},
]

types = [entry['type'] for entry in data]
counts = [entry['count'] for entry in data]
grey_lit_counts = [entry['subset_grey_literature'] for entry in data]

plt.figure(figsize=(10, 6))
bar_width = 0.6 

for i, (doc_type, count, grey_lit) in enumerate(zip(types, counts, grey_lit_counts)):
    # normal bar
    plt.bar(doc_type, count, color='white', edgecolor='black', width=bar_width)
    
    # grey bar
    if grey_lit > 0:
        plt.bar(doc_type, grey_lit, color='white', edgecolor='black', width=bar_width, hatch='//')

    # sum count
    plt.text(
        i, 
        count + 0.2, 
        str(count),
        ha='center', 
        va='bottom', 
        fontsize=10
    )

# legend
plt.title('SLR - Funde', fontsize=14)
plt.xlabel('Dokumenttyp', fontsize=12)
plt.ylabel('Anzahl', fontsize=12)
plt.grid(axis='y', linestyle='--', color='gray', alpha=0.7)
plt.xticks(rotation=30, ha='right', fontsize=10)
legend_elements = [
    Patch(facecolor='white', edgecolor='black', label='Graue Literatur', hatch='//'),
]
plt.legend(handles=legend_elements, fontsize=10, loc='upper left')

plt.tight_layout()
plt.show()
