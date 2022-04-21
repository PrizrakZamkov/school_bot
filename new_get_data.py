from openpyxl import load_workbook
from school_bot.test_dirs_os import get_all_xlsx

def get_data_students():
    dict_s = {}
    for xlsx_name in get_all_xlsx('student_timetables'):
        book = load_workbook(filename=xlsx_name)
        sheet = book['1']
        for indent in range(2,37,9):
            for j in range(65, 91):
                letter = chr(j)
                name = str(sheet[letter + '1'].value)
                dict_s[name] = []
                data = []
                for i in range(indent, 11):
                    if sheet[letter + str(i)].value != None:
                        data.append(sheet[letter + str(i)].value)
                dict_s[name].append(data)
    return dict_s
