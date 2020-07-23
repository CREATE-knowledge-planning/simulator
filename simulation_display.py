import json
import os
import random
from pathlib import Path

from neo4j import GraphDatabase
import numpy as np

from mission_creation.kg_additions import add_volcano_mission
from sensing_interface.data_feed import generate_simulations
import Verification.main as vf_main

import matplotlib
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
    cdf3_line = None

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
    cdf_axes.set_title('Montecarlo CDF')
    cdf_axes.set_xlabel('Simulations')
    cdf_axes.set_ylabel('Probabilities')
    cdf_info = figure.add_subplot(gs[1, 2])
    cdf_info.axis('off')
    cdf_text = cdf_info.text(0.05, 0.95, "", transform=cdf_info.transAxes, fontsize=12, verticalalignment='top')

    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')  # works fine on Windows!
    plt.show()

    path = geopandas.datasets.get_path('naturalearth_lowres')
    earth_info = geopandas.read_file(path)
    earth_info.plot(ax=earth_axes, facecolor='none', edgecolor='black')

    cwd = os.getcwd()
    int_path = os.path.join(cwd, "int_files")
    simulations_path = os.path.join(int_path, "simulations")

    # Connect to database, open session
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    # Updates
    success_probs = []
    success_probs_m2 = []
    success_probs_m3 = []

    for simulation_idx, folder in enumerate(os.listdir(simulations_path)):
        simulation_path = os.path.join(simulations_path, folder, "simulation_information.json")
        with open(simulation_path, "r") as simulation_file:
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
        prob5 = 1.0
        for i in range(5):
            prob5 *= (1. - min(1.0, max(0.0, random.gauss(0.4, 0.05))))
        prob5 = 1. - prob5
        prob10 = 1.0
        for i in range(10):
            prob10 *= (1. - min(1.0, max(0.0, random.gauss(0.4, 0.05))))
        prob10 = 1. - prob10
        print(prob5, prob10)
        success_probs.append(prob5)
        success_probs_m2.append(prob10)
        success_probs.sort()
        success_probs_m2.sort()
        success_probs_m3.append(simulation_probabilities["Method 1"][simulation_idx])
        success_probs_m3.sort()

        if cdf_line is None:
            cdf_line = cdf_axes.plot(success_probs, label="KG - 5 satellites")[0]
        cdf_line.set_data(range(simulation_idx), success_probs)

        if cdf2_line is None:
            cdf2_line = cdf_axes.plot(success_probs_m2, color="red", label="KG - 10 satellites")[0]
        cdf2_line.set_data(range(simulation_idx), success_probs_m2)

        if cdf3_line is None:
            cdf3_line = cdf_axes.plot(success_probs_m3, color="green", label="Method 1")[0]
        cdf3_line.set_data(range(simulation_idx), success_probs_m3)

        cdf_actualtext = '\n'.join([
            f"KG - 5 Satellites: {np.mean(success_probs):.5f}",
            f"KG - 10 Satellites: {np.mean(success_probs_m2):.5f}",
            f"Method 1: {np.mean(success_probs_m3):.5f}",
        ])
        cdf_text.set_text(cdf_actualtext)

        cdf_axes.legend()
        cdf_axes.relim()
        cdf_axes.autoscale_view()

        # Animation
        figure.canvas.draw_idle()
        figure.canvas.start_event_loop(0.0001)

    figure.canvas.start_event_loop(0)


def extract_team(simulation_path, max_satellites):
    simulation_info_path = Path(simulation_path, 'simulation_information.json')
    with simulation_info_path.open() as simulation_info_file:
        simulation_info = json.load(simulation_info_file)
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


def extract_location(simulation_path):
    simulation_info_path = Path(simulation_path, 'simulation_information.json')
    with simulation_info_path.open() as simulation_info_file:
        simulation_info = json.load(simulation_info_file)
    return simulation_info["location"]


def compute_probabilities():
    paths = Path('./int_files/simulations/')
    simulation_probabilities = {"Method 1": [], "Method 2": [], "Method 3": []}
    for simulation_path in [p for p in paths.iterdir() if p.is_dir()]:
        # Method 1
        # Call Amy code with invented Zhaoliang probabilities and the full team from simulation
        team = extract_team(simulation_path, 10)
        location = extract_location(simulation_path)
        print(team, location)
        final_prob = vf_main.main(team, location)
        simulation_probabilities["Method 1"] = final_prob

        # Method 2

        # Method 3

        # ...
    return simulation_probabilities

def main():
    # This is the main process from mission to list of participating satellites

    # 1. Input a mission into the Knowledge Graph
    #add_volcano_mission()

    #generate_simulations(100, 0.5)

    simulation_probabilities = compute_probabilities()

    display_simulation_results(simulation_probabilities)


if __name__ == "__main__":
    main()
