import json
import os
import shutil
import subprocess


def generate_czml_data():
    # TODO: Pass final list of satellites to mark them with different colors and all
    # Call Orekit to generate czml data
    jar_path = os.path.join(os.getcwd(), "jar_files", "czml_generator.jar")
    orekit_process = subprocess.run(["java", "-jar", jar_path], cwd=os.getcwd())

    # Remove GEO satellites FOV
    czml_src_path = os.path.join(os.getcwd(), "int_files", "demo.czml")
    geo_list = ["GOES-16", "GOES-17", "COMS", "Himawari-8", "Himawari-9"]
    with open(czml_src_path) as czml_file:
        czml_json = json.load(czml_file)
        czml_json = [packet for packet in czml_json if ("parent" in packet and packet["parent"] not in geo_list) or not ("parent" in packet)]
    with open(czml_src_path, 'w', encoding='utf8') as czml_file:
        json.dump(czml_json, czml_file)

    czml_dst_path = os.path.join(os.getcwd(), "http_server", "html_files", "demo.czml")
    shutil.copy(czml_src_path, czml_dst_path)
