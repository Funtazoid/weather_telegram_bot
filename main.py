import json
import telebot
from telebot import types
import WeatherApi
import db
import requests


def start_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(telebot.types.KeyboardButton('\U0001F3E0 Погода в моем городе'),
                 telebot.types.KeyboardButton('\U0001F50D Погода в другом городе'),
                 telebot.types.KeyboardButton('\U00002699\U0000FE0F Параметры'))
    return keyboard


def settings_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton('🌏 Изменить город', callback_data='change_geo'),
                 telebot.types.InlineKeyboardButton('🔑 Изменить токен', callback_data='change_key'))
    return keyboard


def get_weather_for_inline(request_id, tg_id):
    result = None
    key = db.get_user_key(tg_id)
    geo = db.get_user_geo(tg_id)
    if key is None or geo is None:
        result = '❌ Вы не авторизованы, введите команду /start'
        return result
    else:
        weather = WeatherApi.WeatherApi(key, geo)
        weather.get()
        if request_id == 0:
            result = '🏙️  {0}' \
                     '\n\n🌡️  {1}°C / {2}' \
                     '\n🚩  По ощущениям {7}°C' \
                     '\n\n⏲️  Давление {3} мм' \
                     '\n💧  Влажность {4}%' \
                     '\n🌀  Ветер {5} м/c {6}' \
                .format(
                    weather.city,
                    weather.temp,
                    weather.description,
                    weather.pressure,
                    weather.humidity,
                    weather.wind[0],
                    weather.wind[1],
                    weather.feels
                )
        elif request_id == 1:
            result = '{0} {1}°C'.format(weather.city, weather.temp)
        return result


def get_another_city_for_inline(request_id, tg_id, geo):
    result = None
    key = db.get_user_key(tg_id)
    if key is None:
        result = '❌ Вы не авторизованы, введите /start'
        return result
    else:
        weather = WeatherApi.WeatherApi(key, geo)
        if weather.get() == 200:
            if request_id == 0:
                result = '🏙️  {0}' \
                         '\n\n🌡️  {1}°C / {2}' \
                         '\n🚩  По ощущениям {7}°C' \
                         '\n\n⏲️  Давление {3} мм' \
                         '\n💧  Влажность {4}%' \
                         '\n🌀  Ветер {5} м/c {6}' \
                    .format(
                        weather.city,
                        weather.temp,
                        weather.description,
                        weather.pressure,
                        weather.humidity,
                        weather.wind[0],
                        weather.wind[1],
                        weather.feels
                    )
            elif request_id == 1:
                result = '🔍 {0} - {1}°C'.format(weather.city, weather.temp)
        else:
            result = '❌ Нет такого города'
        return result


