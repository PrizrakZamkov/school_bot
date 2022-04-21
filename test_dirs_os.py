import os


def get_all_xlsx():
    dirname = 'student_timetables'
    dirfiles = os.listdir(dirname)

    fullpaths = map(lambda name: os.path.join(dirname, name), dirfiles)

    files = []

    for file in fullpaths:
        if os.path.isfile(file):
            print("file")
            files.append(file.split("\\")[1])

    return list(files)
