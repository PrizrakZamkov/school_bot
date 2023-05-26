'''
    Запуск бота и сервера
'''
from datetime import datetime, time, timedelta
import shutil
import sys

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram import Bot, types, Dispatcher, executor
from get_tgd import get_data_students
from get_tgd_teachers import get_data_teachers
from db import create_connection, execute_query, execute_read_query

from dotenv import dotenv_values
from pathlib import Path
import os
from logging import getLogger, StreamHandler, Formatter, INFO
import pandas as pd

import platform
  
import asyncio
import aioschedule
import nest_asyncio
    
# FOR SERVER    
from flask import Flask, render_template, request,flash, redirect, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os



nest_asyncio.apply()
system = platform.system()


logger = getLogger(__name__)
logger.setLevel(INFO)

handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.addHandler(handler)

config = dict(dotenv_values(".env") )
TOKEN = config["TOKEN"]
ADMIN_KEY = config["ADMIN_KEY"]

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data = {}

data_teachers = {}
connection = None
# ТОЛЬКО ДЛЯ ПОСЛЕДНЕГО ОБНОВЛЕНИЯ
# ЖЕЛАТЕЛЬНО ПОМЕНЯТЬ НА execute_query и execute_read_query потом

cursor_for_update = None

user_params = [
    'id',
    'user_id',
    'number',
    'word',
    'is_teacher',
    'teacher_last_name',
    'is_admin',
    'notification_time',
    'notification_before_lesson'
]
days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']

interval_start_hour, interval_start_minute = 5, 0 # 5:00
interval_end_hour, interval_end_minute = 9, 0 # 09:00
interval_start, interval_end = "5:00",  "09:00"
time_of_lesson = [
    {
        "start": "8:30",
        "end": "9:15",
    },
    {
        "start": "9:35",
        "end": "10:20",
    },
    {
        "start": "10:40",
        "end": "11:25",
    },
    {
        "start": "11:45",
        "end": "12:30",
    },
    {
        "start": "12:50",
        "end": "13:35",
    },
    {
        "start": "13:55",
        "end": "14:40",
    },
    {
        "start": "15:00",
        "end": "15:45",
    },
    {
        "start": "15:55",
        "end": "16:40",
    },
    # {
    #     "start": "16:50",
    #     "end": "17:30",
    # },
    {
        "start": "18:00",
        "end": "19:00",
    },
]

def make_time_with_delta(time: str, min_time_delta: int):
    # возвращает time - min_time_delta
    dt = datetime.strptime(time, '%H:%M')  # преобразуем строку в объект datetime
    dt -= timedelta(minutes=min_time_delta)  # вычитаем заданное количество минут
    return dt.strftime('%H:%M')

# за time_delta до звонка будет приходить уведомление о следущем уроке
time_delta = 5
# время для напоминаний перед уроками
times_for_lesson_notifications = [make_time_with_delta(i["start"], time_delta) for i in time_of_lesson]

menu_for_get_timetable = types.ReplyKeyboardMarkup(resize_keyboard=True)
#menu_for_get_timetable.row("Помощь", "Получить расписание")
menu_for_get_timetable.row("Получить расписание")
menu_for_get_timetable.row("Помощь", "Настроить напоминания")

menu_time_week = types.InlineKeyboardButton(
    text="На неделю",
    callback_data="time_week")
menu_time_today = types.InlineKeyboardButton(
    text="На сегодня",
    callback_data="time_today")
menu_time_tomorrow = types.InlineKeyboardButton(
    text="На завтра",
    callback_data="time_tomorrow")
menu_time = types.InlineKeyboardMarkup().row(menu_time_week, menu_time_today, menu_time_tomorrow)

teacher = types.InlineKeyboardButton(
    text="Я учитель",
    callback_data="person_teacher")
student = types.InlineKeyboardButton(
    text="Я ученик",
    callback_data="person_student")
menu_techer_student = types.InlineKeyboardMarkup().row(teacher, student)


menu_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_admin.row("Помощь", "Получить расписание")
menu_admin.row("Добавить админа", "Обновить расписание")



lesson_notifications_button = types.InlineKeyboardButton(
    text="Вкл/Выкл уведомления",
    callback_data="lesson_notification")
menu_lesson_notifications_button = types.InlineKeyboardMarkup().row(lesson_notifications_button)

