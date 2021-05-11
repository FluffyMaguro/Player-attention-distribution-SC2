import os
import json
import traceback
import pathlib
from multiprocessing import Pool

import zephyrus_sc2_parser


def get_game_length(path):
    try:
        replay = zephyrus_sc2_parser.parse_replay(path, local=True, creep=False)
        league = pathlib.Path(path).parent.name
        return (league, replay.metadata['game_length'])
    except Exception:
        traceback.print_exc()


if __name__ == '__main__':
    from pprint import pprint
    # Save replay paths
    replays = set()
    for root, directories, files in os.walk('replays'):
        for file in files:
            if file.endswith('.SC2Replay'):
                replays.add(os.path.join(root, file))

    # Parse replays
    with Pool() as p:
        results = p.map(get_game_length, replays)

    # Go over results, sum up data for given league
    out = dict()
    parsed_replays = 0
    for game in results:

        if game is None:
            continue

        league, length = game

        parsed_replays += 1
        if league not in out:
            out[league] = []
        out[league].append(length)

    print(f"{parsed_replays} replays analyzed and data saved!")

    with open('game_lengths.json', 'w') as f:
        json.dump(out, f, indent=2)
