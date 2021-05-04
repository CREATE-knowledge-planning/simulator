from datetime import datetime, timedelta
import os

from neo4j import GraphDatabase

from kg_access.obtain_driver import get_neo4j_driver


def clear_kg():
    driver = get_neo4j_driver()

    with driver.session() as session:
        summary = session.run('MATCH (m:Mission), (obs:Observation), (l:Location) '
                              'DETACH DELETE m, obs, l').consume()
        print(summary.counters)


def add_volcano_locations():
    driver = get_neo4j_driver()

    with driver.session() as session:
        def create_volcano(tx, name, lat, lon):
            tx.run("CREATE (l1:Location {name: $name, latitude: $lat, longitude: $lon})",
                   name=name, lat=lat, lon=lon)

        # Add locations where measurements need to be made
        session.write_transaction(create_volcano, "Kilauea", 19.4119543, -155.2747327)
        session.write_transaction(create_volcano, "Etna", 37.7510042, 14.9846801)
        session.write_transaction(create_volcano, "Piton de la Fournaise", -21.2494387, 55.7112432)
        session.write_transaction(create_volcano, "Stromboli", 38.7918408, 15.1977824)
        session.write_transaction(create_volcano, "Merapi", -7.5407171, 110.4282145)
        session.write_transaction(create_volcano, "Erta Ale", 13.6069145, 40.6529394)
        session.write_transaction(create_volcano, "Ol Doinyo Lengai", -2.7635781, 35.9056765)
        session.write_transaction(create_volcano, "Mount Unzen", 32.7804497, 130.2497246)
        session.write_transaction(create_volcano, "Mount Yasur", -19.527192, 169.4307231)
        session.write_transaction(create_volcano, "Ambrym", -16.2388854, 168.042517)


def add_hurricane_locations():
    driver = get_neo4j_driver()

    with driver.session() as session:
        def create_hurricane(tx, name, lat, lon):
            tx.run("CREATE (l1:Location {name: $name, latitude: $lat, longitude: $lon})",
                   name=name, lat=lat, lon=lon)

        # Add locations where measurements need to be made
        session.write_transaction(create_hurricane, "Atlantic1", 18.607736, -61.288092)
        session.write_transaction(create_hurricane, "Atlantic2", 26.308562, -75.447379)
        session.write_transaction(create_hurricane, "Atlantic3", 25.957117, -78.542334)
        session.write_transaction(create_hurricane, "Atlantic4", 27.790243, -94.164242)
        session.write_transaction(create_hurricane, "Atlantic5", 11.426051, -81.619162)
        session.write_transaction(create_hurricane, "Pacific1", 33.079810, 143.703265)
        session.write_transaction(create_hurricane, "Pacific2", 22.183588, 136.097657)
        session.write_transaction(create_hurricane, "Pacific3", 14.090973, 130.073797)
        session.write_transaction(create_hurricane, "Pacific4", 6.680097, 130.780933)
        session.write_transaction(create_hurricane, "Pacific5", 0.427483, 138.535974)


def add_flood_locations():
    driver = get_neo4j_driver()

    with driver.session() as session:
        def create_flood(tx, name, lat, lon):
            tx.run("CREATE (l1:Location {name: $name, latitude: $lat, longitude: $lon})",
                   name=name, lat=lat, lon=lon)

        # Add locations where measurements need to be made
        session.write_transaction(create_flood, "India", 28.236019, 77.729279)
        session.write_transaction(create_flood, "Bangladesh", 23.078129, 90.624984)
        session.write_transaction(create_flood, "Texas", 29.695276, -95.351883)
        session.write_transaction(create_flood, "Italy", 45.421771, 12.141446)
        session.write_transaction(create_flood, "Brazil", -3.248639, -60.007637)


def add_forest_fire_locations():
    driver = get_neo4j_driver()

    with driver.session() as session:
        def create_forest_fire(tx, name, lat, lon):
            tx.run("CREATE (l1:Location {name: $name, latitude: $lat, longitude: $lon})",
                   name=name, lat=lat, lon=lon)

        # Add locations where measurements need to be made
        session.write_transaction(create_forest_fire, "Spain", 41.673299, 1.640078)
        session.write_transaction(create_forest_fire, "Greece", 39.774301, 22.058433)
        session.write_transaction(create_forest_fire, "California", 37.735543, -120.793321)
        session.write_transaction(create_forest_fire, "Washington", 46.094343, -121.660813)
        session.write_transaction(create_forest_fire, "Kenya", -0.547029, 40.058512)