async def saveDataInExcel():
    # TODO: СДЕЛАТЬ ЧТО-ТО с data, которая уже не используется
    dir = 'student_timetables'
    shutil.rmtree(dir)
    os.mkdir(dir)
    save_data = {}
    for key in data:
        save_data[key] = []
        for item in data[key]:
            save_data[key].extend(item)
            save_data[key].extend(['']*(9-len(item)))
    df = pd.DataFrame(save_data)
    if system == 'Windows':
        df.to_excel('./student_timetables/timetables.xlsx', sheet_name='1', index=False)
    elif system == 'Linux':
        df.to_excel(rf'.\student_timetables\timetables.xlsx', sheet_name='1', index=False)
    logger.info('Обновлено расписание')
    

def generate_schedule(key, schedule_data):
    result = []
    for day in range(5):
        if key[0] in "0123456789":
            result_day = f"\U0001F514 {key.upper()} {days[day]}: \n\n"
        else:
            result_day = f"\U0001F514 {days[day]}:\n\n"
        for index, lesson in enumerate(schedule_data[day]):
            letter = "{} - {}:    {}\n"
            result_day += letter.format(
                time_of_lesson[index]['start'],
                time_of_lesson[index]['end'],
                lesson
            )
        result.append(result_day)
    return result
def update_schedule(schedule_data):
    new_connection = create_connection("db.sqlite")
    new_cursor = new_connection.cursor()
    # для каждой записи в словаре, который содержит ключ class_or_last_name и список расписаний для каждого дня недели, добавляем или обновляем запись в таблице schedules
    for k, v in schedule_data.items():
        schedule = generate_schedule(k, v)
        # проверяем, существует ли запись с class_or_last_name в таблице, обновляем строку или выполняем вставку в зависимости от результата
        new_cursor.execute(f"SELECT COUNT(*) FROM schedules WHERE class_or_last_name=?", (k,))
        if new_cursor.fetchone()[0] > 0:
            # обновляем 5 полей расписаний в существующей строке
            new_cursor.execute(f"UPDATE schedules SET Monday=?, Tuesday=?, Wednesday=?, Thursday=?, Friday=? WHERE class_or_last_name=?", (*schedule, k))
        else:
            # вставляем новую строку в таблицу со значениями class_or_last_name и пять полями 
            new_cursor.execute(f"INSERT INTO schedules (class_or_last_name, Monday, Tuesday, Wednesday, Thursday, Friday) VALUES (?, ?, ?, ?, ?, ?)", (k, *schedule))

    # сохраняем изменения
    new_connection.commit()
    new_connection.close()

@dp.message_handler(commands="start")
async def callback_start(message: types.Message):
    """
        Первое сообщение
    """
    await bot.send_message(message.chat.id,
                           "\U0001F64B Привет!"
                           " Я бот, который поможет найти тебе твоё расписание.")
    await bot.send_message(message.chat.id,
                           "Кем вы являетесь?",
                           reply_markup=menu_techer_student)


@dp.message_handler(commands="relog")
async def callback_relog(message: types.Message):
    """
        Заново начать регистрацию
    """
    await start_input_person(message)



@dp.message_handler(commands="help")
async def callback_help(message: types.Message):
    """
        Туториал для пользователей
    """
    await bot.send_message(message.chat.id,
                           "Список команд\n"
                           "Зарегистрироваться заново - /relog\n"
                           "Открыть меню - /menu\n"
                           "Открыть расписание - вписать 'Получить расписание'\n"
                           "Отключить уведомления - /disable")


def get_user(user_id: int):
    """
        Пполучить пользователя из базы данных, либо None
    """
    select_users = "SELECT * from users"
    users = execute_read_query(connection, select_users)

    for user in users:
        if int(user[1]) == user_id:
            return_user = {}
            for i in range(len(user)):
                return_user[user_params[i]] = user[i]
            return return_user
    return None

@dp.message_handler(commands="menu")
async def callback_menu(message: types.Message):
    """
        Открыть меню
    """
    if get_user(message.from_user.id)['is_admin']:
        current_menu = menu_admin
    else:
        current_menu = menu_for_get_timetable
    await bot.send_message(message.chat.id,
                           "Меню открыто", reply_markup=current_menu)

