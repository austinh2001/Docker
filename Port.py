import os
import subprocess
import tarfile

import docker
import numpy
from boututils.showdata import showdata
import boutdata

class Port:
    set_lib_library_path_cmd = "export LD_LIBRARY_PATH=home/boutuser/BOUT-next/lib"
    def __init__(self, image, shared_folder = None):
        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient(timeout=600)
        except:
            raise Exception("Docker Desktop is not open.")
        # get the container id from the file
        try:
            with open("container_id.txt", "r") as f:
                container_id = f.read()
        except FileNotFoundError:
            container_id = None

        if (shared_folder is None):
            shared_folder = self.convert_local_path_to_container_path(os.getcwd())

        if(container_id is None):
            self.client.volumes.create("bout-img-shared", driver="local")
            self.container = self.client.containers.run(image, stdout=True, detach=True, volumes={"/home/boutuser/bout-img-shared/": {"bind":"//C/Users/austi/Docker/", "mode" : "rw"}}, volume_driver = "local", environment={"LD_LIBRARY_PATH": "/home/boutuser/BOUT-next/lib"}, tty=True)
            with open("container_id.txt", "w") as text_file:
                text_file.write(self.container.id)
        else:
            self.container = self.client.containers.get(container_id)
            self.container.restart()

        print("Opening Port")
        print("Port Opened")
        self.shared_folder = shared_folder

    def convert_local_path_to_container_path(self, local_path):
        if("C:\\" in local_path):
            container_path = local_path.replace("C:\\", "//C/")
        elif("C:/" in local_path):
            container_path = local_path.replace("C:/", "//C/")
        elif ("C://" in local_path):
            container_path = local_path.replace("C://", "//C/")
        return container_path

    def getTarArchive(self, source, destination):
        strm, stat = self.api_client.get_archive(self.container.id, source)
        folder_name = os.path.basename(os.path.normpath(source))
        f = open(os.path.join(destination, f"{folder_name}.tar"), 'wb')
        for x in strm:
            f.write(x)
        f.close()
        return folder_name

    def setTarArchive(self, source, destination):
        folder_name = self.getTarArchive(source, "./")
        f = open(f"./{folder_name}.tar", 'rb')
        exec_dict = self.api_client.exec_create(self.container.id, f"rm -r /{os.path.join(destination, folder_name)}")
        response = self.api_client.exec_start(exec_dict['Id'])
        success = self.api_client.put_archive(self.container.id, destination, f)
        f.close()

    def __del__(self):
        try:
            print("Closing Port")
            self.container.stop()
            print("Port Closed")
        except(AttributeError):
            pass