def add_volcano_mission(location):
    driver = get_neo4j_driver()

    with driver.session() as session:
        # Count number of missions to get ID
        result = session.run('MATCH (m:Mission) RETURN count(m) as count')
        mission_count = result.single()[0]

        # Create a sample mission
        mission_id = mission_count + 1
        summary = session.run('CREATE (m:Mission {mid: $mission_id, name: $name, description: $description})',
                              mission_id=mission_id,
                              name=f"Mission {mission_id} - Active Volcano Monitoring",
                              description='We want to monitor volcano eruptions in the Pacific Ring of Fire during the '
                                          'next month. Which satellites should we redirect to detect these?').consume()
        print(summary.counters)

        # Add the observations that need to be measured
        now_time = datetime.now()
        month_time = now_time + timedelta(days=14)
        summary = session.run('MATCH (op1:ObservableProperty), (op2:ObservableProperty), (op3:ObservableProperty), '
                              '(op4:ObservableProperty), (m:Mission) '
                              'WHERE op1.name = "Land surface temperature" AND op2.name = "Fire temperature" '
                              'AND op3.name = "Cloud type" AND op4.name = "Land surface topography" '
                              #'AND op5.name = "Atmospheric Chemistry - SO2 (column/profile)" ' 
                              'AND m.mid = $mission_id '
                              'CREATE (o1:Observation {name: $name1, startDate: $start_date, endDate: $end_date, accuracy: $acc1}), '
                              '(o2:Observation {name: $name2, startDate: $start_date, endDate: $end_date, accuracy: $acc2}), '
                              '(o3:Observation {name: $name3, startDate: $start_date, endDate: $end_date, accuracy: $acc3}), '
                              '(o4:Observation {name: $name4, startDate: $start_date, endDate: $end_date, accuracy: $acc4}), '
                              #'(o5:Observation {name: $name5, startDate: $start_date, endDate: $end_date, accuracy: $acc5}), '
                              '(m)-[:REQUIRES]->(o1), (m)-[:REQUIRES]->(o2), (m)-[:REQUIRES]->(o3), '
                              '(m)-[:REQUIRES]->(o4), '
                              #'(m)-[:REQUIRES]->(o5), '
                              '(o1)-[:OBSERVEDPROPERTY]->(op1), (o2)-[:OBSERVEDPROPERTY]->(op2), '
                              '(o3)-[:OBSERVEDPROPERTY]->(op3), (o4)-[:OBSERVEDPROPERTY]->(op4) ',
                              #'(o5)-[:OBSERVEDPROPERTY]->(op5)',
                              mission_id=mission_id,
                              start_date=now_time,
                              end_date=month_time,
                              name1='M1 - Volcano Temperature (TIR)',
                              acc1='1 K',
                              name2='M1 - Volcano Temperature (SWIR)',
                              acc2='1 K',
                              name3='M1 - Volcano Plume',
                              acc3='10 % confidence',
                              name4='M1 - Volcano Land Displacements',
                              acc4='10 cm',
                              #name5='M1 - Volcano Gases',
                              #acc5='0.1'
                              ).consume()
        print(summary.counters)

        summary = session.run('MATCH (m:Mission), (l:Location) '
                              'WHERE m.mid = $mission_id AND l.name = $location '
                              'CREATE (m)-[:HASLOCATION]->(l)',
                              mission_id=mission_id,
                              location=location
                              ).consume()

        print(summary.counters)

        return mission_id


