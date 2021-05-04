import numpy as np
from E2Etest_1d.Sensor_planner import Sensor_planner


def run_sensor_planner(satellite_list, simulation_info):
    event_ts = [int(simulation_info["start"])]
    uts = [0, 1]
    for platform in satellite_list:
        for sensor in platform["sensors"]:
            sensor["probabilities"] = {}
            for measurement, characteristics in sensor["characteristics"].items():
                dx = 1
                dz = 1
                A = np.array([characteristics["A"]]).reshape(dx, dx)
                H = np.array([characteristics["B"]]).reshape(dz, dx)
                B = np.array([characteristics["H"]["c2"]]).reshape(dx, 1)
                Q = np.array([characteristics["Q"]]).reshape(dx, dx)
                R = np.array([characteristics["R"]]).reshape(dz, dz)
                p_tp, p_fp, p_tn, p_fn = Sensor_planner(A, H, B, Q, R, uts, event_ts)
                sensor["probabilities"][measurement] = {
                    "p_tp": p_tp,
                    "p_fp": p_fp,
                    "p_tn": p_tn,
                    "p_fn": p_fn
                }
    return satellite_list
