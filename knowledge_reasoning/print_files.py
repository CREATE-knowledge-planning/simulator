from genericpath import exists
from pathlib import Path
import random
import shutil

from kg_access.mission import get_observedproperty_relations, get_requires_relations, get_mission_information, \
    get_haslocation_relations
from kg_access.obtain_driver import get_neo4j_driver
from kg_access.satellites import get_all_active_satellites_with_instruments, \
    get_sensortype_relations, get_sensorband_relations, get_typeobserves_relations, get_sensorrule_relations, \
    retrieve_available_satellites, get_observes_relationships


def print_kg_reasoning_files(mission_id, access_intervals, simulation_path: Path):
    # Generate the Knowledge Base relationship by relationship, saving the entities in a set to later generate the
    # dictionary

    # Connect to database, open session
    driver = get_neo4j_driver()

    entities = set()
    relations = set()
    kg = []

    # Save kg with names first, at the end substitute for indices
    with driver.session() as session:
        # HOSTS
        # isInstanceOf
        satellites_info = get_all_active_satellites_with_instruments(session)
        relations.add("HOSTS")
        relations.add("isInstanceOf")
        for satellite in satellites_info:
            sat_name = satellite["name"]
            entities.add(sat_name)
            for sensor in satellite["sensors"]:
                sensor_name = sensor["name"]
                sensor_instance_name = f"{sat_name}|{sensor_name}"
                entities.add(sensor_instance_name)
                kg.append({
                    "head": sat_name,
                    "relationship": "HOSTS",
                    "tail": sensor_instance_name
                })
                entities.add(sensor_name)
                kg.append({
                    "head": sensor_instance_name,
                    "relationship": "isInstanceOf",
                    "tail": sensor_name
                })

        # MEASURES
        relations.add("OBSERVES")
        measures_relations = get_observes_relationships(session)
        for relation in measures_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(measures_relations)

        # OBSERVEDPROPERTY
        relations.add("OBSERVEDPROPERTY")
        observedproperty_relations = get_observedproperty_relations(session)
        for relation in observedproperty_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(observedproperty_relations)

        # REQUIRES
        relations.add("REQUIRES")
        requires_relations = get_requires_relations(mission_id, session)
        for relation in requires_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(requires_relations)

        # HASLOCATION
        relations.add("HASLOCATION")
        haslocation_relations = get_haslocation_relations(mission_id, session)
        for relation in haslocation_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(haslocation_relations)

        # inVisibilityOfTarget
        relations.add("inVisibilityOfTarget")
        for sat_name, sat_info in access_intervals["output"].items():
            for instr_name, instr_info in sat_info.items():
                for target_name, accesses in instr_info.items():
                    if len(accesses["timeArray"]) > 0:
                        sensor_instance_name = sat_name + "|" + instr_name
                        entities.add(sensor_instance_name)
                        entities.add(target_name)
                        kg.append({
                            "head": sensor_instance_name,
                            "relationship": "inVisibilityOfTarget",
                            "tail": target_name
                        })

        # SENSORTYPE
        relations.add("SENSORTYPE")
        sensortype_relations = get_sensortype_relations(session)
        for relation in sensortype_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(sensortype_relations)

        # SENSORBAND
        relations.add("SENSORBAND")
        sensorband_relations = get_sensorband_relations(session)
        for relation in sensorband_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(sensorband_relations)

        # SENSORRULE
        relations.add("SENSORRULE")
        sensorrule_relations = get_sensorrule_relations(session)
        for relation in sensorrule_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(sensorrule_relations)

        # TYPEOBSERVES
        relations.add("TYPEOBSERVES")
        typeobserves_relations = get_typeobserves_relations(session)
        for relation in typeobserves_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(typeobserves_relations)

        relations.add("canParticipate")
        ground_truth = retrieve_available_satellites(mission_id, session)
        mission_info = get_mission_information(mission_id, session)

    # Print a file with a relation between entities and indices
    entities_dict_path = simulation_path / "entities.dict"
    inv_entity_dict = {}
    with entities_dict_path.open('w', encoding='utf8') as entities_dict_file:
        for idx, entity in enumerate(entities):
            entities_dict_file.write(f"{idx}\t{entity}\n")
            inv_entity_dict[entity] = idx

    # Print a file with a relation between predicates and indices
    relations_dict_path = simulation_path / "relations.dict"
    inv_relation_dict = {}
    with relations_dict_path.open('w', encoding='utf8') as relations_dict_file:
        for idx, relation in enumerate(relations):
            relations_dict_file.write(f"{idx}\t{relation}\n")
            inv_relation_dict[relation] = idx

    # Print the knowledge base into a file
    kg_path = simulation_path / "train.txt"
    kg_val_path = simulation_path / "valid.txt"
    train_val_split = 0.1
    with kg_path.open('w', encoding='utf8') as kg_file, kg_val_path.open('w', encoding='utf8') as kg_val_file:
        for fact in kg:
            if random.random() < train_val_split:
                kg_file.write(f'{fact["head"]}\t{fact["relationship"]}\t{fact["tail"]}\n')
                kg_val_file.write(f'{fact["head"]}\t{fact["relationship"]}\t{fact["tail"]}\n')
            else:
                kg_file.write(f'{fact["head"]}\t{fact["relationship"]}\t{fact["tail"]}\n')

    # Print a file with the logic rules
    src_rules_path = Path("./knowledge_reasoning/MLN_rule.txt")
    dst_rules_path = simulation_path / "MLN_rule.txt"
    shutil.copy(src_rules_path, dst_rules_path)
    (simulation_path / "final_rules").mkdir(exist_ok=True)
    shutil.copy(Path("./knowledge_reasoning/fc_observation.txt"), simulation_path / "final_rules" / "fc_observation.txt")
    shutil.copy(Path("./knowledge_reasoning/fc_visibility.txt"), simulation_path / "final_rules" / "fc_visibility.txt")

    # Print a ground truth with the set of satellites we know have a chance of participating at all
    ground_truth_path = simulation_path / "test.txt"
    with ground_truth_path.open('w', encoding='utf8') as ground_truth_file:
        for satellite in ground_truth:
            ground_truth_file.write(f'{satellite["name"]}\tcanParticipate\t{mission_info["name"]}\n')
