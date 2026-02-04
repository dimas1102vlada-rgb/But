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

# Внутренняя память тикетов и данных о пользователях
open_tickets = []
banned_users = set()
support_chat_id = config.support_chat

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

# Команда помощи (FAQ)
@bot.message_handler(commands=['faq'])
def show_faq(message):
    if message.chat.type == 'private':
        bot.reply_to(message, config.text_messages['faqs'], parse_mode='Markdown', disable_web_page_preview=True)
    else:
        pass

# Получение всех открытых тикетов
@bot.message_handler(commands=['tickets', 't'])
def list_tickets(message):
    if message.chat.id == support_chat_id:
        if not open_tickets:
            bot.reply_to(message, "ℹ️ Отличная работа, вы ответили на все тикеты!")
            return

        ot_msg = '📨 *Открытые тикеты:*\n\n'
        for ticket in open_tickets:
            user_id = ticket["user_id"]
            user = bot.get_chat(user_id)
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            full_name = f'{first_name} {last_name}'
            link = f'tg://user?id={user_id}'
            ot_msg += f"• {full_name} ({user_id})\n➜ Перейти к пользователю: {link}\n"

        bot.send_message(message.chat.id, ot_msg, parse_mode='Markdown')
    else:
        pass

# Закрытие тикета вручную
@bot.message_handler(commands=['close', 'c'])
def close_ticket(message):
    if message.chat.id == support_chat_id:
        if message.reply_to_message and '#id' in message.reply_to_message.text:
            user_id = int(message.reply_to_message.text.split('#id')[1].split(')')[0])
            found = next((t for t in open_tickets if t["user_id"] == user_id), None)
            if found:
                open_tickets.remove(found)
                bot.reply_to(message, '✅ Ок, закрыли тикет этого пользователя!')
            else:
                bot.reply_to(message, '❌ У этого пользователя нет активного тикета.')
        else:
            bot.reply_to(message, 'ℹ️ Нужно ответить на сообщение')
    else:
        pass

# Забанить пользователя
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.id == support_chat_id:
        if message.reply_to_message and '#id' in message.reply_to_message.text:
            user_id = int(message.reply_to_message.text.split('#id')[1].split(')')[0])
            if user_id in banned_users:
                bot.reply_to(message, '❌ Этот пользователь уже заблокирован...')
            else:
                banned_users.add(user_id)
                bot.reply_to(message, '✅ Ок, заблокировали этого пользователя!')
        else:
            bot.reply_to(message, 'ℹ️ Нужно ответить на сообщение')
    else:
        pass

# Разбанить пользователя
@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.chat.id == support_chat_id:
        if message.reply_to_message and '#id' in message.reply_to_message.text:
            user_id = int(message.reply_to_message.text.split('#id')[1].split(')')[0])
            if user_id in banned_users:
                banned_users.discard(user_id)
                bot.reply_to(message, '✅ Ок, разблокировали этого пользователя!')
            else:
                bot.reply_to(message, '❌ Этот пользователь уже разблокирован...')
        else:
            bot.reply_to(message, 'ℹ️ Нужно ответить на сообщение')
    else:
        pass

# Получение списка забаненных пользователей
@bot.message_handler(commands=['banned'])
def list_banned(message):
    if message.chat.id == support_chat_id:
        if not banned_users:
            bot.reply_to(message, "ℹ️ Хорошие новости, никто пока не забанен...")
            return

        b_msg = '⛔️ *Заблокированные пользователи:*\n\n'
        for user_id in banned_users:
            user = bot.get_chat(user_id)
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            full_name = f'{first_name} {last_name}'
            link = f'tg://user?id={user_id}'
            b_msg += f"• {full_name} ({user_id})\n➜ Перейти к пользователю: {link}\n"

        bot.send_message(message.chat.id, b_msg, parse_mode='Markdown')
    else:
        pass

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
    bot.reply_to(message, '✅ Ваше сообщение передано службе поддержки. Скоро ответим.')

# Обработка сообщений (Поддержка → Пользователь)
@bot.message_handler(func=lambda message: message.chat.id == support_chat_id, content_types=['text', 'photo', 'document'])
def handle_reply_from_support(message):
    if message.reply_to_message:
        original_message = message.reply_to_message
        target_user_id = original_message.forward_from.id
        bot.copy_message(target_user_id, support_chat_id, message.message_id)
        bot.reply_to(message, 'Сообщение доставлено пользователю.')

# Главная точка входа
if __name__ == '__main__':
    print("Telegram Support Bot запущен...")
    bot.polling(none_stop=True)