async def create_user(user_id, number=0, word="", is_teacher=0, teacher_last_name="", is_admin=0):
    """
        Создать пользователя, либо обновить существующего
    """
    if not get_user(user_id):
        create_users = f"""
            INSERT INTO
              users (user_id, number, word, is_teacher, teacher_last_name, is_admin)
            VALUES
              ({user_id}, {number}, '{word}', {int(is_teacher)}, '{teacher_last_name}', {int(is_admin)});
            """
        execute_query(connection, create_users)

        logger.info(f'Создан новый пользователь: user_id : {user_id},'
                        f' Класс : {number},'
                        f' Буква : {word}, is_teacher : {int(is_teacher)}, '
                        f'Фамилия : "{teacher_last_name}", is_admin : {int(is_admin)}')
    else:
        if get_user(user_id)['is_admin']:
            update_description = f"""
            UPDATE
                users
            SET
              number = {number},
              word = "{word}",
              is_teacher = {int(is_teacher)},
              teacher_last_name = "{teacher_last_name}",
              is_admin = {1}
            WHERE
              user_id = {user_id}
            """
            execute_query(connection, update_description)
        else:
            update_description = f"""
            UPDATE
                users
            SET
              number = {number},
              word = "{word}",
              is_teacher = {int(is_teacher)},
              teacher_last_name = "{teacher_last_name}",
              is_admin = {int(is_admin)}
            WHERE
              user_id = {user_id}
            """
            execute_query(connection, update_description)
        logger.info(f'Обновление пользователя: user_id : {user_id},'
                        f' Класс : {number},'
                        f' Буква : {word}, is_teacher : {int(is_teacher)}, '
                        f'Фамилия : "{teacher_last_name}", is_admin : {int(is_admin)}')

async def get_schedule_from_day(user_id, day):
    global connection
    global cursor_for_update
    # создаем список дней недели
    days_for_sqlite = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # получаем соответствующее поле расписания по выбранному дню
    day_field = days_for_sqlite[day]
    
    user_data = get_user(user_id)
    if user_data['is_teacher'] == 1:
        cursor_for_update.execute(f"SELECT {day_field} FROM schedules WHERE class_or_last_name = ?", (f"{user_data['teacher_last_name']}".lower(),))
    else:
        cursor_for_update.execute(f"SELECT {day_field} FROM schedules WHERE class_or_last_name = ?", (f"{user_data['number']}{user_data['word']}".lower(),))
    
    # выполняем запрос к базе данных, выбирая расписание для определенного класса или фамилии и для указанного дня
    row = cursor_for_update.fetchone()
    
    # возвращаем расписание для выбранного класса/фамилии и выбранного дня
    if row is not None:
        return str(row[0])
    else:
        logger.exception(f'Ошибка при попытке получить расписания. Пользователь: {get_user(user_id)}')
        return "Ошибка... Проверьте введенный класс или введённую фамилию, если вы учитель" \
               " (Пропишите /relog и введите нужный класс)"


async def start_input_person(message):
    """
        Учитель / Ученик
    """
    await bot.send_message(message.chat.id, "Кем вы являетесь?",
                           reply_markup=menu_techer_student)


class Teacher(StatesGroup):
    """
        Фамилия учителя
    """
    teacher_last_name = State()

async def send_otmena_message(message: types.Message):
    """
        Начало операции... (впишите 'отмена') для отмены действия
    """
    await bot.send_message(message.from_user.id,
                           "Начало операции... (впишите 'отмена') для отмены действия")

@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel(message: types.Message, state: FSMContext):
    """
        Отмена
    """
    curent_state = await state.get_state()
    if curent_state is None:
        return
    await state.finish()
    await bot.send_message(message.chat.id,
                           "Опереция отменена")


async def start_input_last_name(message):
    """
        Начало регистрации для учителя
    """
    await Teacher.teacher_last_name.set()
    await send_otmena_message(message)
    await bot.send_message(message.from_user.id, "Впишите Вашу фамилию:")


@dp.message_handler(state=Teacher.teacher_last_name)
async def load_last_name(message: types.Message, state: FSMContext):
    """
        Фамилия учителя
    """
    async with state.proxy() as new_teacher:
        new_teacher['teacher_last_name'] = message.text.lower()
        await Teacher.next()
        await state.finish()
        await create_user(message.from_user.id,
                          is_teacher=1,
                          teacher_last_name=new_teacher["teacher_last_name"])

        if get_user(message.from_user.id)['is_admin']:
            current_menu = menu_admin
        else:
            current_menu = menu_for_get_timetable
        await bot.send_message(message.chat.id,
                                   '\U00002705 Теперь вы можете смотреть свое расписание',
                                   reply_markup=current_menu)



