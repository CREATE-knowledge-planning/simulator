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
