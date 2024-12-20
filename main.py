import asyncio
import datetime
import html
import locale
import logging
import requests
import sys

from aiogram import Dispatcher, F, html, Router
#from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.filters import Command, IS_MEMBER, IS_NOT_MEMBER
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from urllib.parse import quote
#from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import bot
from constants import crop_week_day, month_dict, tournament_name
from config import ANNOUNCEMENT_CHANNEL_ID, CHANNEL_ID, TOPIC_ID, allowed_id
from keyboards import build_create_theme_markup, build_reg_markup, get_checking_keyboard, choosing_tournament, room_markup, tournament_type_keyboard
from utils import difficulty_symbol, get_item_color, get_preview_url

locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


dp = Dispatcher(storage=MemoryStorage())
rt = Router()


"""
class SchedulerMiddleware(LifetimeControllerMiddleware):

    def __init__(self, scheduler: AsyncIOScheduler):
        super().__init__()
        self._scheduler = scheduler

    async def pre_process(self, obj: TelegramObject, data: Dict[str, Any], *args: Any):
        data["scheduler"] = self._scheduler
"""
class PostForm(StatesGroup):
    tournamentid = State()
    another_tournament = State()
    another_tour_type = State()
    date_info = State()
    time_info = State()
    editors = State()
    room = State()
    price = State()


###############################################################################
#########################   Начало работы бота   ##############################
###############################################################################
from aiogram.filters import BaseFilter

admin_ids = [123, 456]


class IsAdmin(BaseFilter):
    def __init__(self, admin_ids) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids

@rt.message(Command(commands=["start"]))
async def first_fork(message: Message):
    await message.answer(text="Ошибка доступа!")

@rt.message(~F.from_user.id.in_(allowed_id), Command(commands=["make_me_post"]))
async def first_fork(message: Message):
    await message.answer(text="Ошибка доступа!")

@rt.message(F.from_user.id.in_(allowed_id), Command(commands=["make_me_post"]))
async def first_fork(message: Message):
    builder_fork = InlineKeyboardBuilder()
    fork_buttons = [
        InlineKeyboardButton(text="Добавить информацию о новой игре", callback_data='creation'),
        InlineKeyboardButton(text="Удалить стоимость прошедшего турнира", callback_data='edition'),
        InlineKeyboardButton(text="Завершить работу", callback_data='end')
    ]
    builder_fork.row(*fork_buttons, width=1)
    markup_fork = builder_fork.as_markup()
    await bot.send_message(chat_id=message.chat.id, text='Что Вы хотите сделать? ', reply_markup=markup_fork)


@rt.callback_query(F.data == 'end')
async def process_start_command(call: CallbackQuery):
    await call.message.answer('Хорошего дня!')
    await call.answer()


@rt.callback_query(F.data == 'edition')
async def existing_post_edition(call: CallbackQuery):
    await call.message.answer("Перешлите пост, который необходимо отредактировать")
    await call.answer()


@rt.message(F.forward_from_chat[F.type == "channel"].as_("channel"))
async def edition(message: Message):
    txt = message.html_text
    keyboard = message.reply_markup
    border = txt.find('💲')
    new_txt = txt[:border].rstrip()
    post_id = message.forward_from_message_id
    await bot.edit_message_text(text=new_txt, chat_id=CHANNEL_ID, message_id=post_id, reply_markup=keyboard)
    await message.answer("Пост успешно отредактирован")
    await first_fork(message=message)

@rt.callback_query(F.data == 'creation')
async def process_start_command(call: CallbackQuery, state: FSMContext):
    tour_fork = choosing_tournament()
    await call.message.answer(text='Какой турнир Вы хотите создать?', reply_markup=tour_fork)
    await state.set_state(PostForm.tournamentid)
    await call.answer()

