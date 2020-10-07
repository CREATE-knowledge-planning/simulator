import os

from neo4j import GraphDatabase


def get_neo4j_driver():
    host = os.environ.get("NEO4J_HOST", "localhost")
    port = os.environ.get("NEO4J_PORT", "7687")
    password = os.environ.get("NEO4J_PASSWORD", "test")
    uri = f"bolt://{host}:{port}"
    driver = GraphDatabase.driver(uri, auth=("neo4j", password))
    return driver