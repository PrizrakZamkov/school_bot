import os


def get_all_xlsx(dirname):
    dirfiles = os.listdir(dirname)

    fullpaths = map(lambda name: os.path.join(dirname, name), dirfiles)

    files = []

    for file in fullpaths:
        if os.path.isfile(file):
            name = file.split('\\')[1]
            files.append(rf"{dirname}\{name}")

    return list(files)
