from random import random

from neo4j import GraphDatabase


def save_evidence(session, results, evidence, predicates, predicate_types):
    for record in results:
        for relationship in record:
            start_node = session.run('MATCH (n) WHERE id(n) = {id} RETURN n',
                                     id=relationship.start_node.id).single().value()
            end_node = session.run('MATCH (n) WHERE id(n) = {id} RETURN n',
                                   id=relationship.end_node.id).single().value()
            if relationship.type not in predicate_types:
                predicate_types.add(relationship.type)
                predicates.append({
                    'type': relationship.type,
                    'node_types': [
                        list(start_node.labels)[0],
                        list(end_node.labels)[0]
                    ]
                })
            evidence.append({
                'type': relationship.type,
                'elements': [
                    start_node,
                    end_node
                ]
            })


def create_logic():
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))

    evidence = []
    predicates = []
    name_matching = {}
    predicate_types = set()

    with driver.session() as session:
        # Generate evidence and predicates for sensors and platforms
        results = session.run('MATCH (s:Sensor)-[r:HOSTS]-(p:Platform) '
                              'WHERE p.status = "Currently being flown" '
                              'RETURN r')
        save_evidence(session, results, evidence, predicates, predicate_types)

        # Generate evidence and predicates for sensors and observable properties
        results = session.run('MATCH (p:Platform)-[:HOSTS]-(s:Sensor)-[r:OBSERVES]-(op:ObservableProperty) '
                              'WHERE p.status = "Currently being flown" '
                              'RETURN DISTINCT r')
        save_evidence(session, results, evidence, predicates, predicate_types)

        # Generate evidence and predicates for mission and observations
        results = session.run('MATCH (m:Mission)-[r:REQUIRES]-(ob:Observation) '
                              'WHERE m.mid = 1 '
                              'RETURN r')
        save_evidence(session, results, evidence, predicates, predicate_types)

        # Generate evidence and predicates for observations and its observable properties
        results = session.run('MATCH (m:Mission)-[:REQUIRES]-(ob:Observation)-[r:OBSERVEDPROPERTY]-(op:ObservableProperty) '
                              'WHERE m.mid = 1 '
                              'RETURN DISTINCT r')
        save_evidence(session, results, evidence, predicates, predicate_types)

        # Generate evidence and predicates for platforms being in visibility of the target
        visibility_threshold = 0.8
        predicate_types.add('inVisibilityOfTarget')
        predicates.append({
            'type': 'inVisibilityOfTarget',
            'node_types': ['Platform']
        })
        results = session.run('MATCH (p:Platform) '
                              'WHERE p.status = "Currently being flown" '
                              'RETURN p')
        for record in results:
            platform_node = record.value()
            randnum = random()
            if randnum < visibility_threshold:
                evidence.append({
                    'type': 'inVisibilityOfTarget',
                    'elements': [platform_node]
                })

        return evidence, predicates
