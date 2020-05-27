def retrieve_instrument_accuracies(sensor_name, session):
    """Retrieve information for the accuracies of different measurements from a sensor"""

    # Query the KG for sensors in satellite
    result = session.run(
        'MATCH (s:Sensor)-[ro:OBSERVES]-(op:ObservableProperty) '
        'WHERE s.name={name} RETURN DISTINCT ro, op;',
        name=sensor_name)

    accuracies = {}
    for observes_record in result:
        observable = observes_record["op"]["name"]
        accuracy = observes_record["ro"]["accuracy"]

        # TODO: Find accuracy from datamined sources, including units
        if accuracy == "":
            accuracy = 1.
        else:
            accuracy_list = accuracy.split(" ")
            accuracy = float(accuracy_list[0])
        accuracies[observable] = accuracy

    return accuracies


def retrieve_instrument_characteristics(sensor_name, session):
    # Query the KG for sensors in satellite
    result = session.run(
        'MATCH (s:Sensor)-[ro:OBSERVES]-(op:ObservableProperty) '
        'WHERE s.name={name} RETURN DISTINCT ro, op;',
        name=sensor_name)

    # TODO: Fill these from real data for each sensor
    characteristics = {}
    for observes_record in result:
        observable = observes_record["op"]["name"]

        if observable == "Land surface temperature":
            obs_characteristics = {
                "A": 1.,
                "B": 0.,
                "Q": 0.1,
                "R": 1.,
                "H": {"c1": 233., "c2": 6.67}
            }

        elif observable == "Fire temperature":
            obs_characteristics = {
                "A": 1.,
                "B": 0.,
                "Q": 0.1,
                "R": 1.,
                "H": {"c1": 300., "c2": 40.}
            }
            characteristics[observable] = obs_characteristics
        elif observable == "Cloud type":
            obs_characteristics = {
                "A": 1.,
                "B": 0.,
                "Q": 0.05,
                "R": 0.01,
                "H": {"c1": 0., "c2": 1.}
            }
            characteristics[observable] = obs_characteristics
        elif observable == "Land surface topography":
            obs_characteristics = {
                "A": 1.,
                "B": 0.,
                "Q": 0.1,
                "R": 0.1,
                "H": {"c1": 0., "c2": 1.}
            }
            characteristics[observable] = obs_characteristics
        elif observable == "Atmospheric Chemistry - SO2 (column/profile)":
            obs_characteristics = {
                "A": 1.,
                "B": 0.,
                "Q": 0.1,
                "R": 1.,
                "H": {"c1": 0., "c2": 1.}
            }
            characteristics[observable] = obs_characteristics

    return characteristics


def retrieve_valid_instruments(platform_name, session):
    """Retrieve information of the sensors in a platform"""
    instrument_conical_geometries = ['Conical scanning']
    instrument_rectangular_geometries = ['Cross-track scanning',
                                         'Nadir-viewing',
                                         'Push-broom scanning',
                                         'Side-looking',
                                         'Steerable viewing',
                                         'Whisk-broom scanning']

    # Query the KG for sensors in satellite
    sensor_result = session.run(
        'MATCH (p:Platform)--(s:Sensor) '
        'WHERE p.name={name} RETURN DISTINCT s;',
        name=platform_name)

    sensors = []
    for sensor_record in sensor_result:
        sensor_geometries = sensor_record["s"]["geometries"]
        sensor_geometry = None
        rect_geometries = 0
        conic_geometries = 0
        for db_geometry in sensor_geometries:
            if db_geometry in instrument_conical_geometries:
                conic_geometries += 1
            elif db_geometry in instrument_rectangular_geometries:
                rect_geometries += 1
        if len(sensor_geometries) == conic_geometries:
            sensor_geometry = "conical"
        elif len(sensor_geometries) == rect_geometries:
            sensor_geometry = "rectangular"

        if sensor_geometry is not None:
            sensor_name = sensor_record["s"]["name"]
            sensor = {
                "name": sensor_name,
                "geometry_type": sensor_geometry
            }
            # TODO: Replace for real FOV values
            if sensor_geometry == "rectangular":
                sensor["across_fov"] = 15  # degrees
                sensor["along_fov"] = 15  # degrees
            elif sensor_geometry == "conical":
                sensor["conical_fov"] = 15  # degrees

            # TODO: Add sensing framework information:
            # - A (STM): approximate as an autoregressive model based on real data
            # (although for now just make a based guess)
            # - B: 0 for most sensors (all?)
            # - Q: part of the autoregressive model (white noise)


            # Add accuracies information
            accuracies = retrieve_instrument_accuracies(sensor_name, session)
            sensor["accuracies"] = accuracies

            # TODO: Add sensing framework information:
            # - H: Linearized equation to get L2 measurement from L1 measurement (get from KG -> needs adding to KG)
            # - R: k1 + k2*cos(off_nadir)/h (take into account effects of atmosphere between sensor and measurement)
            sensor["characteristics"] = retrieve_instrument_characteristics(sensor_name, session)

            sensors.append(sensor)
    return sensors


