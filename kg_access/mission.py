from neo4j import Session


def get_target_locations(mission_id, session):
    result = session.run('MATCH (m:Mission)-[:HASLOCATION]-(l:Location) '
                         'WHERE m.mid={mission_id} RETURN DISTINCT l;',
                         mission_id=mission_id)
    locations = []
    for record in result:
        location_info = {
            "name": record["l"]["name"],
            "latitude": record["l"]["latitude"],
            "longitude": record["l"]["longitude"]
        }
        locations.append(location_info)
    return locations


def get_required_observations(mission_id, session):
    result = session.run('MATCH (m:Mission)--(o:Observation) '
                         'WHERE m.mid={mission_id} RETURN DISTINCT o;',
                         mission_id=mission_id)
    observations = []
    for record in result:
        observation_info = {
            "name": record["o"]["name"],
            "startDate": record["o"]["startDate"],
            "endDate": record["o"]["endDate"],
            "accuracy": record["o"]["accuracy"]
        }
        observations.append(observation_info)
    return observations


def get_mission_information(mission_id, session: Session):
    result = session.run('MATCH (m:Mission) '
                         'WHERE m.mid={mission_id} RETURN DISTINCT m;',
                         mission_id=mission_id)

    mission = {}
    mission_record = result.single()["m"]
    mission["name"] = mission_record["name"]
    mission["locations"] = get_target_locations(mission_id, session)
    mission["observations"] = get_required_observations(mission_id, session)
    return mission
