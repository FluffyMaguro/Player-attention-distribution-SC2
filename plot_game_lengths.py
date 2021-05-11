import json
import matplotlib.pyplot as plt
from statistics import mean
from matplotlib.ticker import FuncFormatter
import time

with open('game_lengths.json', 'r') as f:
    data = json.load(f)

# Calculate averages
averages = dict()
for league in data:
    averages[league] = mean(data[league])

# Plot main data
plt.violinplot(list(data.values()))

# Plot averages
for i, league in enumerate(averages):
    avg = time.strftime('%M:%S', time.gmtime(averages[league]))
    plt.text(i + 1, averages[league], avg, horizontalalignment='center')

plt.title('Distribution of game lengths')
plt.ylim(0,3600)
plt.xticks(list(range(1, 9)), [i.capitalize() for i in list(data.keys())], rotation=30)
plt.yticks(list(range(0, 3600, 600)), [time.strftime('%H:%M:%S', time.gmtime(i)) for i in list(range(0, 3600, 600))])
plt.ylabel('Game length')

# plt.show()
plt.tight_layout()
plt.savefig('game_lengths.png')