def main():
    with open('config.json') as f:
        conf = json.load(f)
    bot_token = conf['bot_api_key']
    bot = telebot.TeleBot(bot_token)

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        key = db.get_user_key(message.from_user.id)
        if key is None:
            msg = bot.send_message(message.from_user.id,
                                   '<b>Авторизация. Шаг 1/2</b>'
                                   '\n\n🔑 Введите токен OpenWeatherApi',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, welcome_step2)
        else:
            bot.send_message(message.from_user.id, 'Вы уже авторизованы 🙂')

    def welcome_step2(message):
        key = message.text
        r = requests.get('https://api.openweathermap.org/data/2.5/weather', params={'q': 'Moscow', 'appid': key})
        if r.status_code == 200:
            msg = bot.send_message(message.from_user.id,
                                   '<b>Авторизация. Шаг 2/2</b>\n\n'
                                   '🌏 Теперь введите ваше местоположение (город, например: Новосибирск)',
                                   parse_mode='html')
            bot.register_next_step_handler(msg, welcome_step3, key)
        else:
            msg = bot.send_message(message.from_user.id,
                                   '❌ Указан неверный токен, либо соединение с сервером OpenWeather отсутствует\n'
                                   'Попробуйте еще раз')
            bot.register_next_step_handler(msg, welcome_step2)

    def welcome_step3(message, key):
        r = requests.get('https://api.openweathermap.org/data/2.5/weather', params={'q': message.text, 'appid': key})
        if r.status_code == 200:
            db.register_user(message.from_user.id, key, message.text)
            bot.send_message(message.from_user.id,
                             '✔️ Авторизация прошла успешно, теперь вы можете получать данные о погоде',
                             reply_markup=start_keyboard())
        else:
            msg = bot.send_message(message.from_user.id,
                                   '❌ Такого города не существует, либо соединение с сервером OpenWeather отсутствует'
                                   '\nПопробуйте еще раз')
            bot.register_next_step_handler(msg, welcome_step3, key)

    @bot.message_handler(commands=['weather'])
    def send_weather(message):
        key, geo = db.get_user_key(message.from_user.id), db.get_user_geo(message.from_user.id)
        if key is None or geo is None:
            bot.send_message(message.from_user.id, '❌ Вы не авторизованы, введите команду /start')
        else:
            weather = WeatherApi.WeatherApi(key, geo)
            if weather.get() == 200:
                bot.send_message(message.from_user.id,
                                 '🏙️  <b>{0}</b>'
                                 '\n\n🌡️  <b>{1}°C / {2}</b>'
                                 '\n🚩  По ощущениям <b>{7}°C</b>'
                                 '\n\n⏲️  Давление <b>{3} мм</b>'
                                 '\n💧  Влажность <b>{4}%</b>'
                                 '\n🌀  Ветер <b>{5} м/c {6}</b>'
                                 .format(
                                     weather.city,
                                     weather.temp,
                                     weather.description,
                                     weather.pressure,
                                     weather.humidity,
                                     weather.wind[0],
                                     weather.wind[1],
                                     weather.feels
                                 ),
                                 parse_mode='html', reply_markup=start_keyboard())
            else:
                bot.send_message(message.from_user.id,
                                 '❌ Не удалось получить данные о погоде, пожалуйста, попробуйте позднее!')

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        if message.text == '\U0001F3E0 Погода в моем городе':
            send_weather(message)
        elif message.text == '\U0001F50D Погода в другом городе':
            msg = bot.reply_to(message, 'Введите название города')
            bot.register_next_step_handler(msg, another_city)
        elif message.text == '\U00002699\U0000FE0F Параметры':
            bot.send_message(message.from_user.id, "⚙️ <b>Настройки</b>",
                             parse_mode='html',
                             reply_markup=settings_keyboard())

    def another_city(message):
        geo = message.text
        key = db.get_user_key(message.from_user.id)
        if key is None:
            bot.send_message(message.from_user.id, '❌ Вы не авторизованы, введите /start')
        else:
            weather = WeatherApi.WeatherApi(key, geo)
            if weather.get() == 200:
                bot.send_message(message.from_user.id,
                                 '🏙️  <b>{0}</b>'
                                 '\n\n🌡️  <b>{1}°C / {2}</b>'
                                 '\n🚩  По ощущениям <b>{7}°C</b>'
                                 '\n\n⏲️  Давление <b>{3} мм</b>'
                                 '\n💧  Влажность <b>{4}%</b>'
                                 '\n🌀  Ветер <b>{5} м/c {6}</b>'
                                 .format(
                                     weather.city,
                                     weather.temp,
                                     weather.description,
                                     weather.pressure,
                                     weather.humidity,
                                     weather.wind[0],
                                     weather.wind[1],
                                     weather.feels
                                 ),
                                 parse_mode='html', reply_markup=start_keyboard())
            else:
                msg = bot.send_message(message.from_user.id, '❌ Такого города не существует\nПопробуйте еще раз')
                bot.register_next_step_handler(msg, another_city)

    @bot.inline_handler(lambda query: len(query.query) == 0)
    def query_text(inline_query):
        try:
            r = types.InlineQueryResultArticle('1', get_weather_for_inline(1, inline_query.from_user.id),
                                               types.InputTextMessageContent(
                                                   get_weather_for_inline(0, inline_query.from_user.id)))
            bot.answer_inline_query(inline_query.id, [r])
        except Exception as e:
            print(e)

    @bot.inline_handler(lambda query: len(query.query) > 0)
    def query_text(inline_query):
        try:
            r = types.InlineQueryResultArticle('1',
                                               get_another_city_for_inline(1, inline_query.from_user.id, inline_query.query),
                                               types.InputTextMessageContent(
                                                   get_another_city_for_inline(0, inline_query.from_user.id, inline_query.query)))
            bot.answer_inline_query(inline_query.id, [r])
        except Exception as e:
            print(e)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        if call.data == 'change_geo':
            msg = bot.send_message(call.from_user.id, '🌏 Введите город, который хотите сделать стандартным')
            bot.register_next_step_handler(msg, change_geo)
        elif call.data == 'change_key':
            msg = bot.send_message(call.from_user.id, '🔑 Введите новый токен OpenWeatherApi')
            bot.register_next_step_handler(msg, change_key)

    def change_geo(message):
        geo = message.text
        db.put_user_geo(message.from_user.id, geo)
        bot.send_message(message.from_user.id, '🌏 Настройки обновлены', reply_markup=start_keyboard())

    def change_key(message):
        key = message.text
        db.put_user_geo(message.from_user.id, key)
        bot.send_message(message.from_user.id, '🔑 Настройки обновлены', reply_markup=start_keyboard())

    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    main()
