import telebot
from telebot import types
import bd_session
from bd_tables import Users, Pictures, UseKeys
from random import randrange, choice

TOKEN = '6250800263:AAHiZE1-C91jvjbtMW3SBFDgudK0Ef0Ajwc'

bot = telebot.TeleBot(TOKEN)

name, description, price, downloaded_file = '', '', 0, None  # Для добавления картинки
number, pic, pictures = 0, None, None  # Для отправки картинки пользователю


@bot.message_handler(commands=['start'])
def get_text_messages(message):  # Команда старт при самом первом запуске бота
    db_sess = bd_session.create_session()
    u = db_sess.query(Users).all()
    user_all = [us.id for us in u]
    if message.from_user.id not in user_all:  # Проверка есть ли такой id в db
        user = Users(
            id=message.from_user.id,
            name=message.from_user.username,
            money=10000,
            images=0,
            creatkey='')
        db_sess.add(user)
        db_sess.commit()

    bot.send_message(message.from_user.id, "Привет мальчикам - зайчикам, девочкам - белочкам! "
                                           "Чем я могу тебе помочь?")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):  # Основной текстовый метод (всё начинается от сюда)
    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет мальчикам - зайчикам, девочкам - белочкам! "
                                               "Чем я могу тебе помочь?")
    elif message.text == "/help":
        help(message)
    elif message.text == '/create':
        creat(message)
    elif message.text == '/search':
        search(message)
    elif message.text == '/leaders':
        leaders(message)
    elif message.text == '/referal':
        referal(message)
    elif message.text == '/balance':
        balance(message)
    else:
        bot.send_message(message.from_user.id, "Дорогой(ая), я тебя не понимаю. Напиши /help.")


@bot.message_handler(commands=['help'])
def help(message):  # Команда help
    bot.send_message(message.from_user.id, "Это бот для создания NFT картинок. Есть несколько команд:\n"
                                           "/create - создаёт новую картинку\n"
                                           "/search - выдаёт рандомную картинку для покупки\n"
                                           "/leaders - список лидеров по загрузке/создания NFT\n"
                                           "/referal - создание собственного или активация чужого реферального "
                                           "ключа\n"
                                           "/balance - показывает твой баланс в данную секунду",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(content_types=['text', 'photo'], commands=['create'])
def creat(message):  # Создание картинки и добавление в db
    @bot.message_handler(content_types=['text'])
    def name_picture(message):  # Получение названия картинки
        global name

        name = message.text

        db_sess = bd_session.create_session()
        p = db_sess.query(Pictures).all()
        pictures = [picture.picture for picture in p]  # Список имён уже существующих картинок

        if f'{name}.jpg' in pictures:  # Проверка есть ли такое название картинки
            bot.send_message(message.from_user.id, 'Прости, картинка с таким именем уже есть. Придумай другое')
            bot.register_next_step_handler(message, name_picture)
        else:
            bot.send_message(message.from_user.id, 'Введите описание картинки')
            bot.register_next_step_handler(message, description_picture)

    @bot.message_handler(content_types=['text'])
    def description_picture(message):  # Получение описания картинки
        global description

        description = message.text

        bot.send_message(message.from_user.id, 'Введите цену картинки')
        bot.register_next_step_handler(message, price_picture)

    @bot.message_handler(content_types=['text'])
    def price_picture(message):  # Получение цены картинки
        global price

        if message.text in ['выйти', 'Выйти']:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())
            return
        try:
            price = round(float(message.text))

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Да")
            btn2 = types.KeyboardButton("Нет")
            markup.add(btn1, btn2)

            bot.send_message(message.from_user.id, f'Публикация картинки будет стоить {price * 0.05}. Продолжаем?',
                             reply_markup=markup)

            bot.register_next_step_handler(message, continue_picture)
        except Exception:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Выйти")
            markup.add(btn1)

            bot.send_message(message.from_user.id, 'Сожалею, но вы ввели не то и не так. Нужно было ввести число. '
                                                   'Попробуйте ещё раз', reply_markup=markup)

            bot.register_next_step_handler(message, price_picture)

    @bot.message_handler(content_types=['photo'])
    def photo(message):  # Получение картинки
        global downloaded_file

        if message.text in ['выйти', 'Выйти']:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())
            return
        try:
            fileID = message.photo[-1].file_id
            file_info = bot.get_file(fileID)
            downloaded_file = bot.download_file(file_info.file_path)

            with open(f'pictures/{name}.jpg', 'wb') as new_file:
                new_file.write(downloaded_file)
        except Exception:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Выйти")
            markup.add(btn1)

            bot.send_message(message.from_user.id, 'Я не совсем уверена, что это картинка ... Попробуй ещё раз',
                             reply_markup=markup)

            bot.register_next_step_handler(message, photo)
        try:
            # Списывание средств за публикацию и +1 в db к опубликованным картинкам
            db_sess = bd_session.create_session()
            user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
            user.money -= price * 0.05
            user.images += 1
            db_sess.commit()
            picture = Pictures(
                user_id=message.from_user.id,
                picture=f'{name}.jpg',
                cost=price,
                description=description)
            db_sess.add(picture)  # Добавление в db всё о картинке
            db_sess.commit()

            bot.send_message(message.from_user.id, 'Спасибочки, милашка! Твоя картинка добавлена в базу данных!',
                             reply_markup=types.ReplyKeyboardRemove())
            return
        except Exception:
            bot.send_message(message.from_user.id, 'Прости! Возникла какая-то ошибка. Я не могу решить её сама.'
                                                   'Давай ты попробуешь ещё раз с самого начала, но в другой раз',
                             reply_markup=types.ReplyKeyboardRemove())
            return

    @bot.message_handler(content_types=['text'])
    def continue_picture(message):  # Вопрос: хочет ли пользователь опубликовать картинку (заплатить за публикацию)
        global flag
        if message.text in ['Да', 'Конечно', 'Давай', 'Продолжаем', 'да', 'конечно', 'давай', 'продолжаем']:
            bot.send_message(message.from_user.id, 'Отправьте картинку', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, photo)
        else:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())
            return

    bot.send_message(message.from_user.id, 'Введите название картинки')

    bot.register_next_step_handler(message, name_picture)


