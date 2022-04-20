from openpyxl import load_workbook
def get_data_students():
    book = load_workbook(filename="timetable.xlsx")
    sheet = book['1']
    dict_s = {}
    for j in range(65,91):

        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        dict_s[name] = []
        data = []
        for i in range(2,11):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict_s[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(11,20):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict_s[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(20,28):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict_s[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(28,36):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict_s[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(36,43):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict_s[name].append(data)
    return dict_s