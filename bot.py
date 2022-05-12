'''
    Запуск бота
'''
import datetime
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

from dotenv import load_dotenv
from pathlib import Path
import os
from logging import getLogger, StreamHandler, Formatter, INFO
import pandas as pd


logger = getLogger(__name__)
logger.setLevel(INFO)

handler = StreamHandler(stream=sys.stdout)
handler.setFormatter(Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
logger.addHandler(handler)

load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv("TOKEN")
ADMIN_KEY = os.getenv("ADMIN_KEY")

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data = {}

data_teachers = {}
connection = None

user_params = [
    'id',
    'user_id',
    'number',
    'word',
    'is_teacher',
    'teacher_last_name',
    'is_admin'
]
days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
time_of_lesson = [
    {
        "start": "8:30",
        "end": "9:15",
    },
    {
        "start": "9:30",
        "end": "10:15",
    },
    {
        "start": "10:30",
        "end": "11:15",
    },
    {
        "start": "11:30",
        "end": "12:15",
    },
    {
        "start": "12:35",
        "end": "13:20",
    },
    {
        "start": "13:40",
        "end": "14:25",
    },
    {
        "start": "14:45",
        "end": "15:30",
    },
    {
        "start": "15:40",
        "end": "16:25",
    },
    {
        "start": "16:35",
        "end": "17:20",
    },
]

menu_for_get_timetable = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_for_get_timetable.row("Помощь", "Получить расписание")

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

async def saveData():
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
    df.to_excel('./student_timetables/timetables.xlsx', sheet_name='1', index=False)
    logger.info('Обновлено расписание')

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
                           "Открыть расписание - вписать 'Получить расписание'")


def get_user(user_id):
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




async def get_timetable(user_id, day):
    """
        Получить расписание
    """
    try:
        user_data = get_user(user_id)
        if user_data['is_teacher'] == 1:
            result_timetable = data_teachers[f"{user_data['teacher_last_name']}".lower()][day]
            result = f"\U0001F514 {days[day]}:\n\n"
            for index, lesson in enumerate(result_timetable):
                letter = "{} - {}:    {}\n"
                result += letter.format(
                    time_of_lesson[index]['start'],
                    time_of_lesson[index]['end'],
                    lesson
                )
            return result
        else:
            result_timetable = data[f"{user_data['number']}{user_data['word']}".lower()][day]
            result = f"\U0001F514 {user_data['number']}{user_data['word'].upper()} {days[day]}: \n\n"
            for index, lesson in enumerate(result_timetable):
                letter = "{} - {}:    {}\n"
                result += letter.format(
                    time_of_lesson[index]['start'],
                    time_of_lesson[index]['end'],
                    lesson
                )
            return result

    except Exception as ex:
        logger.exception(f'Ошибка при попытке получить расписания. Пользователь: {get_user(user_id)}, Оишбка: {ex}')
        return "Ошибка... Проверьте введенный класс" \
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
            day = datetime.datetime.today().weekday()
            await bot.send_message(call.from_user.id,
                                   await get_timetable(call.from_user.id, day))
        elif is_today == 2:
            day = datetime.datetime.today().weekday() + 1
            if day > 4:
                day = 0
            await bot.send_message(call.from_user.id,
                                   await get_timetable(call.from_user.id, day))
        else:
            for day in range(5):
                await bot.send_message(call.from_user.id,
                                       await get_timetable(call.from_user.id, day))


@dp.callback_query_handler(text_contains='person_')
async def callback_person(call: types.CallbackQuery):
    """
        Ученик / Учитель
        (is_teacher: False / True)
    """
    if call.data and call.data.startswith("person_"):
        callback_get_person = call.data.split('_')[1]
        is_today = ['student', 'teacher'].index(callback_get_person)
        if is_today == 0:
            await start_input_class(call)
        if is_today == 1:
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
            shutil.rmtree(dir)
            if document := message.document:
                await document.download(
                    destination_dir=dir,
                )
            data.update(get_data_students("update_timetable/documents"))
            await saveData()

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


async def on_startup(_):
    try:
        global connection
        connection = create_connection("db.sqlite")

        global data
        data.update(get_data_students())
        await saveData()
        global data_teachers
        data_teachers = get_data_teachers()
    except Exception as ex:
        logger.exception(f'Ошибка при запуске бота: {ex}')
        sys.exit()
    else:
        logger.info('Бот запущен исправно')



if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
