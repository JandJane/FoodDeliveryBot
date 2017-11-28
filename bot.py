# -*- coding: utf-8 -*-
import config
import telebot
from telebot import types
import pandas as pd
import time

menu = pd.read_csv('menu.csv', sep=',', encoding='cp1251')
SECTIONS = menu['section'].unique()
TOTAL = menu.shape[0]

WAITING_FOR = [None, 'order', 'address', 'phone', 'delivery_time', None]

bot = telebot.TeleBot(config.token)
orders = {}   # queue of orders, user's id is a key and an object of Order type is its value


class Order:
    def __init__(self, text, user):
        self.array = form_array(text)
        self.user = user
        self.time = time.time()
        self.waiting_for = None  # indicates if the bot is waiting for user to give some data
        self.sum = 0  # the bill
        self.stage = 0
        self.address = None
        self.phone = None
        self.delivery_time = None
        self.act()

    def act(self, *args):
        if args:
            self.stage = args[0]
            self.waiting_for = WAITING_FOR[self.stage]
            if self.generate_keyboard():
                bot.send_message(self.user, self.generate_text(), reply_markup=self.generate_keyboard())
            else:
                bot.send_message(self.user, self.generate_text())
            self.stage = 5
        else:
            if self.stage < 5:
                self.stage += 1
            self.waiting_for = WAITING_FOR[self.stage]
            if self.generate_keyboard():
                bot.send_message(self.user, self.generate_text(), reply_markup=self.generate_keyboard())
            else:
                bot.send_message(self.user, self.generate_text())

    def generate_text(self):
        if self.stage == 1:
            self.sum = 0
            message = 'Ваш заказ: \n \n'
            for i in self.array:
                message += str(i) + '. ' + menu.loc[i]['dish'] + '  --  ' + str(menu.loc[i]['price']) + ' RUB \n'
                self.sum += menu.loc[i]['price']
            message += '\n Итого к оплате:  ' + str(self.sum) + ' RUB'
            message += '\n Подтвердите или измените заказ:'
            return message
        elif self.stage == 2:
            return 'Пожалуйста, введите адрес доставки'
        elif self.stage == 3:
            return 'Пожалуйста, введите номер телефона'
        elif self.stage == 4:
            return 'Пожалуйста, введите желаемое время доставки'
        elif self.stage == 5:
            self.sum = 0
            message = 'Ваш заказ: \n \n'
            for i in self.array:
                message += str(i) + '. ' + menu.loc[i]['dish'] + '  --  ' + str(menu.loc[i]['price']) + ' RUB \n'
                self.sum += menu.loc[i]['price']
            message += '\n Итого к оплате:  ' + str(self.sum) + ' RUB'
            message += '\n \n Адрес доставки: ' + self.address
            message += '\n Время доставки ' + str(self.delivery_time[0]) + ':' + str(self.delivery_time[1])
            message += '\n Ваш номер телефона ' + '+7' + self.phone
            message += '\n \n Подтвердите или измените заказ:'
            return message

    def generate_keyboard(self):
        if self.stage == 1:
            keyboard = types.InlineKeyboardMarkup()
            add_button = types.InlineKeyboardButton(text='Добавить', callback_data='order_add')
            del_button = types.InlineKeyboardButton(text='Удалить', callback_data='order_del')
            ok_button = types.InlineKeyboardButton(text='Всё верно>>', callback_data='order_confirm')
            keyboard.row(add_button, del_button, ok_button)
            return keyboard
        elif self.stage == 5:
            keyboard = types.InlineKeyboardMarkup()
            button1 = types.InlineKeyboardButton(text='Изменить заказ', callback_data='change_order')
            button2 = types.InlineKeyboardButton(text='Изменить адрес', callback_data='change_address')
            button3 = types.InlineKeyboardButton(text='Изменить телефон', callback_data='change_phone')
            button4 = types.InlineKeyboardButton(text='Изменить время', callback_data='change_delivery_time')
            button5 = types.InlineKeyboardButton(text='Всё верно, подтверждаю', callback_data='confirm')
            keyboard.row(button1, button2)
            keyboard.row(button3, button4)
            keyboard.row(button5)
            return keyboard
        else:
            return

    def add(self, text):
        self.array += form_array(text)
        self.array.sort()
        bot.send_message(self.user, self.generate_text(), reply_markup=self.generate_keyboard())

    def delete(self, text):
        delete = form_array(text)
        for element in delete:
            if element in self.array:
                self.array.remove(element)
        bot.send_message(self.user, self.generate_text(), reply_markup=self.generate_keyboard())


def generate_menu_keyboard(*args):
    keyboard = types.InlineKeyboardMarkup()
    if args:
        for section in SECTIONS:
            if section != args[0]:
                button = types.InlineKeyboardButton(text=section, callback_data=section)
                keyboard.row(button)
    else:
        for section in SECTIONS:
            button = types.InlineKeyboardButton(text=section, callback_data=section)
            keyboard.row(button)
    return keyboard


