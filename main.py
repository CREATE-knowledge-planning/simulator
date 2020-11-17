from http_server.server_functions import open_local_http_server
from knowledge_reasoning.module_calls import train_uniker, eval_uniker, forward_chain
from knowledge_reasoning.print_files import print_kg_reasoning_files
from mission_creation.kg_additions import add_volcano_mission
from orekit_interface.access_intervals import obtain_access_times
from orekit_interface.czml_interface import generate_czml_data


def write_mln_evidence(evidence, output_path):
    names_dict = {}
    with open(output_path + '.db', 'w') as evidence_file:
        for evidence_piece in evidence:
            uids = []
            for element in evidence_piece['elements']:
                uids.append('{}{}'.format(
                    list(element.labels)[0],
                    element.id
                ))
                names_dict[uids[-1]] = element['name']
            evidence_str = "{}({})\n".format(
                evidence_piece['type'],
                ",".join(uids)
            )
            evidence_file.write(evidence_str)
    with open(output_path + '.dict', 'w') as dict_file:
        for uid, name in names_dict.items():
            dict_file.write('{}: {}\n'.format(uid, name))


def write_mln_program(predicates, formulas_path, output_path):
    with open(output_path + '.mln', 'w') as program_file:
        program_file.write('// predicate declarations\n')
        for predicate in predicates:
            predicate_str = '{}({})\n'.format(
                predicate['type'],
                ','.join(predicate['node_types'])
            )
            program_file.write(predicate_str)
        program_file.write('\n// formulas\n')
        with open(formulas_path) as formulas_file:
            program_file.write(formulas_file.read())


def main():
    # This is the main process from mission to list of participating satellites

    # 1. Input a mission into the Knowledge Graph
    add_volcano_mission()

    # 2. Run Orekit simulation to obtain access times for all satellites that can participate (as in have the right
    # sensors) in the mission.
    access_intervals = obtain_access_times(1)

    # 3. Use the information from KG + simulation to generate outputs for Knowledge Reasoning (logic),
    # Sensing Framework (?), Verification (logic)

    # 4. Call the Knowledge Reasoning
    print_kg_reasoning_files(1, access_intervals)
    # Train the model
    final_path = train_uniker()
    # Perform inference
    satellite_list = merge_results(final_path)

    # 5. Call the Sensing Framework
    generate_fake_data(1, access_intervals)
    call_sensing_framework(satellite_list)

    # 6. Call the Verification module

    # 7. Run an Orekit simulation with the result to obtain metrics and final access times, save results in CZML
    generate_czml_data()

    # 8. Spin up an HTTP server, display Cesium results of the final simulation with FOVs and the ground station/s
    open_local_http_server()


if __name__ == "__main__":
    main()
