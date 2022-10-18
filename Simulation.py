import os
import shutil
import subprocess
import tarfile
import time

import docker
import matplotlib.pyplot as plt
import numpy
from boututils.showdata import showdata
from boutdata.collect import dimensions
import boutdata

from Port import Port


class Simulation:
    image = "boutproject/bout-next:4cee87c-arch"
    port = Port(image)
    source_directory = "/home/boutuser/BOUT-next/examples/"

    def __init__(self, simulation_name):
        self.api_client = None
        self.simulation_name = simulation_name
        self.simulation_folder_path = os.path.join(os.path.join(os.getcwd(), "Simulations"), simulation_name)
        if(not self.exists()):
            self.createSimulationFolder(self.simulation_name)
            try:
                self.download()
            except:
                pass

    @classmethod
    def simulationExists(cls, simulation_name):
        simulation_folder_path = os.path.join(os.path.join(os.getcwd(), "Simulations"), simulation_name)
        return os.path.isdir(os.path.join(simulation_folder_path, simulation_name))

    def exists(self):
        return self.simulationExists(self.simulation_name)

    @classmethod
    def hasSimulationResults(cls, simulation_name):
        simulation_results_folder_path = os.path.join(os.path.join(os.getcwd(), "Results"), simulation_name, "data")
        return any("dmp" in file for file in os.listdir(simulation_results_folder_path))

    def hasResults(self):
        return self.hasSimulationResults(self.simulation_name)

    @classmethod
    def downloadFolder(cls, source, destination):
        cls.port.getTarArchive(source, destination)
        folder_name = os.path.basename(os.path.normpath(source))
        tarfile.open(os.path.join(destination, f"{folder_name}.tar")).extractall(destination)
        os.remove(os.path.join(destination, f"{folder_name}.tar"))

    @classmethod
    def uploadFolder(cls, folder_path, destination):
        cls.port.setTarArchive(folder_path, destination)

    @classmethod
    def uploadSimulation(cls, simulation_name):
        # TODO Uploading simulations does not update the files???
        simulation_folder = f"home/boutuser/bout-img-shared/Simulations/{simulation_name}"
        cls.createSimulationFolder(simulation_name)
        cls.uploadFolder(simulation_folder, cls.source_directory)

    def upload(self):
        self.uploadSimulation(self.simulation_name)

    @classmethod
    def downloadSimulation(cls, simulation_name):
        wd = f"/{os.path.join(cls.source_directory, simulation_name)}"
        simulations_folder = os.path.join(os.getcwd(), "Simulations")
        cls.createSimulationFolder(simulation_name)
        cls.downloadFolder(wd, simulations_folder)

    def download(self):
        self.downloadSimulation(self.simulation_name)

    @classmethod
    def downloadExample(cls, example_name, simulation_name):
        wd = f"/{os.path.join(cls.source_directory, example_name)}"
        destination = os.path.join(os.getcwd(), "Simulations")
        cls.port.getTarArchive(wd, destination)
        os.rename(destination + "/" + example_name + ".tar", destination + "/" + simulation_name + ".tar")
        cls.createSimulationFolder(simulation_name)
        for member in tarfile.open(destination + "/" + simulation_name + ".tar").getmembers():
            tarfile.open(destination + "/" + simulation_name + ".tar").extract(member, destination + "/" + simulation_name)
        # put the file contents of destination destination + "/" + simulation_name + "/" + example_name into destination + "/" + simulation_name
        for file in os.listdir(destination + "/" + simulation_name + "/" + example_name):
            try:
                os.rename(destination + "/" + simulation_name + "/" + example_name + "/" + file, destination + "/" + simulation_name + "/" + file)
            except(FileExistsError):
                try:
                    os.remove(destination + "/" + simulation_name + "/" + file)
                except(PermissionError):
                    shutil.rmtree(destination + "/" + simulation_name + "/" + file)
                os.rename(destination + "/" + simulation_name + "/" + example_name + "/" + file, destination + "/" + simulation_name + "/" + file)
        os.rmdir(destination + "/" + simulation_name + "/" + example_name)
        os.remove(os.path.join(destination, f"{simulation_name}.tar"))

    @classmethod
    def runSimulation(cls, simulation_name):
        # Uploading the current version of the simulation and downloading the simulation results seemingly allows for
        # faster execution times
        cls.uploadSimulation(simulation_name)
        wd = os.path.join(cls.source_directory, simulation_name)
        exec_dict = cls.port.api_client.exec_create(cls.port.container.id, workdir=wd, cmd="ls")
        file_response = cls.port.api_client.exec_start(exec_dict['Id'])
        files = file_response.decode("utf-8").split("\n")
        simulation_file = simulation_name

        for file in files:
            if (".cxx" in file):
                simulation_file = file.replace(".cxx", "")
                break

        command = f"mpiexec -np 1 ./{simulation_file}"

        exec_dict = cls.port.api_client.exec_create(cls.port.container.id, workdir=wd, cmd="mkdir data")
        cls.port.api_client.exec_start(exec_dict['Id'])
        exec_dict = cls.port.api_client.exec_create(cls.port.container.id, workdir=wd, cmd="make")
        cls.port.api_client.exec_start(exec_dict['Id'])
        exec_dict = cls.port.api_client.exec_create(cls.port.container.id, workdir=wd, cmd=command)
        live_response = cls.port.api_client.exec_start(exec_dict['Id'], stream=True)

        results_folder = os.path.join(os.getcwd(), "Results")
        simulation_folder = os.path.join(results_folder, simulation_name)
        try:
            os.mkdir(simulation_folder)
        except:
            pass

        with open(os.path.join(simulation_folder, f"{simulation_name}.txt"), "w") as f:
            for line in live_response:
                print(line.decode("utf-8"))
                try:
                    f.write(line.decode("utf-8"))
                except(UnicodeEncodeError):
                    f.write("?")

        if (not os.path.exists(simulation_folder)):
            os.mkdir(simulation_folder)

        cls.downloadSimulation(simulation_name)
        cls.downloadFolder(wd + "/data", simulation_folder)

    def run(self):
        self.runSimulation(self.simulation_name)

    @classmethod
    def showSimulation(cls, simulation_name, variable, plot = True):
        fps = 30
        dpi = 300
        results_folder = os.path.join(os.getcwd(), "Results")
        simulation_folder = os.path.join(results_folder, simulation_name)
        data_folder = simulation_folder + "/data"
        from boutdata.data import BoutData
        print(BoutData(path=data_folder)['outputs'].keys())
        data_vector = boutdata.collect(variable, path=data_folder) # Read data as NumPy array [t,x,y,z]
        dims = dimensions(variable, path=data_folder)
        dim_sizes = numpy.shape(data_vector)

        valid_dims = []
        for i in range(len(dims)):
            if(dim_sizes[i] != 1):
                valid_dims.append(None)
            else:
                valid_dims.append(1)

        collected_data = data_vector[slice(0,valid_dims[0],1),slice(0,valid_dims[1],1),slice(0,valid_dims[2],1),slice(0,valid_dims[3],1)]
        print(numpy.shape(numpy.squeeze(collected_data)))
        if(plot):
            showdata(numpy.squeeze(collected_data), titles=[simulation_name + f": {variable}"], return_animation=False)
            showdata(numpy.squeeze(collected_data), titles=[simulation_name + f": {variable}"], movie=os.path.join(simulation_folder, f"{simulation_name}_{variable}.mp4"), fps=fps, dpi=dpi)
        else:
            showdata(numpy.squeeze(collected_data), titles=[simulation_name + f": {variable}"], movie=os.path.join(simulation_folder, f"{simulation_name}_{variable}.mp4"), fps=fps, dpi=dpi)

        #TODO: Add a case for 4D data (i.e. 3D data with a time dimension) since showdata doesnt support this.


    def show(self, variable, plot = True):
        self.showSimulation(self.simulation_name, variable, plot)

    @classmethod
    def createSimulationFolder(cls, simulation_name):
        simulations_folder = os.path.join(os.getcwd(), "Simulations")
        simulation_folder = os.path.join(simulations_folder, simulation_name)
        try:
            os.mkdir(simulation_folder)
        except(FileExistsError):
            pass

    @classmethod
    def createFromExample(cls, example_name, simulation_name):
        cls.downloadExample(example_name, simulation_name)
        #return cls(simulation_name)
