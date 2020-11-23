import matplotlib
import matplotlib.pyplot as plt

simulation_teams = {'Full Pipeline': [{}, {}, {(0.5756463080859218, 37.0): {1: ['FY-2F', 'Metop-C'], 2: ['FY-2F', 'Metop-C'], 4: ['FY-2F'], 5: ['FY-2F'], 6: ['FY-2F', 'Metop-C'], 7: ['FY-2F'], 10: ['FY-2F', 'DMSP F-17', 'GCOM-C'], 11: ['DMSP F-18', 'Meteor-M N2-2', 'FY-2F'], 12: ['FY-2F'], 14: ['Kanopus-V N3', 'FY-2F', 'Meteor-M N2-2']}, (0.9081595562818457, 38.0): {1: ['FY-2F', 'GCOM-C', 'Metop-C'], 2: ['FY-2F', 'Metop-C'], 5: ['DMSP F-18', 'Meteor-M N2-2', 'FY-2F'], 6: ['Metop-C'], 10: ['FY-2F', 'DMSP F-17', 'GCOM-C'], 11: ['Meteor-M N2-2'], 12: ['FY-2F', 'GCOM-C'], 14: ['Kanopus-V N3', 'FY-2F', 'Meteor-M N2-2']}}, {}, {}, {}, {}, {(0.5559655489998121, 31.0): {3: ['FY-2F', 'DMSP F-18', 'NOAA-18'], 5: ['NOAA-18', 'FY-2F'], 6: ['FY-2F'], 7: ['FY-2F'], 10: ['FY-2F'], 11: ['NOAA-18'], 12: ['NOAA-18', 'FY-2F'], 14: ['FY-2F']}}, {}, {}, {}, {}, {}, {}, {(0.8079818486611621, 36.0): {10: ['GOES-15'], 11: ['GOES-15'], 13: ['GOES-15']}, (0.7537591869634267, 40.0): {1: ['GOES-15'], 8: ['GOES-15'], 10: ['GOES-15'], 11: ['GOES-15']}}, {}, {(0.7311738455143366, 41.0): {6: ['Meteosat-8'], 8: ['Meteosat-8']}}, {}, {}, {(0.5595639891806238, 37.0): {1: ['KOMPSAT-5', 'FY-4A'], 3: ['Meteor-M N2', 'FY-4A'], 4: ['FY-3D', 'FY-4A'], 7: ['Meteor-M N2-2'], 10: ['Meteor-M N2', 'FY-4A'], 13: ['KOMPSAT-5', 'Sentinel-1 B', 'FY-4A']}}, {}, {}, {(0.6054703577058437, 35.0): {1: ['Aura'], 3: ['COMS', 'Aura'], 6: ['Meteor-M N2-2'], 9: ['Aura'], 13: ['Aura']}}, {}, {}, {}, {}, {(0.9949090587225049, 61.0): {}, (0.9869254793560298, 61.99999999999999): {}, (0.9961776761439644, 63.0): {}}, {(0.9320264511198305, 40.0): {}, (0.9694052208886812, 44.0): {}, (0.9794118047103462, 50.0): {}, (0.9795381758996186, 51.0): {}}, {}, {}, {(0.7533781364287114, 51.0): {3: ['Elektro-L N3'], 5: ['Elektro-L N3', 'FY-3C'], 7: ['Elektro-L N3', 'FY-3C'], 9: ['Elektro-L N3', 'Himawari-8', 'FY-2F'], 11: ['Elektro-L N3', 'FY-3C'], 13: ['Elektro-L N3'], 14: ['Elektro-L N3', 'FY-3C']}, (0.9745703814384826, 55.0): {3: ['Elektro-L N3', 'DMSP F-16', 'FY-2F', 'Himawari-8'], 7: ['Elektro-L N3', 'FY-3C'], 9: ['FY-2F', 'Elektro-L N3'], 11: ['Elektro-L N3', 'FY-3C'], 14: ['Elektro-L N3', 'FY-3C']}, (0.9736514472240545, 58.0): {3: ['FY-2F', 'Elektro-L N3'], 5: ['Elektro-L N3', 'FY-3C'], 7: ['FY-3C', 'Elektro-L N3', 'CloudSat', 'Himawari-8', 'FY-2F'], 9: ['Elektro-L N3', 'Himawari-8', 'FY-2F'], 11: ['FY-3C']}, (0.9459952272342697, 59.0): {3: ['Elektro-L N3', 'DMSP F-16', 'FY-2F', 'Himawari-8'], 5: ['Elektro-L N3', 'FY-3C'], 7: ['Elektro-L N3', 'FY-3C'], 9: ['FY-2F', 'Elektro-L N3'], 11: ['FY-3C', 'Elektro-L N3', 'CloudSat', 'Himawari-8', 'FY-2F']}, (0.9447922509218573, 62.0): {3: ['Elektro-L N3', 'DMSP F-16', 'FY-2F', 'Himawari-8'], 7: ['Elektro-L N3', 'FY-3C'], 9: ['FY-2F', 'Elektro-L N3'], 11: ['FY-3C', 'Elektro-L N3', 'CloudSat', 'Himawari-8', 'FY-2F']}}, {}, {}, {}, {(0.5551598067865497, 31.0): {1: ['NOAA-18', 'Kanopus-V-IR'], 2: ['Meteosat-9', 'Meteor-M N2', 'NOAA-18'], 3: ['Meteosat-9'], 5: ['Kanopus-V-IR', 'Meteosat-9'], 6: ['NOAA-18', 'Kanopus-V-IR'], 7: ['NOAA-18', 'Meteor-M N2'], 8: ['Meteosat-9'], 9: ['Meteosat-9', 'NOAA-18', 'Kanopus-V-IR'], 10: ['Meteosat-9'], 13: ['Meteosat-9'], 14: ['Meteor-M N2']}}, {}, {(0.5782190716946202, 38.0): {1: ['Elektro-L N3'], 2: ['Elektro-L N3'], 6: ['Elektro-L N3'], 12: ['Elektro-L N3']}, (0.9471657213542387, 43.0): {1: ['FY-2E', 'Elektro-L N3'], 6: ['FY-2E', 'Elektro-L N3'], 8: ['FY-2E', 'Elektro-L N3'], 13: ['FY-2E', 'Elektro-L N3']}}, {}, {(0.8382099873199227, 44.0): {5: ['FY-2E'], 8: ['Meteor-M N2'], 9: ['FY-2E', 'Meteor-M N2']}, (0.9597205326851997, 48.0): {5: ['FY-2E', 'INSAT-3DR'], 9: ['INSAT-3DR', 'FY-2E', 'Meteor-M N2']}, (0.9599257569509411, 54.0): {5: ['FY-2E', 'INSAT-3DR'], 9: ['INSAT-3DR', 'FY-2E', 'Meteor-M N2']}}, {}, {(0.6556923539081573, 44.0): {9: ['Elektro-L N2'], 10: ['Elektro-L N2'], 13: ['Elektro-L N2']}, (0.7574801292526783, 45.0): {9: ['HJ-1A', 'Elektro-L N2'], 13: ['Elektro-L N2']}}, {}, {}, {}, {(0.5272764072835849, 37.0): {5: ['FY-4A', 'Himawari-9'], 6: ['FY-4A', 'Himawari-9'], 8: ['FY-3D'], 10: ['FY-4A', 'Himawari-9']}}, {}, {}, {}, {(0.7472864711081207, 37.0): {3: ['Meteor-M N2'], 6: ['FY-2E'], 7: ['FY-2E', 'Kanopus-V N3'], 8: ['Meteor-M N2', 'FY-2E'], 10: ['Kanopus-V N4', 'Meteor-M N2', 'FY-2E'], 13: ['Meteor-M N2', 'FY-2E']}, (0.6727863125766055, 41.0): {6: ['FY-2E'], 7: ['FY-2E'], 8: ['Meteor-M N2', 'FY-2E']}, (0.7777868371065774, 42.0): {7: ['FY-2E', 'Kanopus-V N3'], 8: ['Meteor-M N2'], 11: ['FY-2E']}, (0.7147382524441127, 45.0): {7: ['FY-2E', 'Kanopus-V N3'], 8: ['Kanopus-V N4', 'Meteor-M N2', 'FY-2E'], 10: ['Kanopus-V N4', 'Meteor-M N2', 'FY-2E'], 11: ['FY-2E'], 12: ['FY-2E']}}], 'Benchmark Team': []}

