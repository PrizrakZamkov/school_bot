from openpyxl import load_workbook
def get_data():
    book = load_workbook(filename="timetable.xlsx")
    sheet = book['1']
    dict = {}
    for j in range(65,91):

        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        dict[name] = []
        data = []
        for i in range(2,11):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(11,20):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(20,28):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(28,36):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict[name].append(data)
    for j in range(65,91):
        letter = chr(j)
        name = str(sheet[letter+'1'].value)
        data = []
        for i in range(36,43):
            if sheet[letter+str(i)].value != None:
                data.append(sheet[letter+str(i)].value)
        dict[name].append(data)
    return dict