class Student(StatesGroup):
    """
        Номер и буква класса
    """
    student_number = State()
    student_word = State()


async def start_input_class(message):
    """
        Начало регистрации для ученика
    """
    await Student.student_number.set()
    await send_otmena_message(message)
    await bot.send_message(message.from_user.id, "Впишите номер класса:")


@dp.message_handler(state=Student.student_number)
async def load_number(message: types.Message, state: FSMContext):
    """
        Получает номер класса
    """
    try:
        async with state.proxy() as new_student:
            new_student['number'] = int(message.text)
        await Student.next()
        await message.reply('Введите литеру (букву) класса')
    except Exception:
        await message.reply('Введите только целое число')


@dp.message_handler(state=Student.student_word)
async def load_word(message: types.Message, state: FSMContext):
    """
        Буква класса
    """
    async with state.proxy() as new_student:
        new_student['word'] = message.text.lower()
        await Student.next()
        await state.finish()
        await create_user(message.from_user.id,
                          number=new_student["number"],
                          word=new_student["word"])
        if get_user(message.from_user.id)['is_admin']:
            current_menu = menu_admin
        else:
            current_menu = menu_for_get_timetable
        await bot.send_message(message.chat.id,
                                   "\U00002705 Теперь вы можете смотреть свое расписание,"
                                   " если вам понадобится помощь, введите /help или 'Помощь'",
                                   reply_markup=current_menu)



@dp.message_handler(Text(equals="Получить расписание"))
async def give_timetable(message: types.Message):
    """
        Отдает меню выбора расписания
    """
    await message.reply('Выберете расписание, которое вам требуется', reply_markup=menu_time)


@dp.message_handler(Text(equals="Помощь"))
async def give_help(message: types.Message):
    """
        Меню помощи
    """
    await callback_help(message)


@dp.callback_query_handler(text_contains='time_')
async def callback_time(call: types.CallbackQuery):
    """
        Расписание на
        Неделю / сегодня / завтра
    """
    if call.data and call.data.startswith("time_"):
        callback_get_time = call.data.split('_')[1]
        is_today = ['week', 'today', 'tomorrow'].index(callback_get_time)
        if is_today == 1:
            day = datetime.today().weekday()
            if day > 4:
                await bot.send_message(call.from_user.id,
                                   "Сегодня уроков нет")
            else:
                await bot.send_message(call.from_user.id,
                                   await get_schedule_from_day(call.from_user.id, day))
        elif is_today == 2:
            day = datetime.today().weekday() + 1
            if day > 4:
                day = 0
            await bot.send_message(call.from_user.id,
                                   await get_schedule_from_day(call.from_user.id, day))
        else:
            for day in range(5):
                await bot.send_message(call.from_user.id,
                                       await get_schedule_from_day(call.from_user.id, day))


@dp.callback_query_handler(text_contains='person_')
async def callback_person(call: types.CallbackQuery):
    """
        Ученик / Учитель
        (is_teacher: False / True)
    """
    if call.data and call.data.startswith("person_"):
        callback_get_person = call.data.split('_')[1]
        is_teacher = ['student', 'teacher'].index(callback_get_person)
        if is_teacher == 0:
            await start_input_class(call)
        if is_teacher == 1:
            await start_input_last_name(call)


class AddAdmin(StatesGroup):
    """
        Добавление нового админа
    """
    admin_id = State()


async def start_add_admin(message):
    """
        Начало ввода ID
    """
    await AddAdmin.admin_id.set()
    await send_otmena_message(message)
    await bot.send_message(message.from_user.id, "Впишите ID нового админа (узнать свой айди можно вписав 'ID')")