def add_hurricane_mission(location):
    driver = get_neo4j_driver()

    with driver.session() as session:
        # Count number of missions to get ID
        result = session.run('MATCH (m:Mission) RETURN count(m) as count')
        mission_count = result.single()[0]

        # Create a sample mission
        mission_id = mission_count + 1
        summary = session.run('CREATE (m:Mission {mid: $mission_id, name: $name, description: $description})',
                              mission_id=mission_id,
                              name=f"Mission {mission_id} - Active Hurricane Monitoring",
                              description='').consume()
        print(summary.counters)

        # Add the observations that need to be measured
        now_time = datetime.now()
        month_time = now_time + timedelta(days=14)
        summary = session.run('MATCH (op1:ObservableProperty), (op2:ObservableProperty), (op3:ObservableProperty), '
                              '(op4:ObservableProperty), (m:Mission) '
                              'WHERE op1.name = "Wind speed over sea surface (horizontal)" AND op2.name = "Sea surface temperature" '
                              'AND op3.name = "Cloud imagery" '
                              'AND m.mid = $mission_id '
                              'CREATE (o1:Observation {name: $name1, startDate: $start_date, endDate: $end_date, accuracy: $acc1}), '
                              '(o2:Observation {name: $name2, startDate: $start_date, endDate: $end_date, accuracy: $acc2}), '
                              '(o3:Observation {name: $name3, startDate: $start_date, endDate: $end_date, accuracy: $acc3}), '
                              '(m)-[:REQUIRES]->(o1), (m)-[:REQUIRES]->(o2), (m)-[:REQUIRES]->(o3), '
                              '(o1)-[:OBSERVEDPROPERTY]->(op1), (o2)-[:OBSERVEDPROPERTY]->(op2), '
                              '(o3)-[:OBSERVEDPROPERTY]->(op3), ',
                              mission_id=mission_id,
                              start_date=now_time,
                              end_date=month_time,
                              name1='M1 - Wind speeds',
                              acc1='1 K',
                              name2='M1 - Sea temperature',
                              acc2='1 K',
                              name3='M1 - Clouds',
                              acc3='10 % confidence',
                              #name5='M1 - Volcano Gases',
                              #acc5='0.1'
                              ).consume()
        print(summary.counters)

        summary = session.run('MATCH (m:Mission), (l:Location) '
                              'WHERE m.mid = $mission_id AND l.name = $location '
                              'CREATE (m)-[:HASLOCATION]->(l)',
                              mission_id=mission_id,
                              location=location
                              ).consume()

        print(summary.counters)

        return mission_id


def add_flood_mission(location):
    driver = get_neo4j_driver()

    with driver.session() as session:
        # Count number of missions to get ID
        result = session.run('MATCH (m:Mission) RETURN count(m) as count')
        mission_count = result.single()[0]

        # Create a sample mission
        mission_id = mission_count + 1
        summary = session.run('CREATE (m:Mission {mid: $mission_id, name: $name, description: $description})',
                              mission_id=mission_id,
                              name=f"Mission {mission_id} - Active Flood Monitoring",
                              description='').consume()
        print(summary.counters)

        # Add the observations that need to be measured
        now_time = datetime.now()
        month_time = now_time + timedelta(days=14)
        summary = session.run('MATCH (op1:ObservableProperty), (op2:ObservableProperty), (op3:ObservableProperty), '
                              '(op4:ObservableProperty), (m:Mission) '
                              'WHERE op1.name = "Soil moisture at the surface" AND op2.name = "Precipitation Profile (liquid or solid)" '
                              'AND op3.name = "Land surface imagery" '
                              'AND m.mid = $mission_id '
                              'CREATE (o1:Observation {name: $name1, startDate: $start_date, endDate: $end_date, accuracy: $acc1}), '
                              '(o2:Observation {name: $name2, startDate: $start_date, endDate: $end_date, accuracy: $acc2}), '
                              '(o3:Observation {name: $name3, startDate: $start_date, endDate: $end_date, accuracy: $acc3}), '
                              '(m)-[:REQUIRES]->(o1), (m)-[:REQUIRES]->(o2), (m)-[:REQUIRES]->(o3), '
                              '(o1)-[:OBSERVEDPROPERTY]->(op1), (o2)-[:OBSERVEDPROPERTY]->(op2), '
                              '(o3)-[:OBSERVEDPROPERTY]->(op3), ',
                              mission_id=mission_id,
                              start_date=now_time,
                              end_date=month_time,
                              name1='M1 - Soil moisture',
                              acc1='1 K',
                              name2='M1 - Precipitation intensity',
                              acc2='1 K',
                              name3='M1 - Land cover',
                              acc3='10 % confidence',
                              #name5='M1 - Volcano Gases',
                              #acc5='0.1'
                              ).consume()
        print(summary.counters)

        summary = session.run('MATCH (m:Mission), (l:Location) '
                              'WHERE m.mid = $mission_id AND l.name = $location '
                              'CREATE (m)-[:HASLOCATION]->(l)',
                              mission_id=mission_id,
                              location=location
                              ).consume()

        print(summary.counters)

        return mission_id


