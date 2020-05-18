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
                sensor["across_fov"] = 15 # degrees
                sensor["along_fov"] = 15 # degrees
            elif sensor_geometry == "conical":
                sensor["conical_fov"] = 15 # degrees

            # Add accuracies information
            accuracies = retrieve_instrument_accuracies(sensor_name, session)
            sensor["accuracies"] = accuracies
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