@dp.message_handler(state=AddAdmin.admin_id)
async def load_admin(message: types.Message, state: FSMContext):
    """
        ID админа
    """
    async with state.proxy() as new_admin:
        try:
            new_admin_id = int(message.text)
            try:
                await bot.send_message(new_admin_id,
                                   'Вас назначили админом бота расписаний Школы в Капотне')
            except:
                await bot.send_message(message.chat.id,
                                       'Пользователя с таким ID не существет. Попробуйте снова')
            else:
                await AddAdmin.next()
                await state.finish()
                await create_user(message.from_user.id, is_admin=True)
                await bot.send_message(message.chat.id,
                                       '\U00002705 Админ добавлен, чтобы открыть новое меню, нужно будет ввести команду /menu')
        except ValueError:
            await bot.send_message(message.chat.id,
                                   'Введите только число')



class UpdateTimetable(StatesGroup):
    """
        Обновление расписания
    """
    file = State()


async def start_update_timetable(message):
    """
        Начало Обновления расписания
    """
    await UpdateTimetable.file.set()
    await send_otmena_message(message)
    await bot.send_message(message.from_user.id, "Отправьте файл с обновлениями расписания в правильном формате (впишите 'Формат', чтобы посмотреть формат пасписания)")


@dp.message_handler(state=UpdateTimetable.file, content_types=types.ContentTypes.DOCUMENT)
async def load_timetable_file(message: types.Message, state: FSMContext):
    """
        Файл с расписанием
    """
    async with state.proxy() as update_file:
        try:
            dir = 'update_timetable'
            if os.path.exists(dir):
                shutil.rmtree(dir)
            document = message.document
            await document.download(
                destination_dir=dir,
            )
                
            if system == 'Windows':
                update_schedule(get_data_students("update_timetable/documents"))
            elif system == 'Linux':
                update_schedule(get_data_students(rf"update_timetable\documents"))
            await saveDataInExcel()
            
            await UpdateTimetable.next()
            await state.finish()
            await bot.send_message(message.chat.id,
                                   'Расписание обновлено')
        except Exception as ex:
            logger.exception(ex)
            await bot.send_message(message.chat.id,
                                   'Ошибка')



@dp.message_handler(Text(equals="Обновить расписание"))
async def start_start_update_timetable(message: types.Message):
    """
        Обновить расписание
    """
    await start_update_timetable(message)

@dp.message_handler(Text(equals="Добавить админа"))
async def start_start_add_admin(message: types.Message):
    """
        Добавить админа
    """
    await start_add_admin(message)

@dp.message_handler(Text(equals="Формат"))
async def format(message: types.Message):
    """
        Получить Формат расписания
    """
    await bot.send_message(message.chat.id,
"""
Формат расписаний\n

=================\n

Расписание в xlml файле\n

Имя листа '1'\n

1 строка: классы (Пример: '5А')\n

2-46 строка: названия уроков (5 дней по девять строк)
""")

@dp.message_handler(Text(equals=ADMIN_KEY))
async def give_admin(message: types.Message):
    """
        Админ
    """
    await create_user(message.from_user.id, is_admin=True)
    await bot.send_message(message.from_user.id, "Права администратора выданы", reply_markup=menu_admin)

@dp.message_handler(Text(equals="ID"))
async def give_ID(message: types.Message):
    """
        send id
    """
    await bot.send_message(message.from_user.id, str(message.from_user.id))

    
@dp.callback_query_handler(text_contains='lesson_notification')
async def callback_notification(call: types.CallbackQuery):
    """
        Вкл/Выкл напоминания перед уроками
    """
    await switch_notifications(call.from_user.id)
    current_state = get_notification_before_lesson_state(call.from_user.id)
    if current_state:
        await bot.send_message(call.from_user.id, "\U00002705 Напоминания перед уроком включены")
    else:
        await bot.send_message(call.from_user.id, "\U0000274C Напоминания перед уроком отключены")
    


class Notification(StatesGroup):
    """
        Настройка напоминаний
    """
    time = State()

@dp.message_handler(Text(equals="Настроить напоминания"))
async def start_set_notification_time(message: types.Message):
    """
        Запуск настройки напоминаний
    """
    await start_writing_notification_time(message)

async def start_writing_notification_time(message):
    """
        Начало ввода времени
    """
    await Notification.time.set()
    
    await bot.send_message(message.from_user.id, f"Нажав на кнопку ниже, вы можете включить/выключить уведомления за {time_delta} минут(ы) до урока", reply_markup=menu_lesson_notifications_button)
    await send_otmena_message(message)
    await bot.send_message(message.from_user.id, f"Впишите время в формате ЧЧ:ММ или ЧЧ.ММ, в которое вы хотели бы получать расписание (доступно время с {interval_start} до {interval_end})\n\nЕсли вы хотите отключить уведомления, используйте команду /disable")

