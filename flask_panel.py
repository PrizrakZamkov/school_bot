from flask import Flask, render_template, request,flash, redirect, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os

# расширения файлов, которые разрешено загружать
ALLOWED_EXTENSIONS = {'xls', 'xlsx','txt'}

app = Flask(__name__)

UPLOAD_FOLDER = 'update_timetable'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """ Функция проверки расширения файла """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # проверим, передается ли в запросе файл 
        if 'file' not in request.files:
            print(request.files)
            return redirect(request.url)
        file = request.files['file']
        # Если файл не выбран, то браузер может
        # отправить пустой файл без имени.
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # безопасно извлекаем оригинальное имя файла
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # типо небезопасное сохранение снизу
            #f = request.files['file']
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
            
    return render_template('index.html')

# @app.route('/download-file/<filename>')
# def download_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/download')
def download_file():
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'student_timetables')
    path = os.listdir(path)[0]
    return send_file(rf"student_timetables\timetables.xlsx", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False)

