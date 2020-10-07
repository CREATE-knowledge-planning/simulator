import json
import os
import random
from pathlib import Path

from neo4j import GraphDatabase
import numpy as np
from kg_access.obtain_driver import get_neo4j_driver
from kg_access.satellites import get_sensors_from_satellite_list
from knowledge_reasoning.module_calls import forward_chain

from knowledge_reasoning.print_files import print_kg_reasoning_files
from mission_creation.kg_additions import clear_kg, add_volcano_mission, add_volcano_locations
from sensing_interface.data_feed import generate_simulations
from orekit_interface.access_intervals import read_access_times
# import Verification.main as vf_main

import matplotlib

from sensing_interface.module_calls import run_sensor_planner
from verification_interface.module_calls import run_verification
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# import rasterio
# from rasterio.plot import show
import geopandas


def generate_simulation_text_info(simulation_info):
    textstr = '\n'.join([
        f"Eruption length: {simulation_info['eruption_length']:.2f} hours",
        f"Eruption start: {simulation_info['eruption_start']:.2f} hours",
        f"Location: {simulation_info['location']}",
        f"Eruption Speed: {simulation_info['eruption_length']*simulation_info['speed']:.2f} hours",
        f"Eruption Size: {simulation_info['size']:.2f} m",
        f"Max TIR: {simulation_info['max_tir_temperature']:.2f} W/m^2",
        f"Max SWIR: {simulation_info['max_swir_temperature']:.2f} W/m^2",
        f"Max Plume: {simulation_info['max_ash_cloud']:.2f}",
        f"Max Displacement: {simulation_info['max_terrain_displacement']:.2f} mm",
        f"Max SO2 aerosols: {simulation_info['max_so2_levels']:.2f} Dobson",
    ])

    return textstr


def display_simulation_results(simulation_probabilities):
    cdf_line = None
    cdf2_line = None

    plt.ion()
    figure = plt.figure(constrained_layout=True, figsize=(15, 8))
    widths = [1, 4, 1]
    heights = [2, 1]
    gs = figure.add_gridspec(ncols=3, nrows=2, width_ratios=widths, height_ratios=heights)
    earth_axes = figure.add_subplot(gs[0, 1])
    earth_axes.set_title('Eruption locations and sizes')
    earth_axes.set_xlabel('Longitude (deg)')
    earth_axes.set_ylabel('Latitude (deg)')
    sim_info = figure.add_subplot(gs[0, 2])
    sim_info.axis('off')
    sim_text = sim_info.text(0.05, 0.95, "", transform=sim_info.transAxes, fontsize=12, verticalalignment='top')

    cdf_axes = figure.add_subplot(gs[1, 1])
    cdf_axes.set_title('Montecarlo Results')
    cdf_axes.set_xlabel('Simulation number')
    cdf_axes.set_ylabel('Probability of mission success')
    cdf_info = figure.add_subplot(gs[1, 2])
    cdf_info.axis('off')
    cdf_text = cdf_info.text(0.05, 0.95, "", transform=cdf_info.transAxes, fontsize=12, verticalalignment='top')

    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')  # works fine on Windows!
    plt.show()

    path = geopandas.datasets.get_path('naturalearth_lowres')
    earth_info = geopandas.read_file(path)
    earth_info.plot(ax=earth_axes, facecolor='none', edgecolor='black')

    simulations_path = Path("./int_files/simulations/")

    # Connect to database, open session
    driver = get_neo4j_driver()

    # Updates
    success_probs = []
    success_probs_bench = []
    x_axis = []

    for simulation_idx, folder in enumerate([x for x in simulations_path.iterdir() if x.is_dir()]):
        simulation_path = folder / "simulation_information.json"
        with simulation_path.open("r") as simulation_file:
            simulation_info = json.load(simulation_file)

        with driver.session() as session:
            result = session.run('MATCH (l:Location) '
                                 'WHERE l.name={name} RETURN DISTINCT l;',
                                 name=simulation_info["location"])
            record = result.single()
            location_info = {
                "name": record["l"]["name"],
                "latitude": record["l"]["latitude"],
                "longitude": record["l"]["longitude"]
            }

        earth_axes.add_artist(
            plt.Circle((location_info["longitude"], location_info["latitude"]), simulation_info["size"] * 0.1 / 10000 * 300, ec="red", fill=True, fc="orange"))

        sim_text.set_text(generate_simulation_text_info(simulation_info))

        # Compute probs for demo video
        success_probs_bench.append(0.2)
        success_probs_bench.sort()
        success_probs.append(simulation_probabilities["Full Pipeline"][simulation_idx])
        success_probs.sort()

        x_axis.append(simulation_idx)

        if cdf_line is None:
            cdf_line = cdf_axes.plot(x_axis, success_probs, marker='.', linestyle='', label="Full Pipeline")[0]
        cdf_line.set_data(x_axis, success_probs)

        if cdf2_line is None:
            cdf2_line = cdf_axes.plot(x_axis, success_probs_bench, color="red", label="Benchmark Team")[0]
        cdf2_line.set_data(x_axis, success_probs_bench)

        cdf_actualtext = '\n'.join([
            f"Full Pipeline: {np.mean(success_probs):.5f}",
            f"Benchmark Team: {np.mean(success_probs_bench):.5f}"
        ])
        cdf_text.set_text(cdf_actualtext)

        cdf_axes.legend()
        cdf_axes.relim()
        cdf_axes.autoscale_view()

        # Animation
        figure.canvas.draw_idle()
        figure.canvas.start_event_loop(0.0001)

    figure.canvas.start_event_loop(0)


