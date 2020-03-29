from datetime import datetime, timedelta

from neo4j import GraphDatabase


def add_mission():
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    with driver.session() as session:
        summary = session.run('MATCH (m:Mission), (obs:Observation), (op:ObservableProperty) '
                              'WHERE op.name = "Rocket Launch Fire" OR op.name = "Rocket Launch Plume" '
                              'DETACH DELETE m, obs, op').summary()
        print(summary.counters)
        # Create a sample mission
        summary = session.run('CREATE (m:Mission {mid: 1, description: {description}})',
                              description='We want to detect a rocket launch in North Korea in the next 48h. Which satellites '
                                          'should we redirect to detect this launch?').summary()
        print(summary.counters)

        # Create new observables as they are not common EO measurements
        summary = session.run('CREATE (o1:ObservableProperty {name: {name1}}), (o2:ObservableProperty {name: {name2}})',
                              name1='Rocket Launch Fire',
                              name2='Rocket Launch Plume').summary()
        print(summary.counters)

        # Add the observations that need to be measured
        now_time = datetime.now()
        twodays_time = now_time + timedelta(days=2)
        summary = session.run('MATCH (op1:ObservableProperty), (op2:ObservableProperty), (m:Mission) '
                              'WHERE op1.name = "Rocket Launch Fire" AND op2.name = "Rocket Launch Plume" AND m.mid = 1 '
                              'CREATE (o1:Observation {startDate: {start_date1}, endDate: {end_date1}, accuracy: {acc1}}), '
                              '(o2:Observation {startDate: {start_date2}, endDate: {end_date2}, accuracy: {acc2}}), '
                              '(m)-[:REQUIRES]->(o1), (m)-[:REQUIRES]->(o2), '
                              '(o1)-[:OBSERVEDPROPERTY]->(op1), (o2)-[:OBSERVEDPROPERTY]->(op2)',
                              start_date1=now_time,
                              end_date1=twodays_time,
                              acc1='1K',
                              start_date2=now_time,
                              end_date2=twodays_time,
                              acc2='80%').summary()
        print(summary.counters)

        # Add MEASURES relationships between the right instruments and the ObservableProperties
        # For fire
        fire_bands = ['TIR', 'MWIR']
        fire_technologies = ['Imaging multi-spectral radiometers (vis/IR)', 'Hyperspectral imagers',
                             'Imaging microwave radars', 'Imaging multi-spectral radiometers (passive microwave)',
                             'Atmospheric temperature and humidity sounders',
                             'Multiple direction/polarisation radiometers']
        summary = session.run('MATCH (s:Sensor), (o:ObservableProperty) '
                              'WHERE any(band IN s.wavebands WHERE band IN {bands}) '
                              'AND any(type IN s.types WHERE type IN {types}) '
                              'AND o.name = {obs_name} '
                              'CREATE (s)-[:OBSERVES]->(o)',
                              bands=fire_bands,
                              types=fire_technologies,
                              obs_name='Rocket Launch Fire').summary()
        print(summary.counters)
        # For plume
        plume_bands = ['VIS', 'NIR']
        plume_technologies = ['Imaging multi-spectral radiometers (vis/IR)', 'Hyperspectral imagers',
                              'High resolution optical imagers', 'Multiple direction/polarisation radiometers']
        summary = session.run('MATCH (s:Sensor), (o:ObservableProperty) '
                              'WHERE any(band IN s.wavebands WHERE band IN {bands}) '
                              'AND any(type IN s.types WHERE type IN {types}) '
                              'AND o.name = {obs_name} '
                              'CREATE (s)-[:OBSERVES]->(o)',
                              bands=plume_bands,
                              types=plume_technologies,
                              obs_name='Rocket Launch Plume').summary()
        print(summary.counters)
