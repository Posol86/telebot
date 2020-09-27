import telebot
import sqlite3
from collections import defaultdict

token = '1281128797:AAEPVf9dxrokzsDXpe0jtiZNmrxlLb_cJWA'
START, TITLE, PHOTO, LOCATION, CONFIRMATION = range(5)
USER_STATE = defaultdict(lambda: START)
RESTORAN = defaultdict(lambda: {})
ALL_REST = []

bot = telebot.TeleBot(token)

@bot.message_handler(func=lambda message: get_state(message) == START, commands=['add'])
def handle_message(message):
    bot.send_message(message.chat.id, text='Напишите наименование ресторана')
    update_state(message, TITLE)

@bot.message_handler(func=lambda message: get_state(message) == TITLE)
def handle_title(message):
    update_product(message.chat.id, 'title', message.text)
    bot.send_message(message.chat.id, text='Вставьте фото ресторана')
    update_state(message, PHOTO)

@bot.message_handler(func=lambda message: get_state(message) == PHOTO, content_types=['photo'])
def handle_photo(message):
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    update_product(message.chat.id, 'photo', downloaded_file)
    bot.send_message(message.chat.id, text='Добавьте локацию ресторана')
    update_state(message, LOCATION)

@bot.message_handler(func=lambda message: get_state(message) == LOCATION, content_types=['location'])
def handle_location(message):
    update_product(message.chat.id, 'location', message.location)
    product = get_product(message.chat.id)
    bot.send_message(message.chat.id, text='Записать данные ресторана {}?'.format(product['title']))
    update_state(message, CONFIRMATION)

@bot.message_handler(func=lambda message: get_state(message) == CONFIRMATION)
def handle_confirmation(message):
    if 'да' in message.text.lower():
        save_rest(message.chat.id)
        bot.send_message(message.chat.id, text='Ресторан внесен в список')
    update_state(message, START)

def get_state(message):
    return USER_STATE[message.chat.id]

def update_state(message, state):
    USER_STATE[message.chat.id] = state

def update_product(user_id, key, value):
    RESTORAN[user_id][key] = value

def save_rest(user_id):
    conn = sqlite3.connect("telec_sql.db")
    cursor = conn.cursor()
    ALL_REST.append(RESTORAN[user_id])
    arest = RESTORAN[user_id]
    titleBD = arest['title']
    latitudeBD = arest['location'].latitude
    longtitudeBD = arest['location'].longitude
    photoPD = sqlite3.Binary(arest['photo'])
    sql = """INSERT INTO restoran(id, user_id, title, latitude, longitude, photo) VALUES (NULL, ?, ?, ?, ?, ?)"""
    cursor.execute(sql, (user_id, titleBD, latitudeBD, longtitudeBD, photoPD))
    conn.commit()
    conn.close()

def get_product(user_id):
    return RESTORAN[user_id]


@bot.message_handler(func=lambda message: get_state(message) == START, commands=['list'])
def handle_message(message):
    conn = sqlite3.connect("telec_sql.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT title, latitude, longitude, photo FROM restoran WHERE user_id = ? ORDER BY title LIMIT 10", (message.chat.id,))
        databd = cursor.fetchall()
        bot.send_message(message.chat.id, text='Перечень ресторанов:')
        for singledata in databd:
            title, lat, lon, photo = singledata
            if photo != None:
                bot.send_photo(message.chat.id, photo, caption='Ресторан: ' + title)
                bot.send_location(message.chat.id, lat, lon)
            else:
                bot.send_message(message.chat.id, text='Ресторан: ' + title)
                bot.send_location(message.chat.id, lat, lon)
    except:
        bot.send_message(message.chat.id, text='Данные по ресторанам отсутвуют')
    conn.close()


@bot.message_handler(func=lambda message: get_state(message) == START, commands=['reset'])
def handle_message(message):
    conn = sqlite3.connect("telec_sql.db")
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM restoran WHERE user_id = ?', (message.chat.id,))
        conn.commit()
        cursor.close()
        bot.send_message(message.chat.id, text='Данные удалены')
    except:
        bot.send_message(message.chat.id, text='Данные по ресторанам отсутвуют')
    conn.close()


bot.polling()
