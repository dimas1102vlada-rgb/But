# --------------------------------------------- #
# Название Плагина       : Telegram Support Bot  #
# Имя Автора             : fabston               #
# Название Файла         : main.py               #
# --------------------------------------------- #

import config
import telebot
from datetime import datetime
import uuid  # Импортируем модуль UUID для генерации уникальных идентификаторов

bot = telebot.TeleBot(config.token)

# Текущие тикеты и забаненные пользователи
open_tickets = []  # Здесь будем хранить список объектов тикетов
banned_users = set()
support_chat_id = config.support_chat
admin_ids = config.admin_ids  # Список admin_ids задаётся в config.py

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
        bot.reply_to(message, 'Эта команда доступна только в приватных сообщениях.')

# Показ всех открытых тикетов
@bot.message_handler(commands=['showtickets'])
def list_tickets(message):
    if message.from_user.id in admin_ids:
        if not open_tickets:
            bot.reply_to(message, "Нет открытых заявок.")
            return

        ot_msg = '📨 *Список открытых заявок:*\n\n'
        for idx, ticket in enumerate(open_tickets):
            user_id = ticket["user_id"]
            user = bot.get_chat(user_id)
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            full_name = f'{first_name} {last_name}'
            link = f'tg://user?id={user_id}'
            ot_msg += f"• #{ticket['unique_id'][:8]} ({user_id}): {full_name}\n➜ Перейти к пользователю: {link}\n"

        bot.send_message(message.chat.id, ot_msg, parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Доступ запрещён.')

# Ответ на тикет
@bot.message_handler(commands=['answer'])
def answer_ticket(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=2)
        if len(parts) != 3:
            bot.reply_to(message, 'Формат команды: `/answer <идентификатор заявки> <сообщение>`', parse_mode="MarkdownV2")
            return

        unique_id = parts[1].strip()
        found_ticket = next((ticket for ticket in open_tickets if ticket["unique_id"] == unique_id), None)

        if found_ticket is not None:
            user_id = found_ticket["user_id"]
            response = parts[2].strip()
            
            bot.send_message(user_id, f"💬 Ответ на вашу заявку:\n{response}", parse_mode='Markdown')
            bot.reply_to(message, f"✅ Ответ отправлен пользователю {user_id}.")
            open_tickets.remove(found_ticket)  # Убираем заявку сразу после отправки ответа
        else:
            bot.reply_to(message, 'Заявка не найдена.')
    else:
        bot.reply_to(message, 'Доступ запрещён.')

# Закрытие тикета
@bot.message_handler(commands=['closeticket'])
def close_ticket(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            bot.reply_to(message, 'Формат команды: `/closeticket <идентификатор заявки>`', parse_mode="MarkdownV2")
            return

        unique_id = parts[1].strip()
        found_ticket = next((ticket for ticket in open_tickets if ticket["unique_id"] == unique_id), None)

        if found_ticket is not None:
            open_tickets.remove(found_ticket)
            user_id = found_ticket["user_id"]
            bot.send_message(user_id, 'Ваша заявка успешно закрыта.', parse_mode='Markdown')
            bot.reply_to(message, f"✅ Заявка №{unique_id[:8]} закрыта.")
        else:
            bot.reply_to(message, 'Заявка не найдена.')
    else:
        bot.reply_to(message, 'Доступ запрещён.')

# Обработка сообщений (Пользователь → Поддержка)
@bot.message_handler(func=lambda message: message.chat.type == 'private', content_types=['text', 'photo', 'document'])
def handle_support_request(message):
    user_id = message.chat.id
    
    # Проверяем наличие активных тикетов текущего пользователя
    active_tickets = any(ticket["user_id"] == user_id for ticket in open_tickets)
    
    if user_id in banned_users:
        bot.reply_to(message, 'Вы заблокированы и не можете отправить сообщение.')
        return
    
    elif active_tickets:
        bot.reply_to(message, 'У вас уже есть активная заявка. Подождите ответа.')
        return
        
    new_ticket = {
        "unique_id": str(uuid.uuid4()),  # Уникальный идентификатор тикета
        "user_id": user_id,
        "content": message.text,
        "timestamp": datetime.now()
    }
    open_tickets.append(new_ticket)
    bot.forward_message(support_chat_id, message.chat.id, message.message_id)
    bot.reply_to(message, '✅ Ваша заявка отправлена. Ожидайте ответа.')

# Главная точка входа
if __name__ == '__main__':
    print("Telegram Support Bot запущен...")
    bot.polling(none_stop=True)