def is_time_correct_string(input_string, interval_start, interval_end):
    input_string = input_string.replace('.',':')
    parts = input_string.split(':')
    if len(parts) != 2:
        return False
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        if hours < 0 or hours > 23:
            return False
        if minutes < 0 or minutes > 59:
            return False
        
        start_time = datetime.strptime(interval_start, '%H:%M').time()
        end_time = datetime.strptime(interval_end, '%H:%M').time()
        input_time = datetime.strptime(input_string, '%H:%M').time()
        #if '{:02d}:{:02d}'.format(hours, minutes) < interval_start or '{:02d}:{:02d}'.format(hours, minutes) > interval_end:
        if not(start_time <= input_time <= end_time):    
            return False
    except ValueError:
        return False
    return True
    
def set_time(input_string):
    input_string = input_string.replace('.',':')
    parts = input_string.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    #if minutes % 5 != 0:
    #    minutes = (minutes // 5) * 5   # округляем минуты до ближайшего кратного 5
    return '{:02d}:{:02d}'.format(hours, minutes)


@dp.message_handler(state=Notification.time)
async def set_notification_time(message: types.Message, state: FSMContext):
    """
        Проверка и установка времени для напоминаний
    """
    async with state.proxy() as new_time:
        notification_time = message.text
        if is_time_correct_string(notification_time, interval_start, interval_end):
            notification_time = str(set_time(notification_time))
            global connection
            command = f'''
                UPDATE
                users
                SET
                notification_time = "{notification_time}"
                WHERE
                user_id = {message.from_user.id}
            '''
            execute_query(connection, command)
            await bot.send_message(message.chat.id,
                                    f'\U000023F1 Напоминания установлены на {notification_time}, для отключения введите команду /disable')
            await Notification.next()
            await state.finish()
        else:
            await bot.send_message(message.chat.id,
                                   'Ошибка. Введите время в правильном формате')

async def disable_notifications(user_id):
    global connection
    command = f'''
        UPDATE
        users
        SET
        notification_time = ""
        WHERE
        user_id = {user_id}
    '''
    execute_query(connection, command)
    
    
@dp.message_handler(commands="disable")
async def callback_menu(message: types.Message):
    """
        Отключить напоминания 
    """
    await disable_notifications(message.chat.id)
    await bot.send_message(message.chat.id,
                           "Напоминания отключены")
    
def get_notification_before_lesson_state(user_id):
    global connection
    global cursor_for_update
    
    cursor_for_update.execute(f"SELECT notification_before_lesson FROM users WHERE user_id = {user_id}")
    arr = [int(row[0]) for row in cursor_for_update.fetchall()] 
    
    return arr[0]

async def switch_notifications(user_id):
    set_lesson_notifications = int(not(get_notification_before_lesson_state(user_id)))
    command = f'''
        UPDATE
        users
        SET
        notification_before_lesson = {set_lesson_notifications}
        WHERE
        user_id = {user_id}
    '''
    execute_query(connection, command)


async def send_messages():
    global connection
    global cursor_for_update
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day = datetime.today().weekday()
    if day > 4:
        return 
    
    cursor_for_update.execute("SELECT user_id FROM users WHERE notification_time=?", (current_time,))
    user_id_arr = [int(row[0]) for row in cursor_for_update.fetchall()] 
    for user_id in user_id_arr:
        await bot.send_message(user_id,
                                await get_schedule_from_day(user_id, day))
    
async def run_notification_schedule():
    schedule = aioschedule.Scheduler()
    schedule.every(1).minutes.do(send_messages)
    start_time = datetime.now().replace(hour=interval_start_hour, minute=interval_start_minute, second=0, microsecond=0)
    end_time = datetime.now().replace(hour=interval_end_hour, minute=interval_end_minute, second=0, microsecond=0)
    if datetime.now() > start_time and datetime.now() < end_time:
        while True:
            await schedule.run_pending()
            await asyncio.sleep(60)
            
            
            
            
