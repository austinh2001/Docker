import os
from matplotlib import pyplot as plt
from Port import Port
from Simulation import Simulation

#example_name = "orszag-tang"
example_name = "conduction"
simulation = Simulation(example_name)
# TODO might be better to try and run all simulations in the bout-img-shared folder rather than examples.
#  Issues with uploading
simulation.run()
simulation.show(variable="T")
#docker_port.showSimulation(example_name, variable="n")

#df = xbout.open_boutdataset("./"+example_name+"/data/BOUT.dmp.*.nc","./"+example_name+"/data/BOUT.inp")
#from boutdata import collect
#cwd = os.getcwd()
#variable = "n"
#data_vector = collect(variable,path=f"{cwd}/{example_name}/data/") # Read data as NumPy array [t,x,y,z]

from boututils.plotdata import plotdata

#from boututils.showdata import showdata
#anim = showdata(data_vector[:,:,0,:],return_animation=True)
#anim.save("test.gif",fps=60)
