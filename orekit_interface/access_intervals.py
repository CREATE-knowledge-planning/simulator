import json
import os
import subprocess

import requests
from neo4j import GraphDatabase

from kg_access.locations import get_target_locations
from kg_access.satellites import retrieve_available_satellites


def add_tle_information(satellites):
    active_txt = requests.get('http://www.celestrak.com/NORAD/elements/active.txt').text
    tles = {}
    for line in active_txt.splitlines():
        if line[0] == "1" and len(line) == 69:
            norad_id = int(line[2:7])
            tles[norad_id] = {}
            tles[norad_id]["line1"] = line
        if line[0] == "2" and len(line) == 69:
            norad_id = int(line[2:7])
            tles[norad_id]["line2"] = line
    satellites = [sat for sat in satellites if sat["norad_id"] in tles]
    for satellite in satellites:
        satellite["line1"] = tles[satellite["norad_id"]]["line1"]
        satellite["line2"] = tles[satellite["norad_id"]]["line2"]


def print_orekit_info(satellites, locations):
    # 1. Create directory with all intermediate files
    cwd = os.getcwd()
    int_path = os.path.join(cwd, "int_files")
    if not os.path.isdir(int_path):
        os.makedirs(int_path)

    # 2. Write JSON files with the information in satellites and the mission, which includes
    # all involved satellites;
    # for each satellite - name, TLE, instruments;
    # for each instrument - name, FOV type, FOV values;
    # all involved locations from mission

    satellites_path = os.path.join(int_path, "satellites.json")
    locations_path = os.path.join(int_path, "locations.json")

    with open(satellites_path, "w") as satellites_file:
        json.dump(satellites, satellites_file)
    with open(locations_path, "w") as locations_file:
        json.dump(locations, locations_file)


def obtain_access_times(mission_id):
    # Connect to database, open session
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    with driver.session() as session:
        # 1. Obtain a list of satellites that can participate in the mission from the Knowledge Graph
        satellites = retrieve_available_satellites(mission_id, session)
        # 2. Download the TLEs for the satellites
        add_tle_information(satellites)
        # 3. Get target locations
        locations = get_target_locations(mission_id, session)
        # 4. Save all required information on a file for Orekit:
        print_orekit_info(satellites, locations)

    driver.close()
    # 5. Call Orekit and wait for the results before continuing
    orekit_process = subprocess.run(["java", "-version"], cwd=os.getcwd())

    # 5. Read Orekit results from file and put them into the right format for this code

    # Return a map<Measurement, map<Location, Intervals>>
    pass