def change_keyboard(callback_query):
    keyboard = generate_menu_keyboard(callback_query.data)
    text = ''
    for index, row in menu[menu.section == callback_query.data].iterrows():
        text += str(index) + '. ' + row.dish + '  --  ' + str(row.price) + ' RUB \n'
    bot.edit_message_text(text, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,
                          reply_markup=keyboard)
    bot.answer_callback_query(callback_query.id)


def is_order(text):
    temp = text.split(',')
    order = []
    for element in temp:
        order += element.split()
    i = 0
    while i < len(order) and order[i].isdigit():
        i += 1
    return i == len(order)


def form_array(text):
    temp = text.split(',')
    order = []
    for element in temp:
        order += list(map(int, element.split()))
    order.sort()
    while order and order[0] < 0:
        order = order[1:]
    while order and order[-1] >= TOTAL:  # проверить что если элементы кончились
        order = order[:-1]
    return order


def is_phone(text):
    text1 = text.replace('(', '')
    text1 = text1.replace(')', '')
    text1 = text1.replace('-', '')
    text1 = text1.replace(' ', '')
    if len(text1) >= 1 and text1[0] == '8':
        text1 = text1[1:]
    elif len(text1) >= 2 and text1[0] == '+' and text1[1] == '7':
        text1 = text1[2:]
    else:
        return False
    if len(text1) == 10 and text1[0] == '9':
        return text1
    else:
        return False


def is_time(text):
    text1 = text.replace(' ', '')
    text1 = text1.replace(':', '')
    text1 = text1.replace('-', '')
    text1 = text1.replace('.', '')
    if text1.isdigit() and 3 <= len(text1) <= 4:
        if int(text1[-2:]) <= 59 and int(text1[:-2]) <= 24:
            return((int(text1[:-2]), int(text1[-2:])))
    return False


def handle_callback(cb_query):
    bot.answer_callback_query(cb_query.id)
    if cb_query.message.chat.id in orders:
        order = orders[cb_query.message.chat.id]
        if order.stage in [1, 5] and cb_query.data == 'order_add':
            bot.send_message(cb_query.message.chat.id,
                             'Введите через запятую или пробел номера блюд, которые хотите добавить в заказ:')
            order.waiting_for = cb_query.data
        elif order.stage in [1, 5] and cb_query.data == 'order_del':
            bot.send_message(cb_query.message.chat.id,
                             'Введите через запятую или пробел номера блюд, которые хотите удалить из заказа:')
            order.waiting_for = cb_query.data
        elif order.stage in [1, 5] and cb_query.data == 'order_confirm':
            order.act()
        elif order.stage == 5 and 'change' in cb_query.data:
            order.act(WAITING_FOR.index(cb_query.data[7:]))
        elif order.stage == 5 and cb_query.data == 'confirm':
            bot.send_message(cb_query.message.chat.id, 'Ваш заказ успешно оформлен и передан в обработку!')
            print(order.array)
            print(order.sum)
            print(order.address)
            print(order.phone)
            print(order.delivery_time)
            orders.pop(cb_query.message.chat.id)
    if cb_query.data in SECTIONS:
        change_keyboard(cb_query)


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.send_message(message.chat.id, config.introduction)


@bot.message_handler(commands=['menu'])
def handle_menu(message):
    keyboard = generate_menu_keyboard()
    bot.send_message(message.chat.id, 'Выберете раздел:', reply_markup=keyboard)


@bot.callback_query_handler(handle_callback)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    if message.chat.id in orders and time.time() - orders[message.chat.id].time <= 600:
        order = orders[message.chat.id]
        if order.waiting_for:
            if order.waiting_for == 'order_add':
                if is_order(message.text):
                    order.add(message.text)
                else:
                    bot.send_message(message.chat.id, config.error)
            elif order.waiting_for == 'order_del':
                if is_order(message.text):
                    order.delete(message.text)
                else:
                    bot.send_message(message.chat.id, config.error)
            elif order.waiting_for == 'address':
                order.address = message.text
                order.act()
            elif order.waiting_for == 'phone':
                if is_phone(message.text):
                    order.phone = is_phone(message.text)
                    order.act()
                else:
                    bot.send_message(message.chat.id, config.error)
            elif order.waiting_for == 'delivery_time':
                if is_time(message.text):
                    order.delivery_time = is_time(message.text)
                    order.act()
                else:
                    bot.send_message(message.chat.id, config.error)
    else:
        if message.chat.id in orders:
            orders.pop(message.chat.id)
        if is_order(message.text):
            orders[message.chat.id] = Order(message.text, message.chat.id)
        else:
            bot.send_message(message.chat.id, config.error)


if __name__ == '__main__':
    bot.polling(none_stop=True)