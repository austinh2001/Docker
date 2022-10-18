from Simulation import Simulation

simulation_names = ["conduction", "blob2d", "orszag-tang"]
variables = ["T", "n", "density"]
for index, simulation_name in enumerate(simulation_names):
    simulation = Simulation(simulation_name)
    variable = variables[index]
    if(simulation.hasResults()):
        simulation.show(variable=variable, plot=True)
    else:
        print(f"Simulation {simulation_name} has not been run yet")
        simulation.run()
        simulation.show(variable=variable, plot=True)


