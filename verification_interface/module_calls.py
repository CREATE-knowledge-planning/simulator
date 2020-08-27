from pathlib import Path

from neo4j import GraphDatabase
from kg_access.mission import get_mission_information
from verification import encodeMission
from verification.extractJSON import findTarget, find_time_bounds, generate_team_time_id
from verification.main import construct_team, construct_team_from_list


def run_verification(satellite_list, simulation_path, simulation_info, access_intervals):
    # data from knowledge graph
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    # Save kg with names first, at the end substitute for indices
    with driver.session() as session:
        mission_info = get_mission_information(simulation_info["mission_id"], session)
    path_to_dict = Path('./int_files/output.dict')
    ## FOR MOUNT YASUR MISSION
    # pathTimeJSON = 'test_antoni/MountYasur.json'
    # pathToDict = 'test_antoni/output.dict'
    # bin directory of PRISM application
    prism_path = '/Applications/prism-4.6/prism/bin'      

    # name of files for PRISM (saved to current directory)
    mission_file = simulation_path / "prop1.txt"             # specification
    mdp_file = simulation_path / "KG_MDP1.txt"                   # MDP
    output_file = simulation_path / "output1.txt"            # output log

    # res1 = [random.randrange(0, 1000)/1000. for i in range(168)] 
    # res2 =     [random.randrange(0, 1000)/1000. for i in range(168)] 

    # team = {'GOES-17': [{'ABI': {'Cloud type': res1}    }], \
    #     'Metop-A': [{'IASI': {'Land surface temperature': res2}}]}

    team = construct_team_from_list(satellite_list)
    target = simulation_info["location"]
    team_time = find_time_bounds(team, target, access_intervals)
    
    prefix_list = ['a', 's', 'm']
    a_prefix, s_prefix, m_prefix = prefix_list
    team_time_id = generate_team_time_id(path_to_dict, team_time, a_prefix, s_prefix)
    
    a_list, s_list, m_list = generateASMlists(team, path_to_dict, a_prefix, s_prefix, m_prefix)
    numASM = [len(a_list), len(s_list), len(m_list)]
    num_a, num_s, num_m = numASM

    rewardList = ['numAgents']
    print('# of agents, sensors, meas: ',numASM)

    checkTime(team, team_time_id, m_list, path_to_dict, s_prefix, m_prefix)

    # mission for PRISM
    rewardList = ['numAgents']
    missionLength = encodeMission.findMissionLength(path_mission_json)
    # missionPCTL = encodeMission.generateMissionPCTL(path_mission_json, m_list, mission_file, saveFile = True)
    missionPCTL = encodeMission.generateMissionMulti(m_list, mission_file, rewardList, saveFile = True)
    
    # relationship matrices
    relation_as = construct_asMatrix(team, path_to_dict, num_a, num_s, a_prefix, s_prefix, a_list, s_list)
    relation_ms = construct_msMatrix(team, path_to_dict, num_m, num_s, m_prefix, s_prefix, m_list, s_list)
    
    relation_ms_no, probDict = notMeasMat(team, path_to_dict, relation_ms, num_m, num_s,  m_prefix, s_prefix, m_list, s_list)

    # modules for PRISM MDP
    allStates = allStates_as(num_a, num_s, relation_as, a_list, s_list, team_time_id)
    num_states = len(allStates)    # total number of states

    allStates_dict = allStates_asm(numASM, relation_as,relation_ms_no, allStates, probDict)
    actions, timeDict = action2str(num_a, num_s, team_time, allStates, a_prefix, s_prefix, a_list, s_list, path_to_dict)

    KG_module = constructKGModule(actions, timeDict, allStates_dict, numASM, prefix_list, a_list, s_list, team_time, relation_as, relation_ms,probDict,path_to_dict,missionLength)

    rewardsName = rewardList[0]    # criteria we care about
    rewards_module1 = constructNumAgentsCost(num_a, num_s, team_time, allStates, a_prefix, s_prefix, a_list, s_list, m_list, path_to_dict, rewardsName)
    # rewards_module2 = constructEachPModule(num_a, num_s, num_m,a_list, s_list,teamTime, teamTimeID, relation_as, relation_ms_no,a_prefix, s_prefix, m_prefix, probDict, pathToDict)
    KG_module, rewards_module1 = replaceIdx(a_list, s_list, m_list, KG_module, rewards_module1)

    modules = [KG_module, rewards_module1]
    saveMDPfile(modules, mdp_file)

    # save PRISM files to current directory
    current_dir = str(os.getcwd())
    callPRISM(mdp_file, mission_file, output_file, prism_path)
    # change directory back
    os.chdir(current_dir)
    result = outputResult(output_file)
    
    outputADV(mdp_file, mission_file, prism_path, int_path)
    # change directory back
    os.chdir(current_dir)

    print('\n ===================== PARETO FRONT POINTS ===================== ')
    print(result)
    print('\n ===================== POSSIBLE TEAMS ===================== ')
    return parseADV.parseADVmain(path_to_dict, int_path)