def add_forest_fire_mission(location):
    driver = get_neo4j_driver()

    with driver.session() as session:
        # Count number of missions to get ID
        result = session.run('MATCH (m:Mission) RETURN count(m) as count')
        mission_count = result.single()[0]

        # Create a sample mission
        mission_id = mission_count + 1
        summary = session.run('CREATE (m:Mission {mid: $mission_id, name: $name, description: $description})',
                              mission_id=mission_id,
                              name=f"Mission {mission_id} - Active Forest Fire Monitoring",
                              description='').consume()
        print(summary.counters)

        # Add the observations that need to be measured
        now_time = datetime.now()
        month_time = now_time + timedelta(days=14)
        summary = session.run('MATCH (op1:ObservableProperty), (op2:ObservableProperty), (op3:ObservableProperty), '
                              '(op4:ObservableProperty), (m:Mission) '
                              'WHERE op1.name = "Land surface temperature" AND op2.name = "Fire temperature" '
                              'AND op3.name = "Cloud type" AND op4.name = "Trace gases (excluding ozone)" '
                              #'AND op5.name = "Atmospheric Chemistry - SO2 (column/profile)" ' 
                              'AND m.mid = $mission_id '
                              'CREATE (o1:Observation {name: $name1, startDate: $start_date, endDate: $end_date, accuracy: $acc1}), '
                              '(o2:Observation {name: $name2, startDate: $start_date, endDate: $end_date, accuracy: $acc2}), '
                              '(o3:Observation {name: $name3, startDate: $start_date, endDate: $end_date, accuracy: $acc3}), '
                              '(o4:Observation {name: $name4, startDate: $start_date, endDate: $end_date, accuracy: $acc4}), '
                              #'(o5:Observation {name: $name5, startDate: $start_date, endDate: $end_date, accuracy: $acc5}), '
                              '(m)-[:REQUIRES]->(o1), (m)-[:REQUIRES]->(o2), (m)-[:REQUIRES]->(o3), '
                              '(m)-[:REQUIRES]->(o4), '
                              #'(m)-[:REQUIRES]->(o5), '
                              '(o1)-[:OBSERVEDPROPERTY]->(op1), (o2)-[:OBSERVEDPROPERTY]->(op2), '
                              '(o3)-[:OBSERVEDPROPERTY]->(op3), (o4)-[:OBSERVEDPROPERTY]->(op4) ',
                              #'(o5)-[:OBSERVEDPROPERTY]->(op5)',
                              mission_id=mission_id,
                              start_date=now_time,
                              end_date=month_time,
                              name1='M1 - Temperature (TIR)',
                              acc1='1 K',
                              name2='M1 - Temperature (SWIR)',
                              acc2='1 K',
                              name3='M1 - Smoke',
                              acc3='10 % confidence',
                              name4='M1 - CO Trace',
                              acc4='10 cm',
                              #name5='M1 - Volcano Gases',
                              #acc5='0.1'
                              ).consume()
        print(summary.counters)

        summary = session.run('MATCH (m:Mission), (l:Location) '
                              'WHERE m.mid = $mission_id AND l.name = $location '
                              'CREATE (m)-[:HASLOCATION]->(l)',
                              mission_id=mission_id,
                              location=location
                              ).consume()

        print(summary.counters)

        return mission_id

        # Add MEASURES relationships between the right instruments and the ObservableProperties
        # For fire
        # fire_bands = ['TIR', 'MWIR']
        # fire_technologies = ['Imaging multi-spectral radiometers (vis/IR)', 'Hyperspectral imagers',
        #                      'Imaging microwave radars', 'Imaging multi-spectral radiometers (passive microwave)',
        #                      'Atmospheric temperature and humidity sounders',
        #                      'Multiple direction/polarisation radiometers']
        # summary = session.run('MATCH (s:Sensor), (o:ObservableProperty) '
        #                       'WHERE any(band IN s.wavebands WHERE band IN {bands}) '
        #                       'AND any(type IN s.types WHERE type IN {types}) '
        #                       'AND o.name = {obs_name} '
        #                       'CREATE (s)-[:OBSERVES]->(o)',
        #                       bands=fire_bands,
        #                       types=fire_technologies,
        #                       obs_name='Rocket Launch Fire').summary()
        # print(summary.counters)
        # For plume
        # plume_bands = ['VIS', 'NIR']
        # plume_technologies = ['Imaging multi-spectral radiometers (vis/IR)', 'Hyperspectral imagers',
        #                       'High resolution optical imagers', 'Multiple direction/polarisation radiometers']
        # summary = session.run('MATCH (s:Sensor), (o:ObservableProperty) '
        #                       'WHERE any(band IN s.wavebands WHERE band IN {bands}) '
        #                       'AND any(type IN s.types WHERE type IN {types}) '
        #                       'AND o.name = {obs_name} '
        #                       'CREATE (s)-[:OBSERVES]->(o)',
        #                       bands=plume_bands,
        #                       types=plume_technologies,
        #                       obs_name='Rocket Launch Plume').summary()
        # print(summary.counters)
