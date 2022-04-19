from aiogram import Bot, types, Dispatcher, executor
from get_tgd import get_data
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text, Command
from auth_data import token
from db import create_connection, execute_query, execute_read_query

import datetime

bot = Bot(token=token, parse_mode=types.ParseMode.HTML)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data = {}

menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("Получить расписание")

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


class Student(StatesGroup):
    student_number = State()
    student_word = State()


async def start_input_class(message):
    await Student.student_number.set()
    await message.reply("Процесс регистрации... (впишите 'отмена') для отмены действия")
    await message.reply("Впишите номер класса:")


@dp.message_handler(commands="start")
async def callback_start(message: types.Message):
    await bot.send_message(message.chat.id,
                           "\U0001F64B Привет! Я sd_bot_1201. Я помогу тебе найти расписание.")
    await start_input_class(message)


@dp.message_handler(commands="relog")
async def callback_relog(message: types.Message):
    await start_input_class(message)


@dp.message_handler(commands="menu")
async def callback_menu(message: types.Message):
    await bot.send_message(message.chat.id,
                           "Меню открыто", reply_markup=menu)


@dp.message_handler(commands="help")
async def callback_help(message: types.Message):
    await bot.send_message(message.chat.id,
                           "Список команд\nЗарегистрироваться заново - /relog\nОткрыть меню - /menu\nОткрыть расписание - вписать 'Получить расписание'")


def get_user(user_id):
    select_users = "SELECT * from users"
    users = execute_read_query(connection, select_users)

    for user in users:
        if int(user[1]) == user_id:
            return user
    return None


def create_user(user_id, data):
    if not get_user(user_id):
        print(f"create new user '{user_id}', '{data}'")
        create_users = f"""
            INSERT INTO
              users (user_id, number, word)
            VALUES
              ({user_id}, {data["number"]}, '{data["word"]}');
            """
        execute_query(connection, create_users)
    else:
        update_description = f"""
        UPDATE
            users
        SET
          number = {data["number"]},
          word = "{data["word"]}"   
        WHERE
          user_id = {user_id}
        """
        execute_query(connection, update_description)


def get_student_timetable(user_id, day):
    try:
        user_data = get_user(user_id)
        result_timetable = data[f"{user_data[2]}{user_data[3]}".lower()][day]
        result = f"\U0001F514 {user_data[2]}{user_data[3].upper()} {days[day]}:\n\n"
        for index, lesson in enumerate(result_timetable):
            lesson = lesson[0].upper() + lesson[1:]
            result += f"{time_of_lesson[index]['start']} - {time_of_lesson[index]['end']}:    {lesson}\n"
        return result
    except:
        return "Ошибка... Проверьте введенный класс (Пропишите /start и введите нужный класс)"


@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel(message: types.Message, state: FSMContext):
    curent_state = await state.get_state()
    if curent_state is None:
        return
    await state.finish()


@dp.message_handler(state=Student.student_number)
async def load_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as new_student:
            new_student['number'] = int(message.text)
        await Student.next()
        await message.reply('Введите литеру (букву) класса')
    except Exception:
        await message.reply('Введите только целое число')


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


@dp.message_handler(state=Student.student_word)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_student:
        new_student['word'] = message.text.lower()
        await Student.next()
        await state.finish()
        new_student = {
            "number": new_student['number'],
            "word": new_student['word']
        }
        create_user(message.from_user.id, new_student)
        await bot.send_message(message.chat.id, '\U00002705 Теперь вы можете смотреть свое расписание', reply_markup=menu)


@dp.message_handler(Text(equals="Получить расписание"))
async def give_timetable(message: types.Message):
    await message.reply('Выберете расписание, которое вам требуется', reply_markup=menu_time)


@dp.callback_query_handler(text_contains='time_')
async def callback(call: types.CallbackQuery, state: FSMContext):
    if call.data and call.data.startswith("time_"):
        cl = call.data.split('_')[1]
        is_today = ['week', 'today', 'tomorrow'].index(cl)
        if is_today == 1:
            day = datetime.datetime.today().weekday()
            await bot.send_message(call.from_user.id, get_student_timetable(call.from_user.id, day))
        elif is_today == 2:
            day = datetime.datetime.today().weekday() + 1
            if day > 4:
                day = 0
            await bot.send_message(call.from_user.id, get_student_timetable(call.from_user.id, day))
        else:
            for day in range(5):
                await bot.send_message(call.from_user.id, get_student_timetable(call.from_user.id, day))


if __name__ == "__main__":
    connection = create_connection("db.sqlite")
    data = get_data()
    executor.start_polling(dp)
