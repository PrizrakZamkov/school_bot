from openpyxl import load_workbook
from test_dirs_os import get_all_xlsx


def get_data_students():
    tables_name = get_all_xlsx('student_timetables')
    dict_s = {}
    for i in tables_name:
        book = load_workbook(i)
        sheet = book['1']
        for j in range(1, 30):
            if sheet.cell(row=1, column=j).value != None:
                name = str(sheet.cell(row=1, column=j).value).lower()
                dict_s[name] = []
                for day in range(5):
                    data = []
                    for f in range(day*9 + 2, day*9 + 11):
                        if sheet.cell(row=f, column=j).value != None:
                            data.append(sheet.cell(row=f, column=j).value)
                    dict_s[name].append(data)
    return dict_s
