import json
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

with open('results15.json', 'r') as f:
    data = json.load(f)

races = ['terran', 'protoss', 'zerg']
leagues = ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster', 'pro']
labels = ['army', 'economy', 'infrastructure']
zlabels = labels + ['creep', 'queen']

fig, axis = plt.subplots(1, 3, dpi=100, figsize=(20, 8))

for i, race in enumerate(races):
    army = []
    economy = []
    infrastructure = []
    creep = []
    queen = []

    # Create lists from the data
    for league in leagues:
        total = 0
        for t in data[race][league]:
            if t != 'games':
                total += data[race][league][t]

        # Normalize to total time spent
        army.append(data[race][league]['army'] / total)
        economy.append(data[race][league]['economy'] / total)
        infrastructure.append(data[race][league]['infra'] / total)

        # More data for Zerg
        if race == 'zerg':
            creep.append(data[race][league]['creep'] / total)
            queen.append(data[race][league]['queen'] / total)

    # Plot data
    if race == 'zerg':
        axis[i].stackplot([l.capitalize() for l in leagues], army, economy, infrastructure, creep, queen, labels=[l.capitalize() for l in zlabels])
    else:
        axis[i].stackplot([l.capitalize() for l in leagues], army, economy, infrastructure, labels=[l.capitalize() for l in labels])

    # Add text for army control
    for idx, value in enumerate(army):
        axis[i].text(idx, value, f'{value:.1%}', horizontalalignment='center')

    # Inverse the order in legend, and set its position
    handles, labels = axis[i].get_legend_handles_labels()
    axis[i].legend(handles[::-1], labels[::-1], loc='upper center')

    # Labels and titles
    axis[i].set_xlabel('Player skill')
    axis[i].set_ylabel('Attention usage')
    axis[i].set_title(race.capitalize(), fontsize=14)
    axis[i].yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))

fig.suptitle("How players distribute their attention in-game\n(StarCraft II) (first 15 real-time minutes)", fontsize=16)
plt.tight_layout(h_pad=2)
plt.subplots_adjust(top=0.88)
plt.savefig('result15.png')