from aiogram import Bot, types, Dispatcher, executor
from get_tgd import get_data
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text, Command
from auth_data import token

import datetime

bot = Bot(token=token, parse_mode=types.ParseMode.HTML)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data = {}

menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("Получить расписание")


@dp.message_handler(commands="start")
async def callback_start(message: types.Message):
    await bot.send_message(message.chat.id,
                           "Привет! Я sd_bot_1201. Я помогу тебе найти расписание.",
                           reply_markup=menu)


class Class(StatesGroup):
    class_number = State()
    class_word = State()
    when = State()


def get_class_timetable(new_class):
    result_timetable = data[new_class['number']][new_class['word']]
    return "Типо расписание"

@dp.message_handler(Text(equals="Получить расписание"))
async def callback(message: types.Message):
    await Class.class_number.set()
    await message.reply("Впишите номер класса:")


@dp.message_handler(state=Class.class_number)
async def load_name(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as new_class:
            new_class['number'] = int(message.text)
        await Class.next()
        await message.reply('Введите литеру (букву) класса')
    except Exception:
        await message.reply('Введите только целое число')


menu_time = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_time.row("На неделю", "На сегодня")

@dp.message_handler(state=Class.class_word)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_class:
        new_class['word'] = message.text.lower()
        await Class.next()
        await message.reply('Какое расписание вы хотите получить?', reply_markup=menu_time)

@dp.message_handler(state=Class.class_word)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as new_class:
        if message.text in ['На неделю', 'На сегодня']:
            new_class['when'] = ['На неделю', 'На сегодня'].index(message.text)
            await Class.next()
            new_class = {
                "number": new_class['number'],
                "word": new_class['word'],
                "when": new_class['when'] is 1
            }
            await message.reply(get_class_timetable(new_class))
            await state.finish()
        else:
            await message.reply('Какое расписание вы хотите получить?', reply_markup=menu_time)










if __name__ == "__main__":
    data = get_data()
    executor.start_polling(dp)
