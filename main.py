import telebot
from telebot import types
import bd_session
from bd_tables import Users, Pictures, UseKeys
from random import randrange, choice

TOKEN = '6250800263:AAHiZE1-C91jvjbtMW3SBFDgudK0Ef0Ajwc'

bot = telebot.TeleBot(TOKEN)

name, description, price, downloaded_file = '', '', 0, None
number, pic, pictures = 0, None, None


@bot.message_handler(commands=['start'])
def get_text_messages(message):
    db_sess = bd_session.create_session()
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
def get_text_messages(message):
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
def help(message):
    bot.send_message(message.from_user.id, "Это бот для создания NFT картинок. Есть несколько команд:\n"
                                           "1)/create - создаёт новую картинку\n"
                                           "2)/search - выдаёт рандомную картинку для покупки\n"
                                           "3)/leaders - список лидеров по загрузке/создания NFT\n"
                                           "4)/referal - создание собственного или активация чужого реферального "
                                           "ключа\n"
                                           "5)/balance - показывает твой баланс в данную секунду",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(content_types=['text', 'photo'], commands=['create'])
def creat(message):
    @bot.message_handler(content_types=['text'])
    def name_picture(message):
        global name

        name = message.text

        db_sess = bd_session.create_session()
        p = db_sess.query(Pictures).all()
        pictures = [picture.picture for picture in p]

        if f'{name}.jpg' in pictures:
            bot.send_message(message.from_user.id, 'Прости, картинка с таким именем уже есть. Придумай другое')
            bot.register_next_step_handler(message, name_picture)
        else:
            bot.send_message(message.from_user.id, 'Введите описание картинки')
            bot.register_next_step_handler(message, description_picture)

    @bot.message_handler(content_types=['text'])
    def description_picture(message):
        global description

        description = message.text

        bot.send_message(message.from_user.id, 'Введите цену картинки')
        bot.register_next_step_handler(message, price_picture)

    @bot.message_handler(content_types=['text'])
    def price_picture(message):
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
    def photo(message):
        global downloaded_file

        if message.text in ['выйти', 'Выйти']:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())
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
            db_sess.add(picture)
            db_sess.commit()

            bot.send_message(message.from_user.id, 'Спасибочки, милашка! Твоя картинка добавлена в базу данных!',
                             reply_markup=types.ReplyKeyboardRemove())
        except Exception:
            bot.send_message(message.from_user.id, 'Прости! Возникла какая-то ошибка. Я не могу решить её сама.'
                                                   'Давай ты попробуешь ещё раз с самого начала, но в другой раз',
                             reply_markup=types.ReplyKeyboardRemove())

    @bot.message_handler(content_types=['text'])
    def continue_picture(message):
        global flag
        if message.text in ['Да', 'Конечно', 'Давай', 'Продолжаем', 'да', 'конечно', 'давай', 'продолжаем']:
            bot.send_message(message.from_user.id, 'Отправьте картинку', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, photo)
        else:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())

    bot.send_message(message.from_user.id, 'Введите название картинки')

    bot.register_next_step_handler(message, name_picture)


@bot.message_handler(content_types=['text'], commands=['search'])
def search(message):
    global number, pic, pictures

    db_sess = bd_session.create_session()
    p = db_sess.query(Pictures).all()
    pictures = [picture.picture for picture in p]
    pictures1 = [picture.picture for picture in p]
    number = randrange(len(pictures))
    pic = pictures[number]
    bot.send_photo(message.from_user.id, open(f'pictures/{pic}', 'rb'))
    pict = db_sess.query(Pictures).filter(Pictures.picture == pic).first()
    pr = pict.cost
    ds = pict.description

    @bot.message_handler(content_types=['text'])
    def buy_picture(message):
        global number, pic, pictures

        if message.text in ['Купить', 'Покупаю', 'купить', 'покупаю']:
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
        elif message.text in ['Идём дальше', 'Идем дальше', 'Дальше', 'дальше', 'идём дальше', 'идем дальше']:
            del pictures[number]

            if len(pictures) == 0:
                pictures = pictures1.copy()

            number = randrange(len(pictures))
            pic = pictures[number]
            bot.send_photo(message.from_user.id, open(f'pictures/{pic}', 'rb'))

            pict = db_sess.query(Pictures).filter(Pictures.picture == pic).first()
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
def leaders(message):
    def num_sort(strn):
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
def referal(message):
    @bot.message_handler(content_types=['text'])
    def active_key(message):
        if message.text in ['выйти', 'Выйти']:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())

        db_sess = bd_session.create_session()
        user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()

        if user.creatkey == message.text:
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

            if user is None or len(user) == 0:
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

                if message.from_user.id in key.user_id:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = types.KeyboardButton("Выйти")
                    markup.add(btn1)

                    bot.send_message(message.from_user.id, 'К сожалению, ты уже активировал(а) такой ключ. '
                                                           'Можешь попробовать ввести ключ ещё раз прямо сейчас или '
                                                           'уйти', reply_markup=markup)

                    bot.register_next_step_handler(message, active_key)
                else:
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

    @bot.message_handler(content_types=['text'])
    def ref_answer(message):
        if message.text == 'Создать':
            db_sess = bd_session.create_session()
            user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
            if user.creatkey == '':
                chars = '+-/*!&$#?=@<>abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
                while True:
                    password = ''
                    for i in range(16):
                        password += choice(chars)
                    keys = db_sess.query(Users).filter(Users.creatkey).all()
                    if password not in keys:
                        break
                user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
                user.creatkey = password
                db_sess.commit()

                bot.send_message(message.from_user.id, f'Твой реферальный ключ: {password}')
            else:
                bot.send_message(message.from_user.id, 'У тебя уже есть реферальный ключ',
                                 reply_markup=types.ReplyKeyboardRemove())
        elif message.text == 'Вспомнить':
            db_sess = bd_session.create_session()
            user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
            if user.creatkey == '':
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
        elif message.text == 'Активировать':
            bot.send_message(message.from_user.id, 'Можешь вводить ключ')

            bot.register_next_step_handler(message, active_key)
        else:
            bot.send_message(message.from_user.id, 'Хорошо! Тогда в другой раз!',
                             reply_markup=types.ReplyKeyboardRemove())

    db_sess = bd_session.create_session()
    user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
    if user.creatkey == '':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Создать")
        btn2 = types.KeyboardButton("Активировать")
        btn3 = types.KeyboardButton("Выйти")
        markup.add(btn1, btn2, btn3)

        bot.send_message(message.from_user.id,
                         'У тебя нет реферального ключа. Создать? Или ты хочешь активировать ключ?',
                         reply_markup=markup)
    else:
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
def balance(message):
    db_sess = bd_session.create_session()
    user = db_sess.query(Users).filter(Users.id == message.from_user.id).first()
    balance = user.money

    bot.send_message(message.from_user.id,
                     f'В данную секунду твой баланс составляет: {balance}')


bd_session.global_init("bd/telebot.sqlite")
bot.polling(none_stop=True, interval=0)
