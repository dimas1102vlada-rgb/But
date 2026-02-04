# --------------------------------------------- #
# Название Плагина       : Telegram Support Bot  #
# Имя Автора             : fabston               #
# Название Файла         : main.py               #
# --------------------------------------------- #

import config
import telebot
from datetime import datetime
import arrow

bot = telebot.TeleBot(config.token)

# Текущие тикеты и забаненные пользователи
open_tickets = []
banned_users = set()
support_chat_id = config.support_chat
admin_ids = config.admin_ids  # Списка admin_ids задаётся в config.py

# Обработчики обратных вызовов
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "faqCallbackdata":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=config.text_messages['faqs'], parse_mode='Markdown',
                                  disable_web_page_preview=True)

# Команда старта
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id,
                         config.text_messages['start'].format(message.from_user.first_name),
                         parse_mode='Markdown', disable_web_page_preview=True)
    else:
        bot.reply_to(message, 'Пожалуйста, отправьте личное сообщение, если хотите связаться с командой поддержки.')

# Показ всех открытых тикетов
@bot.message_handler(commands=['showtickets'])
def list_tickets(message):
    if message.from_user.id in admin_ids:
        if not open_tickets:
            bot.reply_to(message, "Сейчас нет открытых тикетов.")
            return

        ot_msg = '📨 *Список открытых тикетов:*\n\n'
        for idx, ticket in enumerate(open_tickets):
            user_id = ticket["user_id"]
            user = bot.get_chat(user_id)
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            full_name = f'{first_name} {last_name}'
            link = f'tg://user?id={user_id}'
            ot_msg += f"• #{idx+1}: {full_name} ({user_id})\n➜ Перейти к пользователю: {link}\n"

        bot.send_message(message.chat.id, ot_msg, parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Доступ ограничен.')

# Ответ на тикет
@bot.message_handler(commands=['reply'])
def reply_to_ticket(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            bot.reply_to(message, 'Формат команды: /reply <номер тикета>')
            return

        index_str = parts[1].strip()
        try:
            index = int(index_str) - 1
            if index >= 0 and index < len(open_tickets):
                ticket = open_tickets[index]
                user_id = ticket["user_id"]
                response = message.reply_to_message.text if message.reply_to_message else ""
                bot.send_message(user_id, f"💬 Ваш тикет обработан службой поддержки:\n{response}",
                                 parse_mode='Markdown')
                bot.reply_to(message, f"✅ Ответ отправлен пользователю {user_id}.")
            else:
                bot.reply_to(message, 'Указанный тикет не найден.')
        except ValueError:
            bot.reply_to(message, 'Неверный индекс тикета.')
    else:
        bot.reply_to(message, 'Доступ ограничен.')

# Закрытие тикета
@bot.message_handler(commands=['closeticket'])
def close_ticket(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            bot.reply_to(message, 'Формат команды: /closeticket <номер тикета>')
            return

        index_str = parts[1].strip()
        try:
            index = int(index_str) - 1
            if index >= 0 and index < len(open_tickets):
                ticket = open_tickets.pop(index)
                user_id = ticket["user_id"]
                bot.send_message(user_id, 'Ваш тикет закрыт.', parse_mode='Markdown')
                bot.reply_to(message, f"✅ Тикет #{index+1} закрыт.")
            else:
                bot.reply_to(message, 'Указанный тикет не найден.')
        except ValueError:
            bot.reply_to(message, 'Неверный индекс тикета.')
    else:
        bot.reply_to(message, 'Доступ ограничен.')

# Обработка сообщений (Пользователь → Поддержка)
@bot.message_handler(func=lambda message: message.chat.type == 'private', content_types=['text', 'photo', 'document'])
def handle_support_request(message):
    user_id = message.chat.id
    if user_id in banned_users:
        bot.reply_to(message, 'Вы заблокированы и не можете общаться с поддержкой.')
        return

    new_ticket = {"user_id": user_id, "content": message.text, "timestamp": datetime.now()}
    open_tickets.append(new_ticket)
    bot.forward_message(support_chat_id, message.chat.id, message.message_id)
    bot.reply_to(message, '✅ Ваше сообщение принято службой поддержки. Ждем ответа.')

# Главная точка входа
if __name__ == '__main__':
    print("Telegram Support Bot запущен...")
    bot.polling(none_stop=True)
