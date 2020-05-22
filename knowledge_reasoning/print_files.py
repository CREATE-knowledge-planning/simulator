from neo4j import GraphDatabase

from kg_access.satellites import get_all_active_satellites_with_instruments, get_measures_relationships


def print_kg_reasoning_files(mission_id, access_intervals):
    # Generate the Knowledge Base relationship by relationship, saving the entities in a set to later generate the
    # dictionary

    # Connect to database, open session
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

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
                sensor_instance_name = sat_name + "|" + sensor_name
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
        relations.add("MEASURES")
        measures_relations = get_measures_relationships(session)
        for relation in measures_relations:
            entities.add(relation["head"])
            entities.add(relation["tail"])
        kg.extend(measures_relations)


        # OBSERVEDPROPERTY

        # REQUIRES

        # inVisibilityOfTarget

        # SENSORTYPE

        # SENSORBAND

        # TYPEOBSERVES

    print(kg)
    # Print a file with a relation between entities and indices
    # Print a file with a relation between predicates and indices
    # Print the knowledge base into a file

    # Print a file with the logic rules

    # Print a ground truth with the set of satellites we know have a chance of participating at all
    pass