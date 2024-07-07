import os
import json
import redis
import vk_api
import random
import sqlite3
import datetime
from dotenv import load_dotenv
# from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

load_dotenv()

host, port, password, token, group_id = os.environ.get('HOST'), os.environ.get('PORT'),\
    os.environ.get('PASSWORD'), os.environ.get('TOKEN'), os.environ.get('GROUP_ID')

# Подключение к Redis
redis_client = redis.Redis(
  host=host,
  port=port,
  password=password
#   ssl=True
)

conn = sqlite3.connect('/data/rent.db')
cursor = conn.cursor()

support_specialists_ids = [541207257]

answer = {
    'Сколько стоит игра?': '800 рублей',
    'Какая продолжительность игры?': 'Игра начинается в 12:00 и длится до 17:00',
    'Можно ли оставить где-то машину?': 'Да, если Вы не опаздываете и приезжаете в указанное время, то можете заехать на территорию полигона',
    'Что делать если опоздал на игру?': 'Можете оставить машину возле ворот, на парковке, и пройти к полигону пешком',
    'Во сколько заезд на игру?': 'Заезд начинается с 10:00 - 12:00',
    'Есть ли туалет на игре?': 'Да, на игре имеются биотуалеты',
    'Есть ли мастерская на игре?': 'Да, находится в большом здание на 2-ом этаже'
}

initial_inventory_values = [
    ("Комплект", 12, 12),
    ("Привод", 23, 23),
    ("Пистолет", 3, 3),
    ("Дробовик", 1, 1),
    ("Маска", 23, 23),
    ("Очки", 10, 10),
    ("Каска", 5, 5),
    ("Броник", 8, 8),
    ("Форма", 20, 20),
    ("Киллкамера", 2, 2)
]

cursor.execute('''
CREATE TABLE IF NOT EXISTS inventory_price (
    item TEXT NOT NULL PRIMARY KEY UNIQUE,
    price TEXT NOT NULL
)''')

conn.commit()

cursor.executemany('''
INSERT OR IGNORE INTO inventory_price (item, price)
VALUES (?, ?)''', [
    ('Комплект', '2200 руб.'),
    ('Привод', '1600 руб.'),
    ('Пистолет', '1200 руб.'),
    ('Дробовик', '1500 руб.'),
    ('Маска', '200 руб.'),
    ('Очки', '200 руб.'),
    ('Каска', '400 Руб.'),
    ('Броник', '400 руб.'),
    ('Форма', '200 Руб.'),
    ('Киллкамера', '1500 руб.')
])

conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS inventory (
    item TEXT NOT NULL PRIMARY KEY,
    quantity_subbota INTEGER NOT NULL,
    quantity_voskresenie INTEGER NOT NULL
)''')

conn.commit()

cursor.executemany('''
INSERT OR IGNORE INTO inventory (item, quantity_subbota, quantity_voskresenie)
VALUES (?, ?, ?)''', initial_inventory_values)

conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS all_save_items (
    full_name TEXT NOT NULL,
    item TEXT NOT NULL,
    day TEXT NOT NULL,
    FOREIGN KEY(item) REFERENCES inventory(item)
)''')

conn.commit()

vk_session = vk_api.VkApi(token=token, api_version='5.199')
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, group_id=group_id)

# Получение состояние для человека
def get_user_state(user_id):
    try:
        return redis_client.get(f'user_state:{user_id}').decode()
    except:
        set_user_state(user_id, '')
        return ''

# Функция для установки состояния человеку
def set_user_state(user_id, state):
    redis_client.set(f'user_state:{user_id}', state)

# Функция для очистки таблицы в среду
def clear_and_restore():
    cursor.execute('DELETE FROM all_save_items')
    conn.commit()
    for item, quantity_subbota, quantity_voskresenie in initial_inventory_values:
        cursor.execute('''UPDATE inventory SET quantity_subbota = ?, quantity_voskresenie = ?
        WHERE item = ?''', (quantity_subbota, quantity_voskresenie, item))

    conn.commit()

# Функция для начала диалога
def start_message(user_id):
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Начать', color=VkKeyboardColor.POSITIVE)
    send_message(user_id, 'Не понимаю, что Вы хотите сделать. Для начала диалога напишите: "Начать"', keyboard=keyboard)

