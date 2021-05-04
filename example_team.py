from verification.parseADV import pareto_plot_all
import os
from verification.generate_MDP_pruned import all_states_as
from verification.main import check_time, main_parallelized, team_per_timestep
from verification.extractJSON import construct_as_matrix, generate_as_lists, generate_m_list, generate_team_time_id
from verification.main import construct_team_from_list
from verification.extractJSON import find_time_bounds
import json
from pathlib import Path
from kg_access.obtain_driver import get_neo4j_driver
from kg_access.satellites import get_sensors_from_satellite_list
import multiprocessing as mp

from orekit_interface.access_intervals import read_access_times
from sensing_interface.module_calls import run_sensor_planner
from verification_interface.module_calls import retrieve_entity_dict

def parallelize(team, team_time, entity_dict, inv_entity_dict, mission_file, mdp_filename, output_filename, simulation_path, prism_path, m_list, prefix_list, i, q, prism_wsl):
    teamUpd = team_per_timestep(team, team_time, i)
    q.put(main_parallelized(entity_dict, inv_entity_dict, mission_file, mdp_filename, output_filename, simulation_path, prism_path, teamUpd, m_list, prefix_list, i, prism_wsl))


def amy_team(team, param):
    new_team = {}
    for agent in team:
        new_sensors = {}
        for sensor in agent["sensors"]:
            new_sensors[sensor["name"]] = sensor[param]
        new_team[agent["name"]] = new_sensors
    return new_team


def main():
    simulation_path = Path('./int_files/simulations/simulation_0').resolve()
    simulation_info_path = simulation_path / 'simulation_information.json'
    with simulation_info_path.open() as simulation_info_file:
        simulation_info = json.load(simulation_info_file)
    # Method 1
    # Full process (UniKER - Sensing - Verification)
    location = simulation_info["location"]
    mission_id = simulation_info["mission_id"]
    access_intervals = read_access_times(location)
    # ["Sentinel-1 A", "Sentinel-1 B", "GOES-13", "GOES-14", "GOES-15", "GOES-16", "GOES-17", "Aqua", "Terra"]
    satellite_list = ["Sentinel-1 A", "Sentinel-1 B", "GOES-15", "GOES-17", "Aqua", "Terra"]

    driver = get_neo4j_driver()
    with driver.session() as session:
        team = get_sensors_from_satellite_list(session, satellite_list)
    team = run_sensor_planner(team, simulation_info)
    team = construct_team_from_list(team)
    team_time = find_time_bounds(team, location, access_intervals)

    print(amy_team(team_time, "probabilities"))
    print(amy_team(team_time, "times"))

    entity_dict, inv_entity_dict = retrieve_entity_dict(driver)

    prefix_list = ['a', 's', 'm']
    a_prefix, s_prefix, m_prefix = prefix_list
    team_time_id = generate_team_time_id(entity_dict, team_time, a_prefix, s_prefix)

    a_list, s_list = generate_as_lists(team, entity_dict, a_prefix, s_prefix)
    m_list = generate_m_list(team, simulation_path / "simulation_information.json", entity_dict, prefix_list[2])
    num_asm = [len(a_list), len(s_list), len(m_list)]
    num_a, num_s, num_m = num_asm
    print('# of agents, sensors, meas: ', num_asm)

    check_time(team, team_time_id, m_list, entity_dict, s_prefix, m_prefix)

    # relationship matrices
    relation_as = construct_as_matrix(team, entity_dict, num_a, num_s, a_prefix, s_prefix, a_list, s_list)

    # modules for PRISM MDP
    all_states = all_states_as(num_a, num_s, relation_as, a_list, s_list, team_time_id)
    num_states = len(all_states)    # total number of states

    prism_wsl = (os.environ.get("PRISM_WSL", "yes") == "yes")

    # name of files for PRISM (saved to current directory)
    mission_file = simulation_path / "prop1.txt"             # specification
    mdp_filename = "KG_MDP1.txt"                   # MDP
    output_filename = "output1.txt"            # output log
    prism_path = Path(os.environ.get("PRISM_PATH", 'D:/Dropbox/darpa_grant/prism/prism/bin'))
    print(prism_path)
    mission_length = 14

    qout = mp.Queue()
    processes = [mp.Process(target=parallelize, args=(team, team_time, entity_dict, inv_entity_dict, mission_file, mdp_filename, output_filename, simulation_path, prism_path, m_list, prefix_list, i, qout, prism_wsl)) for i in range(mission_length)]
    for p in processes:
        p.start()

    for p in processes:
        p.join()

    result = []
    teaming = []
    times = []
    for p in processes:
        result_p, teaming_p, time_dict = qout.get()
        result.append(result_p)
        teaming.append(teaming_p)
        times.append(time_dict)


    # merge all teaming dictionaries into one
    teams = {k: v for d in teaming for k, v in d.items()}
    timestep_dict = {k: v for d in times for k, v in d.items()}

    optimal_teaming = pareto_plot_all(result, teams, timestep_dict)
    print('\n ===================== OPTIMAL TEAM ===================== ')
    print(optimal_teaming)
    print(result)

if __name__ == '__main__':
    main()