example_team_nsats = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 36.0, 37.0, 38.0, 39.0, 40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 48.0]
example_team_scores = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.6669491354123632, 0.6669491354123632, 0.7186995484491399, 0.7543594955632654, 0.7559239311005665, 0.8310820695776377, 0.8310820695776377, 0.8937760675712058, 0.8961256935702031, 0.8961256935702031, 0.918093372992493, 0.920056538253757, 0.920056538253757, 0.9657397917974198, 0.9657397917974198, 0.9884554492720875, 0.9884554492720875, 0.9884554492720875, 0.9884554492720875, 0.9884554492720875, 0.9884554492720875, 0.9952830826299737, 0.9968550444144471]

def compute_pareto_front(population, objective_sign):
    pop_size = len(population)
    obj_num = 2

    domination_counter = [0] * pop_size

    for i in range(pop_size):
        for j in range(i+1, pop_size):
            # check each objective for dominance
            dominate = [0] * obj_num
            for k in range(obj_num):
                if population[i][k] > population[j][k]:
                    dominate[k] = objective_sign[k]*1
                elif population[i][k] < population[j][k]:
                    dominate[k] = objective_sign[k]*-1
            if -1 not in dominate and 1 in dominate:
                domination_counter[j] += 1
            elif -1 in dominate and 1 not in dominate:
                domination_counter[i] += 1

    pareto_solutions = []
    for i in range(len(domination_counter)):
        if domination_counter[i] == 0:
            pareto_solutions.append(population[i])
    return pareto_solutions

example_team_points = list(zip(example_team_nsats, example_team_scores))

simulation_teams_points = []
for simulation in simulation_teams["Full Pipeline"]:
    if simulation:
        for point, team in simulation.items():
            simulation_teams_points.append((point[1], point[0]))

example_pareto = compute_pareto_front(example_team_points, [-1, 1])
simulations_pareto = compute_pareto_front(simulation_teams_points, [-1, 1])

example_pareto_x = [x[0]/14. for x in example_pareto]
example_pareto_y = [x[1] for x in example_pareto]

simulations_teams_x = [x[0]/14. for x in simulation_teams_points]
simulations_teams_y = [x[1] for x in simulation_teams_points]
simulations_pareto_x = [x[0]/14. for x in simulations_pareto]
simulations_pareto_y = [x[1] for x in simulations_pareto]

plt.plot(simulations_teams_x, simulations_teams_y, color="gray", marker="o", linestyle='')
plt.plot(example_pareto_x, example_pareto_y, color="red", marker="o", linestyle='')
plt.plot(simulations_pareto_x, simulations_pareto_y, color="blue", marker="o", linestyle='')
plt.legend(["Dominated points", "Benchmark team", "Our simulations"])
plt.title("Pareto front of teams (top left is better)")
plt.xlabel("Mean number of satellites used/day")
plt.ylabel("P(success)")

plt.show()