# нерейтинговый
@rt.callback_query(F.data == 'another_tournament')
async def process_start_command(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите название турнира, указав тур.<blockquote><b><u>Источники</u></b>:\nМКМ - https://student.chgk.info/ \n\
ШРеК - https://shrek.chgk.su/</blockquote>')
    await state.set_state(PostForm.another_tournament)
    await call.answer()

@rt.message(PostForm.another_tournament)
async def another_tournament_name(message: Message, state: FSMContext):
    await state.update_data(another_tournament=message.text)
    markup_fork = tournament_type_keyboard()
    await bot.send_message(chat_id=message.chat.id, text='Укажите тип турнира', reply_markup=markup_fork)
    await state.set_state(PostForm.another_tour_type)

@rt.callback_query(PostForm.another_tour_type)
async def another_tournament_name(call: CallbackQuery, state: FSMContext):
    global difficulty
    if call.data == 'easy':
        difficulty = 2
    elif call.data == 'medium':
        difficulty = 3.5
    elif call.data == 'hard':
        difficulty = 5
    else:
        difficulty = 0
    await state.update_data(another_tour_type=difficulty)
    await call.message.answer("Введите редакторов в формате <i>{имя фамилия}, ..., {имя фамилия}</i> \nЕсли редакторов шесть и более — укажите только их фамилии\
<blockquote><b><u>Пример 1:</u></b> \n<i>Максим Мерзляков, Сергей Терентьев, Андрей Скиренко, Матвей Гомон</i>\n\n\
<b><u>Пример 2:</u> </b>\n<i>Лешкович, Наугольнов, Полевой, Раскумандрин, Рождествин, Рыбачук, Сушков</i></blockquote>")
    await state.set_state(PostForm.editors)

@rt.message(PostForm.editors)
async def another_tournament_name(message: Message, state: FSMContext):
    await state.update_data(editors=message.text)
    await message.answer("Напишите дату в формате <i>ДД.ММ.ГГ</i> или <i>ДД/ММ/ГГ</i>")
    await state.set_state(PostForm.date_info)

# Не рейтинговый турнир
@rt.callback_query(F.data == 'rate_tournament')
async def process_start_command(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите ID турнира:')
    await state.set_state(PostForm.tournamentid)
    await call.answer()

# Записывается название турнира, переход курсора на поле для даты
@rt.message(PostForm.tournamentid)
async def get_tournament_info(message: Message, state: FSMContext):
    await state.update_data(tournamentid=message.text)
    await message.answer("Напишите дату в формате <i>ДД.ММ.ГГ</i> или <i>ДД/ММ/ГГ</i>")
    await state.set_state(PostForm.date_info)

# Записывается дата, переход курсора на поле для времени
@rt.message(PostForm.date_info)
async def get_date_info(message: Message, state: FSMContext):
    if len(message.text) == 8:
        msg = message.text[:-2] + '20' + message.text[-2:]
    else:
        msg = message.text
    try:
        if '.' in msg:
            our_data = datetime.datetime.strptime(msg, "%d.%m.%Y")
        else:
            our_data = datetime.datetime.strptime(msg, "%d/%m/%Y")
        if our_data.weekday() != 5 and our_data.weekday() != 6:
            await bot.send_message(message.chat.id, "Кажется, это не выходной день...")
            raise
        await state.update_data(date_info=our_data)
        await bot.send_message(message.chat.id, "Напишите время проведения игры в формате <i>ЧЧ:ММ</i> или <i>ЧЧ/ММ</i>")
        await state.set_state(PostForm.time_info)
    except:
        await bot.send_message(message.chat.id, "Введите допустимую дату для турнира")
        get_date_info(message, state)

# TODO: fix
# В этом хэндлере принимается время турнира и собираются данные для поста
@rt.message(PostForm.time_info)
async def get_time_info(message: Message, state: FSMContext):
    global full_name, full_time, difficulty, final_date, \
        place, txt_editors, editors_lst, post, weekday, txt_date
    await state.update_data(time_info=message.text)
    data = await state.get_data()
    global full_date
    full_date = data['date_info']
    full_time = data['time_info']
    if '/' in full_time:
        full_time = full_time.replace('/', ':')
    txt_date = f'{str(full_date.day)} {month_dict[full_date.month]}'
    global week_day
    week_day = full_date.weekday()
    if week_day == 6:
        week_day = "ВОСКРЕСЕНЬЕ"
    elif week_day == 5:
        week_day = 'СУББОТА'
    final_date = week_day + ' (' + txt_date + ')'
    if 'another_tournament' not in data:
        id_url = quote(str(data['tournamentid']))
        url_parse = 'https://api.rating.chgk.net/tournaments/' + id_url
        global tournament_info
        if requests.get(url_parse).json() == []:
            await bot.send_message(message.chat.id, "Турнир не найден! Введите другой ID")
            await state.set_state(PostForm.tournament)
            get_tournament_info(message)
        tournament_info = requests.get(url_parse).json()
        await state.set_state(PostForm.price)
        full_name = tournament_info['name']
        difficulty = difficulty_symbol(tournament_info['difficultyForecast'])
        # Информация о редакторах
        editors = []
        if len(tournament_info['editors']) >= 6:
            for item in tournament_info['editors']:
                editors.append(item['surname'])
        else:
            for item in tournament_info['editors']:
                editors.append(f"{item['name']} {item['surname']}")
        txt_editors = "Редактор" if len(editors) == 1 else "Редакторы"
        editors_lst = ', '.join(editors)
        # Сбор данных об оплате
        global main_payment, currency_symbol, discounted_payment, annotation, currency_symbol_disc
        main_payment = tournament_info['mainPayment']
        if tournament_info['currency'] == 'r':
            currency_symbol = '₽'
        elif tournament_info['currency'] == 'u':
            currency_symbol = '$'
        else:
            currency_symbol = '€'
        try:
            discounted_payment = tournament_info['discountedPayment']
            annotation = tournament_info['discountedPaymentReason']
            currency_symbol_disc = currency_symbol
        except KeyError:
            discounted_payment = "Информация о льготном тарифе отсутствует"
            annotation = "—"
            currency_symbol_disc = ''
    else:
        full_name = data['another_tournament']
        editors_lst = data['editors']
        if ',' in editors_lst:
            txt_editors = 'Редакторы'
        else:
            txt_editors = 'Редактор'
        difficulty = difficulty_symbol(data['another_tour_type'])
        await state.set_state(PostForm.price)
    place_fork = room_markup()
    await bot.send_message(message.chat.id, 'Выберите аудиторию для проведения игры', reply_markup=place_fork)
    await state.set_state(PostForm.room)

@rt.callback_query(F.data == '401')
async def room401(call: CallbackQuery, state: State):
    await state.update_data(room='401')
    data = await state.get_data()
    if 'tournamentid' in data:
        await call.message.answer(
            text=f'Исходные расценки турнира:\n<blockquote><b>Основной тариф</b>: {main_payment}{currency_symbol} \
        \n<b>Льготный тариф</b>: {discounted_payment}{currency_symbol_disc} \n<b>Пояснение к льготе</b>: {annotation}</blockquote>',
            parse_mode='HTML')
    await call.message.answer(text=f'Введите требуемую тарификацию.\n<pre>Основной / студенческий / школьный зачет - 1000 / 700 / 300\nТройки / парный зачет - 700 / 500 </pre>')
    await state.set_state(PostForm.price)

@rt.callback_query(F.data == 'another_room')
async def another_room(call: CallbackQuery):
    await call.message.answer('Введите требуемую аудиторию')

@rt.message(PostForm.room)
async def define_another_room(message: Message, state: State):
    await state.update_data(room=message.text)
    data = await state.get_data()
    if 'tournamentid' in data:
        await message.answer(
            text=f'Исходные расценки турнира:\n<blockquote><b>Основной тариф</b>: {main_payment}{currency_symbol} \
        \n<b>Льготный тариф</b>: {discounted_payment}{currency_symbol_disc} \n<b>Пояснение к льготе</b>: {annotation}</blockquote>',
            parse_mode='HTML')
    await message.answer(text=f'Введите требуемую тарификацию.\n<pre>Основной / студенческий / школьный зачет - 1000 / 700 / 300\nТройки / парный зачет - 700 / 500 </pre>')
    await state.set_state(PostForm.price)


# Хендлер для поста
@rt.message(PostForm.price)
async def make_post(message: Message, state: State):
    global cost, post, place
    cost = message.text
    try:
        if not cost.startswith('Основной'):
            await bot.send_message(message.chat.id, "Стоимость должна начинаться с <i>Основной...</i>. \nВведите корректную тарификацию ")
            raise
        data = await state.get_data()
        place = data['room']
        post = f'{difficulty} {html.bold(final_date)} {difficulty}\nЧто❓ {full_name}\nГде❓ XI корпус СГУ, {place} аудитория\nКогда❓ {full_time}\n\n✍🏻 {txt_editors} - {html.italic(editors_lst)}.\n💲 {cost}.'
        await message.answer(post)
        checking_keyboard = get_checking_keyboard()
        await message.answer("Проверьте текст поста. Всё ли верно?", reply_markup=checking_keyboard)
        await state.clear()
    except:
        make_post(message, state)


# @rt.callback_query(F.data == 'yes')
# async def posting(call: CallbackQuery):
#     builder_create_theme = InlineKeyboardBuilder()
#     btn = InlineKeyboardButton(text="Создать тему и опрос для регистрации", callback_data='theme_poll')
#     builder_create_theme.row(btn, width=1)
#     markup_creation = builder_create_theme.as_markup()
#     await call.message.answer(text="Отлично, перейдём к следующему шагу", reply_markup=markup_creation)
#     await call.answer()


@rt.callback_query(F.data == 'no')
async def correcting(call: CallbackQuery):
    await call.message.answer("Скопируйте предлагаемый пост, исправьте его и пришлите в этот чат")
    await call.answer()


@rt.message(F.text.find('Где❓ XI корпус СГУ') != -1)
async def new_post_init(message: Message):
    # TODO: fix
    global difficulty, final_date, week_day, txt_date, full_name, \
           place, full_time, txt_editors, editors_lst, cost, post
    post = message.text
    difficulty = post[0]
    final_date = post[2:post.find(difficulty, 1) - 1]
    week_day = final_date[:final_date.find('(') - 1]
    txt_date = final_date[final_date.find('(') + 1:final_date.find(')')]
    full_name = post[post.find('❓') + 2:post.find('Где') - 1]
    place = post[post.find('СГУ,') + 5:post.find('СГУ,') + 8]
    full_time = post[post.rfind('❓') + 2:post.rfind('❓') + 7]
    txt_editors = post[post.find('✍🏻') + 3:post.rfind('-') - 1]
    editors_lst = post[post.rfind('-') + 2:post.find('💲') - 1]
    cost = post[post.find('💲') + 2:post.rfind('.')]

    markup_creation = build_create_theme_markup()
    await message.answer(text="Отлично, перейдём к следующему шагу", reply_markup=markup_creation)


@rt.callback_query(F.data == 'theme_poll')
async def make_theme_and_poll(call: CallbackQuery, state: FSMContext):
    await call.answer()
    week_day_short = crop_week_day[week_day.lower()]
    theme_heading = f"{full_name} ({txt_date}, {week_day_short}, {full_time})"
    icon_color = get_item_color(difficulty=difficulty)
    text = f'{full_name}\n{txt_date} ({week_day}) {full_time}, {place} ауд. \n{txt_editors} - {editors_lst}'
    topic = await bot.create_forum_topic(chat_id=TOPIC_ID, name=theme_heading, icon_color=icon_color)
    chat = await bot.get_chat(chat_id=TOPIC_ID)
    await bot.send_message(chat_id=TOPIC_ID, text="Регистрация:", reply_to_message_id=topic.message_thread_id)
    await bot.send_poll(chat_id=TOPIC_ID, question=text, options=["Играю", "Думаю", "Пас"], is_anonymous=False)
    
    keyboard_reging = build_reg_markup(chat_username=chat.username, topic_id=topic.message_thread_id)
    await state.update_data(markup=keyboard_reging)

    await call.message.answer(text="Тема и опрос успешно созданы.\nПришлите фото для поста.")


@rt.message(F.photo)
async def make_post_with_photo(message: Message, state: FSMContext):
    keyboard_reging = await state.get_data()
    preview_url = await get_preview_url(message=message)

    await bot.send_message(
        # TODO: fix
        # chat_id= -1001614796938,
        # chat_id=ANNOUNCEMENT_CHANNEL_ID,
        chat_id=ANNOUNCEMENT_CHANNEL_ID,
        text=f"{html.link(value='&#8288', link=preview_url)}{post}",
        protect_content=False,
        reply_markup=keyboard_reging["markup"],
    )
    await message.answer("Пост добавлен в канал")
    await first_fork(message=message)


async def main():
    dp.include_router(rt)
    await dp.start_polling(bot)


async def logged_main():
    dp.include_router(rt)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    scheduler = asyncio.AsyncIOScheduler()
    try:
       scheduler.start()
       await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(logged_main())
