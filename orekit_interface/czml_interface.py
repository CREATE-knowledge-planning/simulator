import os
import shutil
import subprocess


def generate_czml_data():
    # TODO: Pass final list of satellites to mark them with different colors and all
    # Call Orekit to generate czml data
    jar_path = os.path.join(os.getcwd(), "jar_files", "czml_generator.jar")
    orekit_process = subprocess.run(["java", "-jar", jar_path], cwd=os.getcwd())

    czml_src_path = os.path.join(os.getcwd(), "int_files", "demo.czml")
    czml_dst_path = os.path.join(os.getcwd(), "http_server", "html_files", "demo.czml")
    shutil.copy(czml_src_path, czml_dst_path)
