import requests
from neo4j import GraphDatabase


def retrieve_available_satellites(mission_id):
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "test"))
    with driver.session() as session:
        result = session.run('MATCH (p:Platform)--(s:Sensor)--(op:ObservableProperty)--(ob:Observation)--(m:Mission) '
                             'WHERE m.mid={mission_id} AND p.status="Currently being flown" RETURN DISTINCT p;',
                             mission_id=mission_id)
        satellites = []
        for record in result:
            satellites.append({"name": record["p"]["name"], "norad_id": record["p"]["norad_id"]})
    driver.close()
    return satellites


def add_tle_information(satellites):
    for satellite in satellites:
        r = requests.get('https://ivanstanojevic.me/api/tle/' + str(satellite["norad_id"]))
        tle_json = r.json()
        print(tle_json)


def obtain_access_times(mission_id):
    # 1. Obtain a list of satellites that can participate in the mission from the Knowledge Graph
    satellites = retrieve_available_satellites(mission_id)
    # 2. Download the TLEs for the satellites
    add_tle_information(satellites)
    # 3. Save all required information on a file for Orekit:
    # all involved satellites;
    # for each satellite - name, TLE, instruments;
    # for each instrument - name, FOV type, FOV values;
    # all involved locations from mission

    # 4. Call Orekit and wait for the results before continuing

    # 5. Read Orekit results from file and put them into the right format for this code

    # Return a map<Measurement, map<Location, Intervals>>
    pass