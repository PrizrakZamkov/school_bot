from openpyxl import load_workbook
from test_dirs_os import get_all_xlsx

def get_data_teachers():
    dict_t = {}

    for xlsx_name in get_all_xlsx('teacher_timetables'):
        book = load_workbook(filename=xlsx_name)
        sheet = book['teachers']  # название листа в файле
        index = 4
        while sheet['B' + str(index)].value:
            name = str(sheet['B' + str(index)].value).split(' ')[0].lower()
            dict_t[name] = []
            current_sheet = 67
            for i in range(5):
                dict_t[name].append([])
                for j in range(9):
                    letter = current_sheet
                    if letter > 90:
                        letter = str(chr(65) + chr(65 + letter - 91))
                    else:
                        letter = chr(letter)
                    next = sheet[letter + str(index)].value
                    if next:
                        dict_t[name][i].append(next)
                    current_sheet += 1

            index += 1
    return dict_t
