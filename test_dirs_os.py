import os
import platform

system = platform.system()

def get_all_xlsx(dirname):
    dirfiles = os.listdir(dirname)

    fullpaths = map(lambda name: os.path.join(dirname, name), dirfiles)

    files = []

    for file in fullpaths:
        if os.path.isfile(file):
            if system == 'Windows':
                name = file.split('\\')[1]
                files.append(rf"{dirname}\{name}")
            elif system == 'Linux':
                name = file.split('\\')[0]
                files.append(rf"{name}")

    return list(files)