def retrieve_available_satellites(mission_id, session):
    """Retrieve satellites available for the requested mission, together with information on the sensors they carry"""
    result = session.run('MATCH (p:Platform)--(s:Sensor)--(op:ObservableProperty)--(ob:Observation)--(m:Mission) '
                         'WHERE m.mid={mission_id} AND p.status="Currently being flown" RETURN DISTINCT p;',
                         mission_id=mission_id)
    satellites = []
    for record in result:
        platform_name = record["p"]["name"]
        if record["p"]["norad_id"] is not None:
            satellite_info = {
                "name": platform_name,
                "norad_id": record["p"]["norad_id"],
                "sensors": []
            }
            sensors = retrieve_valid_instruments(platform_name, session)
            if len(sensors) > 0:
                satellite_info["sensors"] = sensors
                satellites.append(satellite_info)
    return satellites


def get_all_active_satellites_with_instruments(session):
    result = session.run('MATCH (p:Platform)-[r:HOSTS]-(s:Sensor) '
                         'WHERE p.status="Currently being flown" RETURN DISTINCT p, r, s;')
    satellites = []
    for record in result:
        platform_name = record["p"]["name"]
        satellite_info = {
            "name": platform_name,
            "sensors": []
        }
        sensors = retrieve_valid_instruments(platform_name, session)
        satellite_info["sensors"] = sensors
        satellites.append(satellite_info)
    return satellites


def get_observes_relationships(session):
    result = session.run(
        'MATCH (p:Platform)--(s:Sensor)-[ro:OBSERVES]-(op:ObservableProperty) '
        'WHERE p.status="Currently being flown" RETURN DISTINCT s, ro, op;')
    relations = []
    for record in result:
        sensor_name = record["s"]["name"]
        op_name = record["op"]["name"]
        relations.append({
            "head": sensor_name,
            "relationship": "OBSERVES",
            "tail": op_name
        })
    return relations


def get_sensortype_relations(session):
    result = session.run(
        'MATCH (p:Platform)--(s:Sensor) '
        'WHERE p.status="Currently being flown" RETURN DISTINCT s;')
    relations = []
    for record in result:
        sensor_name = record["s"]["name"]
        sensor_types = record["s"]["types"]
        sensor_technology = record["s"]["technology"]
        if sensor_technology is not None:
            relations.append({
                "head": sensor_name,
                "relationship": "SENSORTYPE",
                "tail": sensor_technology
            })
        for sensor_type in sensor_types:
            relations.append({
                "head": sensor_name,
                "relationship": "SENSORTYPE",
                "tail": sensor_type
            })
    return relations


def get_sensorband_relations(session):
    result = session.run(
        'MATCH (p:Platform)--(s:Sensor) '
        'WHERE p.status="Currently being flown" RETURN DISTINCT s;')
    relations = []
    for record in result:
        sensor_name = record["s"]["name"]
        sensor_bands = record["s"]["wavebands"]
        for sensor_band in sensor_bands:
            relations.append({
                "head": sensor_name,
                "relationship": "SENSORBAND",
                "tail": sensor_band
            })
    return relations


def get_sensorrule_relations(session):
    result = session.run(
        'MATCH (p:Platform)--(s:Sensor) '
        'WHERE p.status="Currently being flown" RETURN DISTINCT s;')
    relations = []
    for record in result:
        sensor_name = record["s"]["name"]
        sensor_types = record["s"]["types"]
        sensor_technology = record["s"]["technology"]
        sensor_mergedtypes = list(sensor_types)
        if sensor_technology is not None:
            sensor_mergedtypes.append(sensor_technology)
        sensor_bands = record["s"]["wavebands"]
        for sensor_type in sensor_mergedtypes:
            for sensor_band in sensor_bands:
                relations.append({
                    "head": sensor_name,
                    "relationship": "SENSORRULE",
                    "tail": sensor_band + " " + sensor_type
                })
    return relations


def get_typeobserves_relations(session):
    result = session.run(
        'MATCH (st:SensorType)--(o:ObservableProperty) '
        'RETURN DISTINCT st, o;')
    relations = []
    for record in result:
        sensor_rule = record["st"]["name"]
        obsprop_name = record["o"]["name"]
        relations.append({
            "head": sensor_rule,
            "relationship": "TYPEOBSERVES",
            "tail": obsprop_name
        })
    return relations