# Функция для отправки сообщений
def send_message(user_id, message, keyboard=None):
    post_params = {'user_id': user_id, 'message': message, 'random_id': random.randint(1, 1000)}
    if keyboard is not None:
        post_params['keyboard'] = keyboard.get_keyboard()
    else:
        post_params['keyboard'] = VkKeyboard.get_empty_keyboard()
    vk.messages.send(**post_params)

# Функция для сохранения данных
def handler_item(user_id, text, state):
    keyboard = VkKeyboard(one_time=False)

    if state == 'воскресенье':
        set_user_state(user_id, '')
        user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name') 
        full_name = user_info[0]['first_name'] + " " + user_info[0]['last_name']

        cursor.execute('SELECT item, quantity_voskresenie FROM inventory WHERE item = ?', (text.title(),))
        item = cursor.fetchone()
        
        # Проверка наличия аренды и обновление данных
        if item and item[1] > 0:
            cursor.execute('UPDATE inventory SET quantity_voskresenie = quantity_voskresenie - 1 WHERE item = ?', (text.title(),))
            conn.commit()
            cursor.execute('INSERT INTO all_save_items (full_name, item, day) VALUES (?, ?, ?)', (full_name, text.title(), 'Воскресенье'))
            conn.commit()
            keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
            send_message(user_id, f'Вы успешно забронировали "{text.title()}" на воскресенье!', keyboard=keyboard)
        else:
            keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
            send_message(user_id, 'Данный тип аренды закончился', keyboard=keyboard)

    elif state == 'воскресенье отмена':
        user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name')
        full_name = user_info[0]['first_name'] + " " + user_info[0]['last_name']
        
        cursor.execute('SELECT * FROM all_save_items WHERE full_name = ?', (full_name,))
        user_items = cursor.fetchall()
        
        if user_items:
            cursor.execute('SELECT * FROM all_save_items WHERE full_name = ? AND item = ? AND day = "Воскресенье"', (full_name, text.title()))
            item_to_cancel = cursor.fetchone()
            
            if item_to_cancel:
                cursor.execute('''DELETE FROM all_save_items WHERE rowid IN (SELECT rowid FROM all_save_items 
                    WHERE full_name = ? AND item = ? AND day = "Воскресенье" LIMIT 1)''', (full_name, text.title()))
                conn.commit()
                
                cursor.execute('UPDATE inventory SET quantity_voskresenie = quantity_voskresenie + 1 WHERE item = ?', (text.title(),))
                conn.commit()
                
                keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
                send_message(user_id, f'Вы успешно отменили бронь "{text.title()}" на воскресенье!', keyboard=keyboard)
            else:
                keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
                send_message(user_id, 'Данный тип аренды Вы не бронировали!', keyboard=keyboard)
        else:
            keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
            send_message(user_id, 'Вы не бронировали вещи!', keyboard=keyboard)

    else:
        start_message(user_id)

# Функция для вывода арендованных вещей
def send_rental_info(user_id):
    keyboard = VkKeyboard(one_time=False)
    user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name') 
    full_name = user_info[0]['first_name'] + " " + user_info[0]['last_name'] 
    cursor.execute('SELECT item, day FROM all_save_items')
    rentals = cursor.fetchall() 
    if len(rentals) != 0:
        message_lines = [f'Пользователь {full_name}, вы арендовали:']
        for rental in rentals:
            message_lines.append(f"  - {rental[0]} на {rental[1]}")
        message_text = '\n'.join(message_lines)
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, message_text, keyboard=keyboard)
    else:
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'У вас нет арендованных вещей', keyboard=keyboard)

