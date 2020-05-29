import os


def call_sensing_framework(satellite_list):
    cwd = os.getcwd()
    int_path = os.path.join(cwd, "int_files")
    can_participate_path = os.path.join(int_path, "can_participate.txt")
    with open(can_participate_path, 'w', encoding='utf8') as can_participate_file:
        for satellite in satellite_list:
            can_participate_file.write(satellite + '\n')
    print("Called sensing framework")