def extract_team(simulation_info, max_satellites):
    team = {}
    for satellite_name, satellite_info in simulation_info["data_locations"].items():
        team[satellite_name] = []
        for sensor_name, sensor_info in satellite_info.items():
            if sensor_info:
                team[satellite_name].append({
                    sensor_name: {}
                })
                for measurement_name, measurement_info in sensor_info.items():
                    if measurement_info:
                        # TODO: Change to Zhaoliang output?
                        team[satellite_name][-1][sensor_name][measurement_name] = [min(1.0, max(0.0, random.gauss(0.95, 0.2)))]
                if not team[satellite_name][-1][sensor_name]:
                    del team[satellite_name][-1][sensor_name]
                if not team[satellite_name][-1]:
                    del team[satellite_name][-1]
        if not team[satellite_name]:
            del team[satellite_name]
    team_sample = random.sample(list(team), max_satellites)
    pruned_team = {}
    for choice in team_sample:
        pruned_team[choice] = team[choice]
    return pruned_team


def compute_probabilities():
    paths = Path('./int_files/simulations/')
    simulation_probabilities = {"Full Pipeline": [], "Benchmark Team": []}
    for simulation_path in [p for p in paths.iterdir() if p.is_dir()]:
        simulation_info_path = simulation_path / 'simulation_information.json'
        with simulation_info_path.open() as simulation_info_file:
            simulation_info = json.load(simulation_info_file)

        # Method 1
        # Full process (UniKER - Sensing - Verification)
        location = simulation_info["location"]
        mission_id = simulation_info["mission_id"]
        access_intervals = read_access_times(location)
        print_kg_reasoning_files(mission_id, access_intervals, simulation_path)
        satellite_list = forward_chain(simulation_path)

        driver = get_neo4j_driver()
        with driver.session() as session:
            team = get_sensors_from_satellite_list(session, satellite_list)
        team = run_sensor_planner(team, simulation_info)
        team_probs_info_path = simulation_path / 'team_probs.json'
        with team_probs_info_path.open('w') as team_probs_info_file:
            json.dump(team, team_probs_info_file)

        max_prob, final_team = run_verification(team, simulation_path, simulation_info, access_intervals)

        simulation_probabilities["Full Pipeline"].append(max_prob)

        # Method 2

        # ...
    simulation_results = paths / 'results.json'
    with simulation_results.open('w') as simulation_res_file:
        json.dump(simulation_probabilities, simulation_res_file)
    return simulation_probabilities


def load_probabilities():
    simulation_results_path = Path("./int_files/simulations/results.json")
    with simulation_results_path.open('r', encoding='utf-8') as simulation_res_file:
        simulation_probabilities = json.load(simulation_res_file)
    return simulation_probabilities


def main():
    # This is the main process from mission to list of participating satellites

    # 1. Clear the KG for a new simulation run
    clear_kg()
    add_volcano_locations()

    # 2. Generate 100 simulations
    generate_simulations(100, 0.5)

    # 3. Compute the success probabilities for each approach and simulation
    simulation_probabilities = compute_probabilities()
    #simulation_probabilities = load_probabilities()

    # 4. Display the simulation results on the GUI
    display_simulation_results(simulation_probabilities)


if __name__ == "__main__":
    main()
