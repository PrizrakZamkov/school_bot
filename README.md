"# school_bot" 
Инструкция по запуску
=====================
- pip install -r requirements.txt
- python3 bot.py

Формат расписаний
=====================
- Расписание в .xlsx файле
- Имя листа '1'
- 1 строка: классы (Пример: '5А') 
- 2-46 строка: названия уроков (5 дней по девять строк) 

- Расписания по умолчанию должны находиться в папке 'student_timetables'

Для админов
===========
Добавление/Обновление расписания
--------------------------------
- Команда для добавления: Обновить расписание
- Расписание должно быть в правильном формате

.env
===========
- TOKEN = 'токен бота'
- ADMIN_KEY = 'ключ добавления админа' (при вводе ключа в сообщении выдаются права администратора)

