import os
import json
import traceback
import pathlib
from collections import namedtuple
from multiprocessing import Pool

import zephyrus_sc2_parser
from zephyrus_sc2_parser.game import GameObj

# Max game length up to where player selections count (real-time minutes)
MAX_LENGTH = 15

command_buildings = [
    'Nexus',
    'CommandCenter',
    'OrbitalCommand',
    'PlanetaryFortress',
    'Hatchery',
    'Lair',
    'Hive',
]

# ~7sec. PlayerStatsEvents occur at this interval throughout the game
TICK_SIZE = 160

PlayerTuple = namedtuple('PlayerTuple', ['name', 'race'])


def handle_replay(path, player_names=None, identifiers=None):
    parsed_ticks = {}

    replay = zephyrus_sc2_parser.parse_replay(path, local=True, creep=False)

    for player in replay.players.values():
        tick_times = {
            'economy': [],
            'army': [],
            'infra': [],

            # new categories
            'creep': [],
            'queen': [],
        }
        # remove last selection since it technically has no end
        selections = player.selections[:-1]
        selections.sort(key=lambda x: x['start'])

        # list of selections in ~7sec intervals throughout the game
        ticks = [[]]

        # current tick
        tick = 1
        for s in selections:
            # as long as the selection ends before the end of the tick
            # we count it as part of the tick
            # tick * TICK_SIZE = upper gameloop limit for the current tick
            if s['end'] <= tick * TICK_SIZE:
                # add to current tick
                ticks[tick - 1].append(s)
            else:
                # create a new tick
                ticks.append([s])
                tick += 1

        for count, t in enumerate(ticks):
            all_times = []
            selection_times = {
                'economy': [],
                'army': [],
                'infra': [],

                # new categories
                'creep': [],
                'queen': [],
            }

            # iterating through all selections in the current tick
            for s in t:
                # if there are any objects of a group (economy/army/infra) in a selection
                # it counts for that groups. multiple groups can be counted in a single selection
                seen_group = set()
                diff = s['end'] - s['start']
                all_times.append(diff)

                # Skip events that are over max length
                if MAX_LENGTH is not None and s['start'] > MAX_LENGTH * 22.4 * 60:
                    continue

                # check the selection for each group
                # if we haven't already counted it for a group, record the selection length
                for obj in s['selection']:
                    if obj.name == 'Egg' or obj.name == 'Larva':
                        continue
                    if 'Creep' in obj.name:
                        if 'creep' not in seen_group:
                            selection_times['creep'].append(diff)
                            seen_group.add('creep')
                    elif obj.name == 'Queen':
                        if 'queen' not in seen_group:
                            selection_times['queen'].append(diff)
                            seen_group.add('queen')
                    elif (obj.name in command_buildings or GameObj.WORKER in obj.type or obj.name == 'Larva'):
                        if 'economy' not in seen_group:
                            selection_times['economy'].append(diff)
                            seen_group.add('economy')
                    elif (GameObj.BUILDING in obj.type or obj.name == 'Queen' or 'Overlord' in obj.name or 'Overseer' in obj.name):
                        if 'infra' not in seen_group:
                            selection_times['infra'].append(diff)
                            seen_group.add('infra')
                    elif GameObj.UNIT in obj.type:
                        if 'army' not in seen_group:
                            selection_times['army'].append(diff)
                            seen_group.add('army')

            total_percentage = 0
            selection_percentages = {}

            # iterate through all selection times for all groups
            for n, v in selection_times.items():
                # if no selections for a particular group, skip it
                if not v:
                    continue

                # total selection time in seconds for the current group
                vt = sum(v) / 22.4

                # total selection time in seconds
                all_sec = sum(all_times) / 22.4

                # percentage of time the current group was selected
                percent = (vt / all_sec) * 100
                total_percentage += percent
                selection_percentages[n] = percent

            for n, v in selection_percentages.items():
                tick_times[n].append({
                    'tick': (count + 1) * TICK_SIZE,
                    'percent': v,
                })

        parsed_ticks[PlayerTuple(player.name.lower(), player.race.lower())] = tick_times
    return parsed_ticks


def sum_ticks(file_path: str) -> dict:
    """ Sums up selection in ticks, and returns the total sum for given replay (per player, per type)
    It's in percent, so for actual time, it would need to be *tick_lenght/100."""
    try:
        parsed_ticks = handle_replay(file_path)
    except zephyrus_sc2_parser.exceptions.ReplayDecodeError:
        print(f"Error: replay could not be decoded {file_path}")
        return
    except Exception:
        print(traceback.format_exc())
        return

    league = pathlib.Path(file_path).parent.name
    out = []
    for player in parsed_ticks:
        player_data = {'league': league, 'race': player.race}
        for type in parsed_ticks[player]:
            for datapoint in parsed_ticks[player][type]:
                player_data[type] = player_data.get(type, 0) + datapoint['percent']
        out.append(player_data)

    return out


if __name__ == '__main__':
    # Save replay paths
    replays = set()
    for root, directories, files in os.walk('replays'):
        for file in files:
            if file.endswith('.SC2Replay'):
                replays.add(os.path.join(root, file))

    # Parse replays
    with Pool() as p:
        results = p.map(sum_ticks, replays)

    # Go over results, sum up data for given league
    out = dict()
    parsed_replays = 0
    for game in results:

        if game is None:
            continue

        parsed_replays += 1

        # Iterate over players in each game
        for player in game:
            league = player['league']
            race = player['race']

            # Create structure if it's note there out-race-league-data
            if race not in out:
                out[race] = dict()
            if not league in out[race]:
                out[race][league] = dict()

            # Count games
            out[race][league]['games'] = out[race][league].get('games', 0) + 1

            # Fill data
            for item in player:
                if item in {'race', 'league'}:
                    continue
                out[race][league][item] = out[race][league].get(item, 0) + player[item]

    with open(f'results{MAX_LENGTH if MAX_LENGTH is not None else ""}.json', 'w') as f:
        json.dump(out, f, indent=2)

    print(f"{parsed_replays} replays analyzed and data saved!")