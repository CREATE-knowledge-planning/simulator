import numpy as np
import matplotlib.pyplot as plt


def generate_fake_timeline(data, state_changes, states):
    state = 0
    last_change = 0
    next_change = state_changes[0]
    rng_generator = np.random.default_rng()
    for i in range(168):
        if state < len(state_changes) and i == state_changes[state]:
            state += 1
            last_change = i
            if state < len(state_changes):
                next_change = state_changes[state]
            else:
                next_change = 168
        print(last_change, next_change)
        next_num = generate_num(states[state], rng_generator, i - last_change, next_change - last_change)
        data[i] = next_num


def generate_num(state, rng, diff, length_slope):
    if state["type"] == "stable":
        return state["mean"] + rng.normal(0, state["var"])
    elif state["type"] == "slope":
        slope = float(state["end"] - state["start"])/length_slope
        current_num = state["start"] + slope*diff + rng.normal(0, state["var"])
        return current_num
    else:
        return 0.


def generate_fake_data():
    # For all data, we assume hourly collection for a week (24*7 = 168 data points)
    # Furthermore, the volcano eruption starts happening at 3AM on the third day (datapoint 50)
    # The peak of the eruption is at 8AM (dp 55)
    # Eruption stops fifth day 12PM (dp 107)
    # Data back to normal after 12 hours (dp 119)


    # Generate TIR data (Kelvin)
    state_changes = [50, 55, 107, 119]
    states = [{"type": "stable", "mean": 25, "var": 0.1},
              {"type": "slope", "start": 25, "end": 180, "var": 0.1},
              {"type": "stable", "mean": 180, "var": 0.},
              {"type": "slope", "start": 180, "end": 25, "var": 0.1},
              {"type": "stable", "mean": 25, "var": 0.1}]
    tir_data1 = np.zeros(168)
    generate_fake_timeline(tir_data1, state_changes, states)

    states = [{"type": "stable", "mean": 25, "var": 0.3},
              {"type": "slope", "start": 25, "end": 180, "var": 0.3},
              {"type": "stable", "mean": 180, "var": 0.},
              {"type": "slope", "start": 180, "end": 25, "var": 0.3},
              {"type": "stable", "mean": 25, "var": 0.3}]
    tir_data2 = np.zeros(168)
    generate_fake_timeline(tir_data2, state_changes, states)

    # Generate SWIR data (Kelvin)
    state_changes = [54, 58, 100, 107]
    states = [{"type": "stable", "mean": 200, "var": 0.},
              {"type": "slope", "start": 200, "end": 450, "var": 0.25},
              {"type": "stable", "mean": 450, "var": 0.25},
              {"type": "slope", "start": 450, "end": 200, "var": 0.25},
              {"type": "stable", "mean": 200, "var": 0.}]
    swir_data1 = np.zeros(168)
    generate_fake_timeline(swir_data1, state_changes, states)

    states = [{"type": "stable", "mean": 25, "var": 0.3},
              {"type": "slope", "start": 25, "end": 180, "var": 0.3},
              {"type": "stable", "mean": 180, "var": 0.},
              {"type": "slope", "start": 180, "end": 25, "var": 0.3},
              {"type": "stable", "mean": 25, "var": 0.3}]
    swir_data2 = np.zeros(168)
    generate_fake_timeline(swir_data2, state_changes, states)

    # Generate Plume data (prob of ash plume)
    state_changes = [50, 55, 107, 119]
    states = [{"type": "stable", "mean": 0, "var": 0.},
              {"type": "slope", "start": 0, "end": 0.85, "var": 0.05},
              {"type": "stable", "mean": 0.85, "var": 0.05},
              {"type": "slope", "start": 0.85, "end": 0., "var": 0.05},
              {"type": "stable", "mean": 0, "var": 0.}]
    plume_data1 = np.zeros(168)
    generate_fake_timeline(plume_data1, state_changes, states)

    states = [{"type": "stable", "mean": 0, "var": 0.},
              {"type": "slope", "start": 0, "end": 0.90, "var": 0.10},
              {"type": "stable", "mean": 0.90, "var": 0.10},
              {"type": "slope", "start": 0.90, "end": 0., "var": 0.10},
              {"type": "stable", "mean": 0, "var": 0.}]
    plume_data2 = np.zeros(168)
    generate_fake_timeline(plume_data2, state_changes, states)

    # Generate SAR data (mean displacement of terrain in cm)
    state_changes = [50, 55, 107, 119]
    states = [{"type": "slope", "start": 0, "end": 20, "var": 0.5},
              {"type": "slope", "start": 20, "end": 80, "var": 0.5},
              {"type": "slope", "start": 80, "end": 30, "var": 0.5},
              {"type": "slope", "start": 30, "end": 0, "var": 0.5},
              {"type": "stable", "mean": 0, "var": 0.5}]
    sar_data1 = np.zeros(168)
    generate_fake_timeline(sar_data1, state_changes, states)

    states = [{"type": "slope", "start": 0, "end": 20, "var": 1},
              {"type": "slope", "start": 20, "end": 80, "var": 1},
              {"type": "slope", "start": 80, "end": 30, "var": 1},
              {"type": "slope", "start": 30, "end": 0, "var": 1},
              {"type": "stable", "mean": 0, "var": 0.4}]
    sar_data2 = np.zeros(168)
    generate_fake_timeline(sar_data2, state_changes, states)

    # Generate SO2 data (special units for this)
    state_changes = [50, 55, 107, 119]
    states = [{"type": "stable", "mean": 0.1, "var": 0.05},
              {"type": "slope", "start": 0.1, "end": 2.1, "var": 0.05},
              {"type": "stable", "mean": 2.1, "var": 0.05},
              {"type": "slope", "start": 2.1, "end": 0.1, "var": 0.05},
              {"type": "stable", "mean": 0, "var": 0.05}]
    so2_data1 = np.zeros(168)
    generate_fake_timeline(so2_data1, state_changes, states)

    states = [{"type": "stable", "mean": 0.1, "var": 0.1},
              {"type": "slope", "start": 0.1, "end": 2.1, "var": 0.1},
              {"type": "stable", "mean": 2.1, "var": 0.1},
              {"type": "slope", "start": 2.1, "end": 0.1, "var": 0.1},
              {"type": "stable", "mean": 0, "var": 0.1}]
    so2_data2 = np.zeros(168)
    generate_fake_timeline(so2_data2, state_changes, states)

    with open('numbers.npy', 'wb') as f:
        np.save(f, tir_data1)
        plt.plot(tir_data1)
        plt.show()
        np.save(f, tir_data2)
        np.save(f, swir_data1)
        np.save(f, swir_data2)
        np.save(f, plume_data1)
        np.save(f, plume_data2)
        np.save(f, sar_data1)
        np.save(f, sar_data2)
        np.save(f, so2_data1)
        np.save(f, so2_data2)


if __name__ == "__main__":
    generate_fake_data()