@bot.message_handler(content_types=['text'], commands=['search'])
def search(message):  # Покупка картинки
    global number, pic, pictures

    db_sess = bd_session.create_session()
    p = db_sess.query(Pictures).all()
    pictures = [picture.picture for picture in p]  # Все название картинок в db
    pictures1 = [picture.picture for picture in p]  # Тоже самое, но резерв (дальше нужно будет)
    number = randrange(len(pictures))
    pic = pictures[number]
    pict = db_sess.query(Pictures).filter(Pictures.picture == pic, Pictures.user_id != message.from_user.id).first()
    if pict is None:  # Если в db только картинки от одного пользователя
        bot.send_message(message.from_user.id, 'Прости, в моей базе данных нет других картинок, кроме твоих! '
                                               'Дождись пока другие пользователи опубликуют свои картинки',
                         reply_markup=types.ReplyKeyboardRemove())
        return
    bot.send_photo(message.from_user.id, open(f'pictures/{pic}', 'rb'))  # Отправка картинки пользователю
    pr = pict.cost
    ds = pict.description

    @bot.message_handler(content_types=['text'])
    def buy_picture(message):  # Покупка картинки (купить, дальше, выйти)
        global number, pic, pictures

        if message.text in ['Купить', 'Покупаю', 'купить', 'покупаю']:  # Сама покупка, списание денег
            pict = db_sess.query(Pictures).filter(Pictures.picture == pic).first()
            pr = pict.cost
            us_id = pict.user_id
            user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
            user.money -= pr
            db_sess.commit()
            user = db_sess.query(Users).filter(Users.id == us_id).first()
            user.money += pr
            db_sess.commit()

            bot.send_message(message.from_user.id, 'Ты только что купил эту картинку. ПОЗДРАВЛЯЮ С ПРЕОБРЕТЕНИЕМ!',
                             reply_markup=types.ReplyKeyboardRemove())
            return
        elif message.text in ['Идём дальше', 'Идем дальше', 'Дальше', 'дальше', 'идём дальше', 'идем дальше']:
            del pictures[number]
            # Повторная отправка (если "дальше")
            if len(pictures) == 0:  # Обновление списка названий картинок
                pictures = pictures1.copy()

            number = randrange(len(pictures))
            pic = pictures[number]
            # Получение картинок других пользователей (не данного картинок пользователя)
            pict = db_sess.query(Pictures).filter(Pictures.picture == pic,
                                                  Pictures.user_id != message.from_user.id).first()

            if pict is None:  # Если в db только картинки от одного пользователя
                bot.send_message(message.from_user.id, 'Прости, в моей базе данных нет других картинок, кроме твоих! '
                                                       'Дождись пока другие пользователи опубликуют свои картинки',
                                 reply_markup=types.ReplyKeyboardRemove())
                return

            bot.send_photo(message.from_user.id, open(f'pictures/{pic}', 'rb'))

            pr = pict.cost
            ds = pict.description

            text = f'Описание данной картинки: {ds}\n' \
                   f'Цена данной картинки: {pr}\n' \
                   f'Дальше? Купить? Или выйти?'

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Купить")
            btn2 = types.KeyboardButton("Дальше")
            btn3 = types.KeyboardButton("Выход")
            markup.add(btn1, btn2, btn3)

            bot.send_message(message.from_user.id, text, reply_markup=markup)

            bot.register_next_step_handler(message, buy_picture)
        else:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())
            return

    text = f'Описание данной картинки: {ds}\n' \
           f'Цена данной картинки: {pr}\n' \
           f'Дальше? Купить? Или выйти?'

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Купить")
    btn2 = types.KeyboardButton("Дальше")
    btn3 = types.KeyboardButton("Выход")
    markup.add(btn1, btn2, btn3)

    bot.send_message(message.from_user.id, text, reply_markup=markup)

    bot.register_next_step_handler(message, buy_picture)


