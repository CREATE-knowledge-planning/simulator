import os
from pathlib import Path
import random
import copy
import multiprocessing as mp

from numpy.core.numeric import inf
from kg_access.mission import get_mission_information
from verification.encodeMission import find_mission_length
from verification.extractJSON import construct_as_matrix, find_time_bounds, generate_asm_lists, generate_team_time_id
from verification.generate_MDP_pruned import all_states_as
from verification.main import check_time, construct_team_from_list, main_parallelized, team_per_timestep
from verification.parseADV import pareto_plot_all

from kg_access.obtain_driver import get_neo4j_driver


def random_team_choice(team, num_agents):
    new_team = random.sample(team, k=num_agents)
    return new_team


def retrieve_entity_dict(driver):
    with driver.session() as session:
        result = session.run('MATCH (n) RETURN n;')
        entity_dict = {}
        inv_entity_dict = {}
    
        for record in result:
            node_type = list(record["n"].labels)[0]
            node_id = record["n"].id
            node_name = record["n"]["name"]
            entity_dict[node_name] = f"{node_type}{node_id}"
            inv_entity_dict[f"{node_type}{node_id}"] = node_name
    return entity_dict, inv_entity_dict


def run_verification(original_team, simulation_path: Path, simulation_info, access_intervals):
    # data from knowledge graph
    driver = get_neo4j_driver()

    # Save kg with names first, at the end substitute for indices
    with driver.session() as session:
        mission_info = get_mission_information(simulation_info["mission_id"], session)
    path_to_dict = Path('./int_files/output.dict')   
    prism_path = Path(os.environ.get("PRISM_PATH", 'D:/Dropbox/darpa_grant/prism/prism/bin'))
    print(prism_path)
    prism_wsl = (os.environ.get("PRISM_WSL", "yes") == "yes")

    # name of files for PRISM (saved to current directory)
    mission_file = simulation_path / "prop1.txt"             # specification
    mdp_filename = "KG_MDP1.txt"                   # MDP
    output_filename = "output1.txt"            # output log

    # Make paths absolute
    mission_file = mission_file.resolve()
    simulation_path = simulation_path.resolve()

    # Iterate teams until we have a manageable number of states (~1000)
    entity_dict, inv_entity_dict = retrieve_entity_dict(driver)
    num_states = inf
    base_team = copy.deepcopy(original_team)
    num_agents = 7
    while num_states > 1000:
        mission_length = find_mission_length(mission_info)

        base_team = random_team_choice(base_team, num_agents)
        team = construct_team_from_list(base_team)
        target = simulation_info["location"]
        team_time = find_time_bounds(team, target, access_intervals)
        
        prefix_list = ['a', 's', 'm']
        a_prefix, s_prefix, m_prefix = prefix_list
        team_time_id = generate_team_time_id(entity_dict, team_time, a_prefix, s_prefix)
        
        a_list, s_list, m_list = generate_asm_lists(team, entity_dict, a_prefix, s_prefix, m_prefix)
        num_asm = [len(a_list), len(s_list), len(m_list)]
        num_a, num_s, num_m = num_asm
        print('# of agents, sensors, meas: ', num_asm)

        check_time(team, team_time_id, m_list, entity_dict, s_prefix, m_prefix)

        # relationship matrices
        relation_as = construct_as_matrix(team, entity_dict, num_a, num_s, a_prefix, s_prefix, a_list, s_list)

        # modules for PRISM MDP
        all_states = all_states_as(num_a, num_s, relation_as, a_list, s_list, team_time_id)
        num_states = len(all_states)    # total number of states
        print(f"Num agents: {num_agents}; Num states: {num_states}")
        num_agents -= 1

    def parallelize(i, q):
        teamUpd = team_per_timestep(team, team_time, i)
        q.put(main_parallelized(entity_dict, inv_entity_dict, mission_file, mdp_filename, output_filename, simulation_path, prism_path, teamUpd, i))

    qout = mp.Queue()
    processes = [mp.Process(target=parallelize, args=(i, qout)) for i in range(mission_length)]
    for p in processes:
        p.start()

    for p in processes:
        p.join()

    result = []
    teaming = []
    for p in processes:
        result_p, teaming_p = qout.get()
        result.append(result_p)
        teaming.append(teaming_p)

    # merge all teaming dictionaries into one
    teams = {k: v for d in teaming for k, v in d.items()}

    optimal_teaming = pareto_plot_all(result, teams)
    print('\n ===================== OPTIMAL TEAM ===================== ')
    print(optimal_teaming)

    return optimal_teaming