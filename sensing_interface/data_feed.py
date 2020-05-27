import json
import os
import re
import unicodedata

import numpy as np
from neo4j import GraphDatabase

from kg_access.satellites import retrieve_available_satellites


def slugify(value):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)


def generate_fake_timeline(variance, access_intervals, fake_data_generator):
    time_array = np.array([])
    data_array = np.array([])
    changes = fake_data_generator["changes"]
    states = fake_data_generator["states"]
    rng_generator = np.random.default_rng()
    for idx, rise_set_time in enumerate(access_intervals["timeArray"]):
        if rise_set_time["isRise"]:
            next_second = np.math.ceil(rise_set_time["time"])
            last_second = np.math.ceil(access_intervals["timeArray"][idx+1]["time"])
            current_time_array = np.arange(next_second, last_second, 1)
            current_data_array = np.zeros(current_time_array.size)

            # Set up generator
            current_state = 0
            last_change = 0
            next_change = changes[0]
            for idx, change in enumerate(changes):
                if next_second > change:
                    current_state += 1
                    last_change = change
                    if idx < len(changes) - 1:
                        next_change = changes[idx+1]
                    else:
                        next_change = 604800
                else:
                    break

            # Sample data for the interval
            for idx, time in enumerate(current_time_array):
                if current_state < len(changes) and time == changes[current_state]:
                    current_state += 1
                    last_change = time
                    if current_state < len(changes):
                        next_change = changes[current_state]
                    else:
                        next_change = 604800
                next_num = generate_num(states[current_state], rng_generator, time - last_change, next_change - last_change, variance)
                current_data_array[idx] = next_num

            # Concatenate with main arrays
            time_array = np.concatenate((time_array, current_time_array))
            data_array = np.concatenate((data_array, current_data_array))

    return time_array, data_array


def generate_num(state, rng, diff, length_slope, var):
    if state["type"] == "stable":
        return state["mean"] + rng.normal(0, var)
    elif state["type"] == "slope":
        slope = float(state["end"] - state["start"])/length_slope
        current_num = state["start"] + slope*diff + rng.normal(0, var)
        return current_num
    else:
        return 0.


def generate_fake_data(mission_id, access_intervals):
    # For all data, we assume second-by-second collection for a week (24*7*3600 = 604800 data points)
    # We only save the data points for the times when the target is visible for each instrument
    # Furthermore, the volcano eruption starts happening at 3AM on the third day (datapoint 180000)
    # The peak of the eruption is at 8AM (dp 198000)
    # Eruption stops fifth day 12PM (dp 3852000)
    # Data back to nominal after 12 hours (dp 428400)

    fake_data_generators = {"Mauna Loa": {}}
    # Generate TIR data (radiance @ 11 um)
    state_changes = [180000, 198000, 385200, 428200]
    states = [{"type": "stable", "mean": 10},
              {"type": "slope", "start": 10, "end": 70},
              {"type": "stable", "mean": 70},
              {"type": "slope", "start": 70, "end": 10},
              {"type": "stable", "mean": 10}]
    fake_data_generators["Mauna Loa"]["Land surface temperature"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate SWIR data (radiance @ 4 um)
    state_changes = [194400, 208800, 360000, 385200]
    states = [{"type": "stable", "mean": 0.},
              {"type": "slope", "start": 0., "end": 10.},
              {"type": "stable", "mean": 10.},
              {"type": "slope", "start": 10., "end": 0.},
              {"type": "stable", "mean": 0.}]
    fake_data_generators["Mauna Loa"]["Fire temperature"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate Plume data (prob of ash plume)
    state_changes = [180000, 198000, 385200, 428200]
    states = [{"type": "stable", "mean": 0.},
              {"type": "slope", "start": 0., "end": 0.85},
              {"type": "stable", "mean": 0.85},
              {"type": "slope", "start": 0.85, "end": 0.},
              {"type": "stable", "mean": 0}]
    fake_data_generators["Mauna Loa"]["Cloud type"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate SAR data (mean displacement of terrain in mm)
    state_changes = [180000, 198000, 385200, 428200]
    states = [{"type": "slope", "start": 0., "end": 20.},
              {"type": "slope", "start": 20., "end": 80.},
              {"type": "slope", "start": 80., "end": 30.},
              {"type": "slope", "start": 30., "end": 0.},
              {"type": "stable", "mean": 0.}]
    fake_data_generators["Mauna Loa"]["Land surface topography"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate SO2 data (Dobson units)
    state_changes = [180000, 198000, 385200, 428200]
    states = [{"type": "stable", "mean": 0.5},
              {"type": "slope", "start": 0.5, "end": 2.1},
              {"type": "stable", "mean": 2.1},
              {"type": "slope", "start": 2.1, "end": 0.5},
              {"type": "stable", "mean": 0.5}]
    fake_data_generators["Mauna Loa"]["Atmospheric Chemistry - SO2 (column/profile)"] = {
        "changes": state_changes,
        "states": states
    }

    cwd = os.getcwd()
    int_path = os.path.join(cwd, "int_files")
    data_streams_path = os.path.join(int_path, "data_streams")
    if not os.path.exists(data_streams_path):
        os.makedirs(data_streams_path)
    data_location_path = os.path.join(int_path, "data_location.json")

    # Connect to database, open session
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    with driver.session() as session:
        satellites = retrieve_available_satellites(mission_id, session)
        data_locations_json = {}
        for satellite in satellites:
            if satellite["name"] in access_intervals["output"]:
                data_locations_json[satellite["name"]] = {}
                for instrument in satellite["sensors"]:
                    data_locations_json[satellite["name"]][instrument["name"]] = {}
                    for observation in instrument["characteristics"]:
                        data_locations_json[satellite["name"]][instrument["name"]][observation] = {}
                        for location in access_intervals["output"][satellite["name"]][instrument["name"]]:
                            observation_name = slugify(satellite["name"] + "__" + instrument["name"] + "__" + location + "__" + observation)
                            data_locations_json[satellite["name"]][instrument["name"]][observation][location] = observation_name + ".npy"
                            array_path = os.path.join(data_streams_path, observation_name + ".npy")
                            time_array, data_array = generate_fake_timeline(instrument["characteristics"][observation]["Q"],
                                                                            access_intervals["output"][satellite["name"]][instrument["name"]][location],
                                                                            fake_data_generators[location][observation])
                            with open(array_path, 'wb') as f:
                                np.save(f, time_array)
                                np.save(f, data_array)
                            print(observation_name)

    with open(data_location_path, 'w', encoding='utf8') as data_locations_file:
        json.dump(data_locations_json, data_locations_file)