async def send_message_of_next_lesson(time:str):
    next_time_of_lesson = make_time_with_delta(time, -time_delta)
    day = datetime.today().weekday()
    if day > 4:
        return
    global connection
    global cursor_for_update
    cursor_for_update.execute("SELECT user_id FROM users WHERE notification_before_lesson = 1")
    user_id_arr = [int(row[0]) for row in cursor_for_update.fetchall()] 
    for user_id in user_id_arr:
        lesson = await get_schedule_from_day(user_id, day)
        if next_time_of_lesson in lesson:
            start = lesson.find(next_time_of_lesson)
            end = start + lesson[start:].find('\n')
            current_lesson = lesson[start:end]
            await bot.send_message(user_id,
                                    current_lesson)
           
            
async def run_notifications_before_lessons():
    schedule = aioschedule.Scheduler()
    for time in times_for_lesson_notifications:
        schedule.every().day.at(time).do(send_message_of_next_lesson, time=time)
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)
    
    
    
# _____________________________ FLASK ___________________________________________

# расширения файлов, которые разрешено загружать
ALLOWED_EXTENSIONS = {'xls', 'xlsx','txt'}
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'update_timetable'
def allowed_file(filename):
    """ Функция проверки расширения файла """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
async def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
async def upload_file():
    if request.method == 'POST':
        # проверим, передается ли в запросе файл 
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # Если файл не выбран, то браузер может
        # отправить пустой файл без имени.
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # безопасно извлекаем оригинальное имя файла
            dir = app.config['UPLOAD_FOLDER']
            if not os.path.exists(dir):
                os.makedirs(dir)
            else:
                shutil.rmtree(dir)
                os.makedirs(dir)
                
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            update_schedule(get_data_students("update_timetable"))
            await saveDataInExcel()
            
            # типо небезопасное сохранение оставил снизу
            #f = request.files['file']
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
            
    return render_template('index.html')

@app.route('/download')
def download_file():
    path = os.path.dirname(__file__)
    path = os.path.join(path, 'student_timetables')
    path = os.listdir(path)[0]
    return send_file(rf"student_timetables\timetables.xlsx", as_attachment=True)





async def on_startup(_):
    try:
        global connection
        connection = create_connection("db.sqlite")
        
        global cursor_for_update
        cursor_for_update = connection.cursor()
        
        create_table_of_schedule_command = '''
            CREATE TABLE IF NOT EXISTS schedules (
                ID INTEGER PRIMARY KEY,
                class_or_last_name TEXT(50),
                Monday TEXT(800),
                Tuesday TEXT(800),
                Wednesday TEXT(800),
                Thursday TEXT(800),
                Friday TEXT(800)
            );
        '''
        create_table_of_users_command = """
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                number INTEGER,
                word TEXT,
                is_teacher INTEGER,
                teacher_last_name TEXT,
                is_admin INTEGER DEFAULT 0,
                notification_time TEXT DEFAULT "",
                notification_before_lesson INT DEFAULT 0
            );
        """
        execute_query(connection, create_table_of_schedule_command)
        execute_query(connection, create_table_of_users_command)
        
        # delete = """
        #     UPDATE
        #     users
        #     SET
        #     is_admin = 0,
        #     notification_before_lesson = 1
        #     WHERE
        #     user_id = 1120501932
        # """
        # execute_query(connection, delete)
        
        
        update_schedule(get_data_students())
        update_schedule(get_data_teachers())
        await saveDataInExcel()
    except Exception as ex:
        logger.exception(f'Ошибка при запуске бота: {ex}')
        sys.exit()
    else:
        logger.info('Бот запущен исправно')
        
    try:
        asyncio.create_task(run_notification_schedule())
    except Exception as ex:
        logger.exception(f'Ошибка при запуске напоминаний: {ex}')
        sys.exit()
    else:
        logger.info('Напоминания запущены исправно')
        
    try:
        asyncio.create_task(run_notifications_before_lessons())
    except Exception as ex:
        logger.exception(f'Ошибка при запуске напоминаний перед уроками: {ex}')
        sys.exit()
    else:
        logger.info('Напоминания 2 запущены исправно')
        
    try:
        asyncio.create_task(asyncio.to_thread(app.run))
    except Exception as ex:
        logger.exception(f'Ошибка при запуске сервера: {ex}')
        sys.exit()
    else:
        logger.info('Сервер на Flask запущен исправно')
   


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
'update_timetable'