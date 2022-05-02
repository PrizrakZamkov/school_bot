from openpyxl import load_workbook
from test_dirs_os import get_all_xlsx
def get_data_students():
    tables_name = get_all_xlsx('student_timetables')
    dict_s = {}
    for i in tables_name:
        book = load_workbook(i)
        sheet = book['1']
        for j in range(1,30):
            if sheet.cell(row=1, column=j)!= None:
                name = str((sheet.cell(row=1, column = j).value))
                dict_s[name] = []
                data = []
                for f in range(2,11):
                    if sheet.cell(row = f, column = j).value != None:
                        data.append(sheet.cell(row = f, column = j).value)
                dict_s[name].append(data)
                data = []
                for f in range(11,20):
                    if sheet.cell(row = f, column = j).value != None:
                        data.append(sheet.cell(row = f, column = j).value)
                dict_s[name].append(data)
                data = []
                for f in range(20,28):
                    if sheet.cell(row = f, column = j).value != None:
                        data.append(sheet.cell(row = f, column = j).value)
                dict_s[name].append(data)
                data = []
                for f in range(28,36):
                    if sheet.cell(row = f, column = j).value != None:
                        data.append(sheet.cell(row = f, column = j).value)
                dict_s[name].append(data)
                data = []
                for f in range(36,43):
                    if sheet.cell(row = f, column = j).value != None:
                        data.append(sheet.cell(row = f, column = j).value)
                dict_s[name].append(data)
    return dict_s