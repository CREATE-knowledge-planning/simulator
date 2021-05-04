import json
import os
import re
import shutil
import unicodedata
import random
from pathlib import Path

import numpy as np
from neo4j import GraphDatabase
from kg_access.obtain_driver import get_neo4j_driver

from kg_access.satellites import retrieve_available_satellites
from mission_creation.kg_additions import add_volcano_mission
from orekit_interface.access_intervals import obtain_access_times, read_access_times


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


def generate_volcano_simulation(mission_id, access_intervals, eruption_length, eruption_start, location, speed, size,
                        max_tir_temperature, max_swir_temperature, max_ash_cloud, max_terrain_displacement,
                        max_so2_levels, simulation_information_path, data_streams_path):
    # For all data, we assume second-by-second collection for a week (24*7*3600 = 604800 data points)
    # We only save the data points for the times when the target is visible for each instrument
    # Furthermore, the volcano eruption starts happening at 3AM on the third day (datapoint 180000)
    # The peak of the eruption is at 8AM (dp 198000)
    # Eruption stops fifth day 12PM (dp 3852000)
    # Data back to nominal after 12 hours (dp 428400)

    fake_data_generators = {location: {}}
    eruption_start_dp = eruption_start*3600
    eruption_max_dp = eruption_start_dp + speed*eruption_length*3600
    eruption_slope_dp = eruption_start_dp + 0.9*eruption_length*3600
    eruption_end_dp = eruption_start_dp + eruption_length*3600
    # Generate TIR data (radiance @ 11 um)
    state_changes = [eruption_start_dp, eruption_max_dp, eruption_slope_dp, eruption_end_dp]
    states = [{"type": "stable", "mean": 10.},
              {"type": "slope", "start": 10., "end": max_tir_temperature},
              {"type": "stable", "mean": max_tir_temperature},
              {"type": "slope", "start": max_tir_temperature, "end": 10.},
              {"type": "stable", "mean": 10.}]
    fake_data_generators[location]["Land surface temperature"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate SWIR data (radiance @ 4 um)
    state_changes = [eruption_start_dp, eruption_max_dp, eruption_slope_dp, eruption_end_dp]
    states = [{"type": "stable", "mean": 0.},
              {"type": "slope", "start": 0., "end": max_swir_temperature},
              {"type": "stable", "mean": max_swir_temperature},
              {"type": "slope", "start": max_swir_temperature, "end": 0.},
              {"type": "stable", "mean": 0.}]
    fake_data_generators[location]["Fire temperature"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate Plume data (prob of ash plume)
    state_changes = [eruption_start_dp, eruption_max_dp, eruption_slope_dp, eruption_end_dp]
    states = [{"type": "stable", "mean": 0.},
              {"type": "slope", "start": 0., "end": max_ash_cloud},
              {"type": "stable", "mean": max_ash_cloud},
              {"type": "slope", "start": max_ash_cloud, "end": 0.},
              {"type": "stable", "mean": 0}]
    fake_data_generators[location]["Cloud type"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate SAR data (mean displacement of terrain in mm)
    state_changes = [eruption_start_dp, eruption_max_dp, eruption_slope_dp, eruption_end_dp]
    states = [{"type": "slope", "start": 0., "end": 20.},
              {"type": "slope", "start": 20., "end": max_terrain_displacement},
              {"type": "slope", "start": max_terrain_displacement, "end": 30.},
              {"type": "slope", "start": 30., "end": 0.},
              {"type": "stable", "mean": 0.}]
    fake_data_generators[location]["Land surface topography"] = {
        "changes": state_changes,
        "states": states
    }

    # Generate SO2 data (Dobson units)
    state_changes = [eruption_start_dp, eruption_max_dp, eruption_slope_dp, eruption_end_dp]
    states = [{"type": "stable", "mean": 0.5},
              {"type": "slope", "start": 0.5, "end": max_so2_levels},
              {"type": "stable", "mean": max_so2_levels},
              {"type": "slope", "start": max_so2_levels, "end": 0.5},
              {"type": "stable", "mean": 0.5}]
    fake_data_generators[location]["Atmospheric Chemistry - SO2 (column/profile)"] = {
        "changes": state_changes,
        "states": states
    }

    # Connect to database, open session
    driver = get_neo4j_driver()

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
                            if access_intervals["output"][satellite["name"]][instrument["name"]][location]["timeArray"]:
                                observation_name = slugify(satellite["name"] + "__" + instrument["name"] + "__" + location + "__" + observation)
                                data_locations_json[satellite["name"]][instrument["name"]][observation][location] = observation_name + ".npy"
                                array_path = data_streams_path / f"{observation_name}.npy"
                                #time_array, data_array = generate_fake_timeline(instrument["characteristics"][observation]["Q"],
                                #                                                access_intervals["output"][satellite["name"]][instrument["name"]][location],
                                #                                                fake_data_generators[location][observation])
                                # with open(array_path, 'wb') as f:
                                #     np.save(f, time_array)
                                #     np.save(f, data_array)
                                print(observation_name)

    observable_properties = ["Land surface temperature", "Fire temperature", "Cloud type" , "Land surface topography"]
    with simulation_information_path.open('w', encoding='utf8') as simulation_information_file:
        simulation_information_json = {
            "mission_id": mission_id,
            "length": eruption_length,
            "start": eruption_start,
            "location": location,
            "speed": speed,
            "size": size,
            "max_tir_temperature": max_tir_temperature,
            "max_swir_temperature": max_swir_temperature,
            "max_ash_cloud": max_ash_cloud,
            "max_terrain_displacement": max_terrain_displacement,
            "max_so2_levels": max_so2_levels,
            "data_locations": data_locations_json,
            "observable_properties": observable_properties
        }
        json.dump(simulation_information_json, simulation_information_file)


def generate_volcano_simulations(quantity, event_fraction):
    int_path = Path("./int_files")
    simulations_path = int_path / "simulations"
    simulations_path.mkdir(parents=True, exist_ok=True)
    accesses_path = int_path / "accesses"

    eruption_length_range = [12., 120.]  # hours
    eruption_start_range = [0., 168.]  # hours since beginning of simulation
    location_range = ["Kilauea", "Etna", "Piton de la Fournaise", "Stromboli", "Merapi",
                "Erta Ale", "Ol Doinyo Lengai", "Mount Unzen", "Mount Yasur", "Ambrym"]
    speed_range = [0.1, 0.5]  # fraction of time until max eruption
    size_range = [200., 2000.]  # meter radius
    max_tir_temperature_range = [50., 80.]
    max_swir_temperature_range = [5., 15.]
    max_ash_cloud_range = [0.5, 0.9]
    max_terrain_displacement_range = [50., 150.]
    max_so2_levels_range = [1.0, 3.0]

    # For each simulation, sample a value for each parameter, create a simulation, save it under int_files
    for sim_number in range(quantity):
        # Create paths
        simulation_path = simulations_path / f"simulation_{sim_number}"
        if simulation_path.exists():
            shutil.rmtree(simulation_path)
        simulation_path.mkdir(parents=True, exist_ok=True)

        simulation_information_path = simulation_path / "simulation_information.json"
        data_streams_path = simulation_path / "data_streams"

        # Sample values
        eruption_length = random.uniform(*eruption_length_range)
        eruption_start = random.uniform(*eruption_start_range)
        location = random.choice(location_range)
        speed = random.uniform(*speed_range)
        size = random.uniform(*size_range)
        max_tir_temperature = random.uniform(*max_tir_temperature_range)
        max_swir_temperature = random.uniform(*max_swir_temperature_range)
        max_ash_cloud = random.uniform(*max_ash_cloud_range)
        max_terrain_displacement = random.uniform(*max_terrain_displacement_range)
        max_so2_levels = random.uniform(*max_so2_levels_range)

        # Create a mission in the KG
        mission_id = add_volcano_mission(location)

        # Generate accesses if not already there
        access_path = accesses_path / f"{location}.json"
        if not access_path.exists():
            access_times = obtain_access_times(mission_id)
        else:
            access_times = read_access_times(location)

        # Create simulation
        generate_volcano_simulation(mission_id, access_times, eruption_length, eruption_start, location, speed, size,
                            max_tir_temperature, max_swir_temperature, max_ash_cloud, max_terrain_displacement,
                            max_so2_levels, simulation_information_path, data_streams_path)


def generate_hurricane_simulation(mission_id, hurricane_length, hurricane_start, location, speed, size,
                                  max_wind_speed, max_sea_temp, max_cloud, simulation_information_path):
    observable_properties = ["Wind speed over sea surface (horizontal)", "Sea surface temperature", "Cloud imagery"]
    with simulation_information_path.open('w', encoding='utf8') as simulation_information_file:
        simulation_information_json = {
            "mission_id": mission_id,
            "length": hurricane_length,
            "start": hurricane_start,
            "location": location,
            "speed": speed,
            "size": size,
            "max_wind_speed": max_wind_speed,
            "max_sea_temp": max_sea_temp,
            "max_cloud": max_cloud,
            "observable_properties": observable_properties
        }
        json.dump(simulation_information_json, simulation_information_file)


def generate_hurricane_simulations(quantity, event_fraction):
    int_path = Path("./int_files")
    simulations_path = int_path / "simulations"
    simulations_path.mkdir(parents=True, exist_ok=True)
    accesses_path = int_path / "accesses"

    eruption_length_range = [12., 120.]  # hours
    eruption_start_range = [0., 168.]  # hours since beginning of simulation
    location_range = ["Atlantic1", "Atlantic2", "Atlantic3", "Atlantic4", "Atlantic5",
                      "Pacific1", "Pacific2", "Pacific3", "Pacific4", "Pacific5"]
    speed_range = [0.1, 0.5]  # fraction of time until max eruption
    size_range = [200., 2000.]  # meter radius
    max_wind_speed_range = [50., 80.]
    max_sea_temp_range = [5., 15.]
    max_cloud_range = [0.5, 0.9]

    # For each simulation, sample a value for each parameter, create a simulation, save it under int_files
    for sim_number in range(quantity):
        # Create paths
        simulation_path = simulations_path / f"simulation_{sim_number}"
        if simulation_path.exists():
            shutil.rmtree(simulation_path)
        simulation_path.mkdir(parents=True, exist_ok=True)

        simulation_information_path = simulation_path / "simulation_information.json"
        data_streams_path = simulation_path / "data_streams"

        # Sample values
        eruption_length = random.uniform(*eruption_length_range)
        eruption_start = random.uniform(*eruption_start_range)
        location = random.choice(location_range)
        speed = random.uniform(*speed_range)
        size = random.uniform(*size_range)
        max_wind_speed = random.uniform(*max_wind_speed_range)
        max_sea_temp = random.uniform(*max_sea_temp_range)
        max_cloud = random.uniform(*max_cloud_range)
        # Create a mission in the KG
        mission_id = add_volcano_mission(location)

        # Generate accesses if not already there
        access_path = accesses_path / f"{location}.json"
        if not access_path.exists():
            access_times = obtain_access_times(mission_id)
        else:
            access_times = read_access_times(location)

        # Create simulation
        generate_hurricane_simulation(mission_id, eruption_length, eruption_start, location, speed, size,
                            max_wind_speed, max_sea_temp, max_cloud, simulation_information_path)


def generate_flood_simulation(mission_id, hurricane_length, hurricane_start, location, speed, size,
                                  max_soil_moisture, max_precipitation, max_land, simulation_information_path):
    observable_properties = ["Soil moisture at the surface", "Precipitation Profile (liquid or solid)", "Land surface imagery"]
    with simulation_information_path.open('w', encoding='utf8') as simulation_information_file:
        simulation_information_json = {
            "mission_id": mission_id,
            "length": hurricane_length,
            "start": hurricane_start,
            "location": location,
            "speed": speed,
            "size": size,
            "max_soil_moisture": max_soil_moisture,
            "max_precipitation": max_precipitation,
            "max_land": max_land,
            "observable_properties": observable_properties
        }
        json.dump(simulation_information_json, simulation_information_file)


def generate_flood_simulations(quantity, event_fraction):
    int_path = Path("./int_files")
    simulations_path = int_path / "simulations"
    simulations_path.mkdir(parents=True, exist_ok=True)
    accesses_path = int_path / "accesses"

    eruption_length_range = [12., 120.]  # hours
    eruption_start_range = [0., 168.]  # hours since beginning of simulation
    location_range = ["India", "Bangladesh", "Texas", "Italy", "Brazil"]
    speed_range = [0.1, 0.5]  # fraction of time until max eruption
    size_range = [200., 2000.]  # meter radius
    max_soil_moisture_range = [80., 99.]
    max_precipitation_range = [200., 300.]
    max_land_range = [0.5, 0.9]

    # For each simulation, sample a value for each parameter, create a simulation, save it under int_files
    for sim_number in range(quantity):
        # Create paths
        simulation_path = simulations_path / f"simulation_{sim_number}"
        if simulation_path.exists():
            shutil.rmtree(simulation_path)
        simulation_path.mkdir(parents=True, exist_ok=True)

        simulation_information_path = simulation_path / "simulation_information.json"
        data_streams_path = simulation_path / "data_streams"

        # Sample values
        eruption_length = random.uniform(*eruption_length_range)
        eruption_start = random.uniform(*eruption_start_range)
        location = random.choice(location_range)
        speed = random.uniform(*speed_range)
        size = random.uniform(*size_range)
        max_soil_moisture = random.uniform(*max_soil_moisture_range)
        max_precipitation = random.uniform(*max_precipitation_range)
        max_land = random.uniform(*max_land_range)
        # Create a mission in the KG
        mission_id = add_volcano_mission(location)

        # Generate accesses if not already there
        access_path = accesses_path / f"{location}.json"
        if not access_path.exists():
            access_times = obtain_access_times(mission_id)
        else:
            access_times = read_access_times(location)

        # Create simulation
        generate_flood_simulation(mission_id, eruption_length, eruption_start, location, speed, size,
                            max_soil_moisture, max_precipitation, max_land, simulation_information_path)


def generate_forest_fire_simulation(mission_id, hurricane_length, hurricane_start, location, speed, size,
                                    max_temp, max_fire_temp, max_cloud, max_gases, simulation_information_path):
    observable_properties = ["Land surface temperature", "Fire temperature", "Cloud type", "Trace gases (excluding ozone)"]
    with simulation_information_path.open('w', encoding='utf8') as simulation_information_file:
        simulation_information_json = {
            "mission_id": mission_id,
            "length": hurricane_length,
            "start": hurricane_start,
            "location": location,
            "speed": speed,
            "size": size,
            "max_temp": max_temp,
            "max_fire_temp": max_fire_temp,
            "max_cloud": max_cloud,
            "max_gases": max_gases,
            "observable_properties": observable_properties
        }
        json.dump(simulation_information_json, simulation_information_file)


def generate_forest_fire_simulations(quantity, event_fraction):
    int_path = Path("./int_files")
    simulations_path = int_path / "simulations"
    simulations_path.mkdir(parents=True, exist_ok=True)
    accesses_path = int_path / "accesses"

    eruption_length_range = [12., 120.]  # hours
    eruption_start_range = [0., 168.]  # hours since beginning of simulation
    location_range = ["Spain", "Greece", "California", "Washington", "Kenya"]
    speed_range = [0.1, 0.5]  # fraction of time until max eruption
    size_range = [200., 2000.]  # meter radius
    max_temp_range = [80., 99.]
    max_fire_temp_range = [200., 300.]
    max_cloud_range = [0.5, 0.9]
    max_gases_range = [100, 200]

    # For each simulation, sample a value for each parameter, create a simulation, save it under int_files
    for sim_number in range(quantity):
        # Create paths
        simulation_path = simulations_path / f"simulation_{sim_number}"
        if simulation_path.exists():
            shutil.rmtree(simulation_path)
        simulation_path.mkdir(parents=True, exist_ok=True)

        simulation_information_path = simulation_path / "simulation_information.json"
        data_streams_path = simulation_path / "data_streams"

        # Sample values
        eruption_length = random.uniform(*eruption_length_range)
        eruption_start = random.uniform(*eruption_start_range)
        location = random.choice(location_range)
        speed = random.uniform(*speed_range)
        size = random.uniform(*size_range)
        max_temp = random.uniform(*max_temp_range)
        max_fire_temp = random.uniform(*max_fire_temp_range)
        max_cloud = random.uniform(*max_cloud_range)
        max_gases = random.uniform(*max_gases_range)
        # Create a mission in the KG
        mission_id = add_volcano_mission(location)

        # Generate accesses if not already there
        access_path = accesses_path / f"{location}.json"
        if not access_path.exists():
            access_times = obtain_access_times(mission_id)
        else:
            access_times = read_access_times(location)

        # Create simulation
        generate_forest_fire_simulation(mission_id, eruption_length, eruption_start, location, speed, size,
                                        max_temp, max_fire_temp, max_cloud, max_gases, simulation_information_path)