# Функция для выбора дня (для взятия аренды)
def choice_date_from_arenda(user_id, text, state):
    keyboard = VkKeyboard(one_time=False)
    
    if (text == 'воскресенье') and (state == 'menu_arenda'):
        s = 0
        set_user_state(user_id, 'воскресенье')
        cursor.execute('SELECT item FROM inventory WHERE quantity_voskresenie != 0')
        inventoru_from_voskresenie = cursor.fetchall()
        for el in inventoru_from_voskresenie:
            s += 1
            if s % 2 == 0:
                keyboard.add_line()
            keyboard.add_button(el[0], color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'Выберите аренду', keyboard=keyboard)

    elif (text == 'воскресенье') and (state == 'is_cancel'):
        set_user_state(user_id, 'воскресенье отмена')

        user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name') 
        full_name = user_info[0]['first_name'] + " " + user_info[0]['last_name'] 
        cursor.execute('SELECT item FROM all_save_items WHERE full_name == ? AND day == ?', (full_name, 'Воскресенье'))
        items = cursor.fetchall()
        if len(items) > 0:
            for rental in items:

                keyboard.add_button(rental[0], color=VkKeyboardColor.SECONDARY)
            keyboard.add_line()
            keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
            send_message(user_id, "Выберите, какую аренду Вы хотите отменить", keyboard=keyboard)
        else:
            keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
            send_message(user_id, 'У вас нет арендованных вещей на данный день', keyboard=keyboard)

    else:
        handler_item(user_id, text, state)

def main_menu(user_id):
    keyboard = VkKeyboard(one_time=False)

    set_user_state(user_id, '')

    keyboard.add_button('Информация', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Аренда', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Помощь', color=VkKeyboardColor.PRIMARY)
    send_message(user_id, 'Главное меню', keyboard=keyboard)