@bot.message_handler(commands=['leaders'])
def leaders(message):  # Список лидеров
    def num_sort(strn):  # Сортировка
        computed_num = [ele for ele in strn.split() if ele.isdigit()]

        if len(computed_num) > 0:
            return int(computed_num[0])
        return -1

    ldrs = []
    db_sess = bd_session.create_session()

    for user in db_sess.query(Users).filter(Users.images > 0).all():
        ldrs.append(f'{user.name}. Количество картинок: {user.images}')
        ldrs = sorted(ldrs, key=num_sort, reverse=True)

    text = 'Топ 10 лидеров по картинкам:\n'

    if len(ldrs) >= 10:
        q = 10
    else:
        q = len(ldrs)
    for i in range(q):
        text += f'❤️ {ldrs[i]}\n'

    bot.send_message(message.from_user.id, text)


@bot.message_handler(commands=['referal'], content_types=['text'])
def referal(message):  # Реферальный ключ
    @bot.message_handler(content_types=['text'])
    def active_key(message):  # Активация ключа
        if message.text in ['выйти', 'Выйти']:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())
            return

        db_sess = bd_session.create_session()
        user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()

        if user.creatkey == message.text:  # Если пользователь ввёл свой собственный ключ
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Выйти")
            markup.add(btn1)

            bot.send_message(message.from_user.id, 'Как странно, этот ключ мне что-то напоминает ... '
                                                   'Точно! Это же твой реферальный ключ! '
                                                   'К сожалению, я не могу его принять. Попробуй ещё раз прямо сейчас.'
                                                   'Или можешь просто уйти и попробовать в другой раз',
                             reply_markup=markup)

            bot.register_next_step_handler(message, active_key)
        else:
            user = db_sess.query(Users).filter(Users.creatkey == message.text).first()

            if user is None:  # Если такого ключа нет в db
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                btn1 = types.KeyboardButton("Выйти")
                markup.add(btn1)

                bot.send_message(message.from_user.id, 'К сожалению, такого ключа не существует. '
                                                       'Рекомендую ещё раз проверить правильность написания ключа! '
                                                       'Можешь ввести правильный ключ прямо сейчас или уйти. Я жду!',
                                 reply_markup=markup)

                bot.register_next_step_handler(message, active_key)
            else:
                key = db_sess.query(UseKeys).filter(UseKeys.key == message.text).first()

                if message.from_user.id in key.user_id:  # Проверка на повторную активация уже активированного ключа
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = types.KeyboardButton("Выйти")
                    markup.add(btn1)

                    bot.send_message(message.from_user.id, 'К сожалению, ты уже активировал(а) такой ключ. '
                                                           'Можешь попробовать ввести ключ ещё раз прямо сейчас или '
                                                           'уйти', reply_markup=markup)

                    bot.register_next_step_handler(message, active_key)
                else:  # Все условия для активации выполнены (не свой; существующий; ещё не активировал)
                    user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
                    user.money += 5000
                    db_sess.commit()
                    user = db_sess.query(Users).filter(Users.creatkey == message.text).first()
                    user.money += 1000
                    db_sess.commit()

                    bot.send_message(message.from_user.id, 'Мои поздравления! Реферальный ключ активирован. '
                                                           'Ты же знаешь, что один реферальный ключ можно активировать '
                                                           'только один раз. В следующий раз тебе придётся вводить '
                                                           'другой реферальный ключ',
                                     reply_markup=types.ReplyKeyboardRemove())

                    db_sess = bd_session.create_session()
                    useKey = UseKeys(
                        user_id=message.from_user.id,
                        key=message.text,
                    )
                    db_sess.add(useKey)
                    db_sess.commit()
                    return

    @bot.message_handler(content_types=['text'])
    def ref_answer(message):  # Главный метод (создать, вспомнить, активировать)
        if message.text == 'Создать':  # Создание ключа
            db_sess = bd_session.create_session()
            user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
            if user.creatkey == '':  # Проверка если ли у пользователя ключ
                chars = '+-/*!&$#?=@<>abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
                while True:  # Создание ключа
                    password = ''
                    for i in range(16):
                        password += choice(chars)
                    keys = db_sess.query(Users).filter(Users.creatkey).all()
                    if password not in keys:  # Проверка есть ли такой ключ в db
                        break
                user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
                user.creatkey = password
                db_sess.commit()

                bot.send_message(message.from_user.id, f'Твой реферальный ключ: {password}')
            else:
                bot.send_message(message.from_user.id, 'У тебя уже есть реферальный ключ',
                                 reply_markup=types.ReplyKeyboardRemove())
            return
        elif message.text == 'Вспомнить':  # Если забыл свой ключ
            db_sess = bd_session.create_session()
            user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
            if user.creatkey == '':  # Проверка есть ли у пользователя ключ
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                btn1 = types.KeyboardButton("Создать")
                btn2 = types.KeyboardButton("Активировать")
                markup.add(btn1, btn2)

                bot.send_message(message.from_user.id,
                                 'У тебя нет реферального ключа. Создать? Или ты хочешь активировать ключ?',
                                 reply_markup=markup)

                bot.register_next_step_handler(message, ref_answer)
            else:
                bot.send_message(message.from_user.id, f'Твой реферальный ключ: {user.creatkey}',
                                 reply_markup=types.ReplyKeyboardRemove())
                return
        elif message.text == 'Активировать':  # Активация ключа
            bot.send_message(message.from_user.id, 'Можешь вводить ключ')

            bot.register_next_step_handler(message, active_key)
        else:  #
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())
            return

    db_sess = bd_session.create_session()
    user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
    if user.creatkey == '':  # Проверка есть ли у пользователя ключ
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Создать")
        btn2 = types.KeyboardButton("Активировать")
        btn3 = types.KeyboardButton("Выйти")
        markup.add(btn1, btn2, btn3)

        bot.send_message(message.from_user.id,
                         'У тебя нет реферального ключа. Создать? Или ты хочешь активировать ключ?',
                         reply_markup=markup)
    else:  # Если ли у пользователя есть ключ
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Вспомнить")
        btn2 = types.KeyboardButton("Активировать")
        btn3 = types.KeyboardButton("Выйти")
        markup.add(btn1, btn2, btn3)

        bot.send_message(message.from_user.id,
                         'Ты заглянул(а) сюда, чтобы активировать ключ или вспомнить свой реферальный ключ?',
                         reply_markup=markup)

    bot.register_next_step_handler(message, ref_answer)


@bot.message_handler(commands=['balance'], content_types=['text'])
def balance(message):  # Баланс пользователя
    db_sess = bd_session.create_session()
    user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
    balance = user.money

    bot.send_message(message.from_user.id,
                     f'В данную секунду твой баланс составляет: {balance}')


bd_session.global_init("bd/telebot.sqlite")
bot.polling(none_stop=True, interval=0)
