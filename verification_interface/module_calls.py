import os
from pathlib import Path
import random
import copy

from neo4j import GraphDatabase
from numpy.core.numeric import inf
from kg_access.mission import get_mission_information
from verification.encodeMission import find_mission_length, generate_mission_multi
from verification.extractJSON import construct_as_matrix, construct_ms_matrix, find_time_bounds, generate_asm_lists, generate_team_time_id, load_entity_dict, not_meas_mat
from verification.generate_MDP_pruned import action2str, all_states_asm, all_states_as, construct_num_agents_cost, construct_kg_module, replace_idx, save_mdp_file
from verification.main import call_prism, check_time, construct_team_from_list, output_adv, output_result
from verification.parseADV import parse_adv_main


def random_team_choice(team, num_agents):
    new_team = copy.deepcopy(team)
    new_team = random.choices(new_team, k=num_agents)
    return new_team


def run_verification(original_team, simulation_path, simulation_info, access_intervals):
    # data from knowledge graph
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    # Save kg with names first, at the end substitute for indices
    with driver.session() as session:
        mission_info = get_mission_information(simulation_info["mission_id"], session)
    path_to_dict = Path('./int_files/output.dict')
    prism_path = Path('D:/Dropbox/darpa_grant/prism/prism/bin')      

    # name of files for PRISM (saved to current directory)
    mission_file = simulation_path / "prop1.txt"             # specification
    mdp_file = simulation_path / "KG_MDP1.txt"                   # MDP
    output_file = simulation_path / "output1.txt"            # output log

    # Make paths absolute
    mission_file = mission_file.resolve()
    mdp_file = mdp_file.resolve()
    output_file = output_file.resolve()

    # Iterate teams until we have a manageable number of states (~1000)
    entity_dict, inv_entity_dict = load_entity_dict(path_to_dict)
    num_states = inf
    base_team = copy.deepcopy(original_team)
    num_agents = 10
    while num_states > 200:
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

        reward_list = ['numAgents']
        print('# of agents, sensors, meas: ', num_asm)

        check_time(team, team_time_id, m_list, entity_dict, s_prefix, m_prefix)

        # mission for PRISM
        reward_list = ['numAgents']
        mission_length = find_mission_length(mission_info)
        mission_pctl = generate_mission_multi(m_list, mission_file, reward_list, save_file=True)
        
        # relationship matrices
        relation_as = construct_as_matrix(team, entity_dict, num_a, num_s, a_prefix, s_prefix, a_list, s_list)
        relation_ms = construct_ms_matrix(team, entity_dict, num_m, num_s, m_prefix, s_prefix, m_list, s_list)
        
        relation_ms_no, prob_dict = not_meas_mat(team, entity_dict, relation_ms, num_m, num_s, m_prefix, s_prefix, m_list, s_list)

        # modules for PRISM MDP
        all_states = all_states_as(num_a, num_s, relation_as, a_list, s_list, team_time_id)
        num_states = len(all_states)    # total number of states
        print(f"Num agents: {num_agents}; Num states: {num_states}")
        num_agents -= 1

    all_states_dict = all_states_asm(num_asm, relation_as, relation_ms_no, all_states, prob_dict)
    actions, time_dict = action2str(num_a, num_s, team_time, all_states, a_prefix, s_prefix, a_list, s_list, inv_entity_dict)

    kg_module = construct_kg_module(actions, time_dict, all_states_dict, num_asm, prefix_list, a_list, s_list, team_time, relation_as, relation_ms, prob_dict, entity_dict, mission_length)

    rewards_name = reward_list[0]    # criteria we care about
    rewards_module1 = construct_num_agents_cost(num_a, num_s, team_time, all_states, a_prefix, s_prefix, a_list, s_list, m_list, inv_entity_dict, rewards_name)
    # rewards_module2 = constructEachPModule(num_a, num_s, num_m,a_list, s_list,teamTime, teamTimeID, relation_as, relation_ms_no,a_prefix, s_prefix, m_prefix, probDict, pathToDict)
    kg_module, rewards_module1 = replace_idx(a_list, s_list, m_list, kg_module, rewards_module1)

    modules = [kg_module, rewards_module1]
    save_mdp_file(modules, mdp_file)

    # save PRISM files to current directory
    call_prism(mdp_file, mission_file, output_file, prism_path, wsl=True)
    result = output_result(output_file)
    
    output_adv(mdp_file, mission_file, prism_path, simulation_path, wsl=True)

    print('\n ===================== PARETO FRONT POINTS ===================== ')
    print(result)
    print('\n ===================== POSSIBLE TEAMS ===================== ')
    teams = parse_adv_main(inv_entity_dict, simulation_path)
    team_prob, team = max(teams.items(), key=lambda kv_pair: kv_pair[0][0])
    return team_prob[0], team