# Функция для обработки нажатий на кнопки
def handle_buttons(user_id, text, state):
    keyboard = VkKeyboard(one_time=False)

    if (state == 'is_help') and (text != 'вопрос закрыт'):
        pass

    elif text == 'начать':
        main_menu(user_id)

    elif text == 'информация':
        set_user_state(user_id, 'info')

        keyboard.add_callback_button(label='Услуги', color=VkKeyboardColor.PRIMARY, payload={"type": "open_link", "link": "https://vk.com/uslugi-218785093?screen=group"})
        keyboard.add_line()
        keyboard.add_button('Как добраться?', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_callback_button(label='Правила', color=VkKeyboardColor.PRIMARY, payload={"type": "open_link", "link": "https://vk.com/topic-218785093_49290691"})
        keyboard.add_line()
        keyboard.add_callback_button(label='Фото полигона', color=VkKeyboardColor.PRIMARY, payload={"type": "open_link", "link": "https://vk.com/airsoft_pd?z=album-218785093_301260832"})
        keyboard.add_line()
        keyboard.add_callback_button(label='Отзывы/Предложения', color=VkKeyboardColor.PRIMARY, payload={"type": "open_link", "link": "https://vk.com/topic-218785093_49318795"})
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'Меню информации', keyboard=keyboard)

    elif (text == 'как добраться?') and (state == 'info'):
        keyboard.add_callback_button(label='Полигон Южный', color=VkKeyboardColor.POSITIVE, payload={"type": "open_link", "link": "https://vk.com/topic-218785093_50861865"})
        keyboard.add_callback_button(label='Полигон Домодедово', color=VkKeyboardColor.POSITIVE, payload={"type": "open_link", "link": "https://vk.com/topic-218785093_49262342"})
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'Выберите на какой полигон Вы хотите добарться', keyboard=keyboard)

    elif (text == 'аренда'):
        set_user_state(user_id, 'menu_arenda')

        keyboard.add_button('Аренда вещей', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Цены на аренду', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Количество оставшейся аренды (вс)', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Мои арендованные вещи', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Отменить аренду', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'Меню аренды', keyboard=keyboard)

    elif (text == 'аренда вещей') and (state == 'menu_arenda'):
        keyboard.add_button('Воскресенье', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'Выберите день на который Вам нужна аренда', keyboard=keyboard)

    elif (text == 'мои арендованные вещи') and (state == 'menu_arenda'):
        send_rental_info(user_id)

    elif (text == 'отменить аренду') and (state == 'menu_arenda'):
        set_user_state(user_id, 'is_cancel')

        keyboard.add_button('Воскресенье', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'Выберите день на который Вы хотите отменить аренду', keyboard=keyboard)

    elif (text == 'количество оставшейся аренды (вс)') and (state == 'menu_arenda'):
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        cursor.execute('SELECT item, quantity_voskresenie FROM inventory')
        items_quantity = cursor.fetchall()
        send_message(user_id, '\n'.join([f"{item}: {quantity} шт.\n" for item, quantity in items_quantity]), keyboard=keyboard)

    elif (text == 'цены на аренду') and (state == 'menu_arenda'):
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        cursor.execute('SELECT item, price FROM inventory_price')
        inventoru_price = cursor.fetchall()
        send_message(user_id, '\n'.join([f"{item}: {quantity}\n" for item, quantity in inventoru_price]), keyboard=keyboard)

    elif (text == 'назад') and (state == 'answer_question'):
        question_send(user_id)

    elif text == 'назад':
        main_menu(user_id)

    elif text == 'помощь':
        set_user_state(user_id, 'menu_help')

        keyboard.add_button('Связаться с оператором', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Частые вопросы', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, 'Меню помощи', keyboard=keyboard)

    elif (text == 'частые вопросы') and (state == 'menu_help'):
        question_send(user_id)

    elif state == 'question_send':
        answer_question(user_id, text)

    elif (text == 'связаться с оператором') and (state == 'menu_help'): 
        set_user_state(user_id, 'is_help')
        ticket(user_id)

    elif text == 'вопрос закрыт':
        main_menu(user_id)

    else:
        choice_date_from_arenda(user_id, text, state)

def question_send(user_id):
    keyboard = VkKeyboard(one_time=False)
    set_user_state(user_id, 'question_send')

    counter = 0
    for el in answer:
        counter += 1
        keyboard.add_button(el, color=VkKeyboardColor.PRIMARY)
        if counter in [2, 3, 5, 6, 8, 9]:
            keyboard.add_line()
    keyboard.add_line()
    keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
    send_message(user_id, 'Часто задаваемые вопросы', keyboard=keyboard)

def answer_question(user_id, text):
    keyboard = VkKeyboard(one_time=False)
    set_user_state(user_id, 'answer_question')
    if text.title() in [el.title() for el in answer.keys()]:
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        send_message(user_id, f'{answer.get((text[0].upper() + text[1:]))}', keyboard=keyboard)
    else:
        keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_button('Помощь', color=VkKeyboardColor.POSITIVE)
        send_message(user_id, 'Не понимаю, что за вопрос Вы задали. Попробуйте обратиться через меню "Помощь" к оператору', keyboard=keyboard)

def ticket(user_id):
    keyboard = VkKeyboard(one_time=False, inline=True)    
    keyboard_from_user = VkKeyboard(one_time=True)

    user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name') 
    full_name = user_info[0]['first_name'] + " " + user_info[0]['last_name']

    for specialist_id in support_specialists_ids:

        keyboard.add_callback_button(label='Перейти к диалогу', color=VkKeyboardColor.POSITIVE, payload={"type": "open_link", "link": f"https://vk.com/gim220612553?sel={user_id}"})
        send_message(specialist_id, f'Пользователь {full_name} запрашивает техническую поддержку.', keyboard=keyboard)

        keyboard_from_user.add_button('Вопрос закрыт', color=VkKeyboardColor.POSITIVE)
        send_message(user_id, 'В скором времени Вы будете соединены со специалистом технической поддержки.', keyboard=keyboard_from_user)


already_called = False

# Обработка событий
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.from_user:
            user_id = event.obj.message["from_id"]
            text = event.obj.message["text"].lower()
            state = get_user_state(user_id)

            if datetime.datetime.now().weekday() == 2 and not already_called:
                clear_and_restore()
                already_called = True

            elif datetime.datetime.now().weekday() != 2:
                already_called = False

            handle_buttons(user_id, text, state)

    elif event.type == VkBotEventType.MESSAGE_EVENT:
        try:
            conversation_message_ids = event.object.conversation_message_id
            vk.messages.delete(
                conversation_message_ids=[conversation_message_ids],
                peer_id=event.object.peer_id,
                delete_for_all=1
            )
        except:
            ...
        vk.messages.sendMessageEventAnswer(
            event_id=event.object.event_id,
            user_id=event.object.user_id,
            peer_id=event.object.peer_id,                                                   
            event_data=json.dumps(event.object.payload))
