import os
from matplotlib import pyplot as plt
from Port import Port
from Simulation import Simulation
# TODO: If the simulation fails to run, ensure that the makefile has the right BOUT_TOP
simulation_name = "conduction"
simulation = Simulation(simulation_name)
#simulation.run()
simulation.show(variable="T", plot=True)
#simulation.show(variable="phi", plot=True)
#docker_port.showSimulation(example_name, variable="n")
