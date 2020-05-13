from datetime import datetime, timedelta

from neo4j import GraphDatabase


def add_volcano_mission():
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    with driver.session() as session:
        summary = session.run('MATCH (m:Mission), (obs:Observation), (l:Location) '
                              'DETACH DELETE m, obs, l').summary()
        print(summary.counters)
        # Create a sample mission
        summary = session.run('CREATE (m:Mission {mid: 1, name: {name}, description: {description}})',
                              name='Mission 1 - Active Volcano Monitoring',
                              description='We want to monitor volcano eruptions in the Pacific Ring of Fire during the '
                                          'next month. Which satellites should we redirect to detect these?').summary()
        print(summary.counters)

        # Add the observations that need to be measured
        now_time = datetime.now()
        month_time = now_time + timedelta(days=7)
        summary = session.run('MATCH (op1:ObservableProperty), (op2:ObservableProperty), (op3:ObservableProperty), '
                              '(op4:ObservableProperty), (op5:ObservableProperty), (m:Mission) '
                              'WHERE op1.name = "Land surface temperature" AND op2.name = "Fire temperature" AND '
                              'op3.name = "Cloud type" AND op4.name = "Land surface topography" AND '
                              'op5.name = "Atmospheric Chemistry - SO2 (column/profile)" AND m.mid = 1 '
                              'CREATE (o1:Observation {name: {name1}, startDate: {start_date}, endDate: {end_date}, accuracy: {acc1}}), '
                              '(o2:Observation {name: {name2}, startDate: {start_date}, endDate: {end_date}, accuracy: {acc2}}), '
                              '(o3:Observation {name: {name3}, startDate: {start_date}, endDate: {end_date}, accuracy: {acc3}}), '
                              '(o4:Observation {name: {name4}, startDate: {start_date}, endDate: {end_date}, accuracy: {acc4}}), '
                              '(o5:Observation {name: {name5}, startDate: {start_date}, endDate: {end_date}, accuracy: {acc5}}), '
                              '(m)-[:REQUIRES]->(o1), (m)-[:REQUIRES]->(o2), (m)-[:REQUIRES]->(o3), '
                              '(m)-[:REQUIRES]->(o4), (m)-[:REQUIRES]->(o5), '
                              '(o1)-[:OBSERVEDPROPERTY]->(op1), (o2)-[:OBSERVEDPROPERTY]->(op2), '
                              '(o3)-[:OBSERVEDPROPERTY]->(op3), (o4)-[:OBSERVEDPROPERTY]->(op4), '
                              '(o5)-[:OBSERVEDPROPERTY]->(op5)',
                              start_date=now_time,
                              end_date=month_time,
                              name1='M1 - Volcano Temperature (TIR)',
                              acc1='1K',
                              name2='M1 - Volcano Temperature (SWIR)',
                              acc2='1K',
                              name3='M1 - Volcano Plume',
                              acc3='10% confidence',
                              name4='M1 - Volcano Land Displacements',
                              acc4='10cm',
                              name5='M1 - Volcano Gases',
                              acc5='0.1'
                              ).summary()
        print(summary.counters)

        # Add locations where measurements need to be made
        summary = session.run('MATCH (m:Mission) '
                              'WHERE m.mid = 1 '
                              'CREATE (l1:Location {name: {name1}, latitude: {lat1}, longitude: {lon1}}), '
                              '(m)-[:HASLOCATION]->(l1)',
                              name1='Mauna Loa',
                              lat1=19.4758589,
                              lon1=-155.6483856,
                              ).summary()
        print(summary.counters)

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
