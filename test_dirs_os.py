import os
import platform

system = platform.system()

def get_all_xlsx(dirname):
    dirfiles = os.listdir(dirname)

    fullpaths = map(lambda name: os.path.join(dirname, name), dirfiles)

    files = []

    for file in fullpaths:
        if os.path.isfile(file):
            name = file.split('\\')[1]

            if system == 'Windows':
                files.append(rf"{dirname}\{name}")
            elif system == 'Linux':
                files.append(rf"{name}")

    return list(files)
