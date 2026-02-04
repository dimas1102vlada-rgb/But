# --------------------------------------------- #
# Название Плагина       : Telegram Support Bot  #
# Имя Автора             : fabston               #
# Название Файла         : main.py               #
# --------------------------------------------- #

import config
import telebot
from datetime import datetime, timedelta
import uuid  # Импортируем модуль UUID для генерации уникальных идентификаторов
import threading  # Модуль для фоновых процессов

bot = telebot.TeleBot(config.token)

# Текущие тикеты и забаненные пользователи
open_tickets = []  # Здесь будем хранить список объектов тикетов
banned_users = set()  # Набор заблокированных пользователей
support_chat_id = config.support_chat
admin_ids = config.admin_ids  # Список admin_ids задаётся в config.py

# Функция очистки устаревших заявок
def clean_old_tickets():
    global open_tickets
    now = datetime.now()
    expired_tickets = [
        ticket for ticket in open_tickets
        if (now - ticket["timestamp"]) > timedelta(hours=24)
    ]
    for ticket in expired_tickets:
        open_tickets.remove(ticket)
        user_id = ticket["user_id"]
        bot.send_message(user_id, '❗️ Ваша заявка устарела и была автоматически удалена.', parse_mode='Markdown')

    # Повторяем очистку каждые 24 часа
    threading.Timer(24*60*60, clean_old_tickets).start()

# Запускаем фоновый процесс чистки заявок
clean_old_tickets()

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

# Ответ на тикет по ID пользователя
@bot.message_handler(commands=['answer'])
def answer_ticket(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=2)
        if len(parts) != 3:
            bot.reply_to(message, 'Формат команды: `/answer <id пользователя> <сообщение>`', parse_mode="MarkdownV2")
            return

        user_id = parts[1].strip()
        found_ticket = next((ticket for ticket in open_tickets if ticket["user_id"] == int(user_id)), None)

        if found_ticket is not None:
            response = parts[2].strip()
            
            bot.send_message(int(user_id), f"💬 Ответ на вашу заявку:\n{response}", parse_mode='Markdown')
            bot.reply_to(message, f"✅ Ответ отправлен пользователю {user_id}.", parse_mode='Markdown')
            open_tickets.remove(found_ticket)  # Убираем заявку сразу после отправки ответа
        else:
            bot.reply_to(message, f'Активная заявка для пользователя с ID "{user_id}" не найдена.', parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Доступ запрещён.')

# Закрытие тикета по ID пользователя
@bot.message_handler(commands=['closeticket'])
def close_ticket(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            bot.reply_to(message, 'Формат команды: `/closeticket <id пользователя>`', parse_mode="MarkdownV2")
            return

        user_id = parts[1].strip()
        found_ticket = next((ticket for ticket in open_tickets if ticket["user_id"] == int(user_id)), None)

        if found_ticket is not None:
            open_tickets.remove(found_ticket)
            bot.send_message(int(user_id), 'Ваша заявка успешно закрыта.', parse_mode='Markdown')
            bot.reply_to(message, f"✅ Заявка для пользователя {user_id} закрыта.", parse_mode='Markdown')
        else:
            bot.reply_to(message, f'Активная заявка для пользователя с ID "{user_id}" не найдена.', parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Доступ запрещён.')

# Блокировка пользователя по ID
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            bot.reply_to(message, 'Формат команды: `/ban <id пользователя>`', parse_mode="MarkdownV2")
            return

        user_id = parts[1].strip()
        if user_id.isdigit():
            user_id = int(user_id)
            if user_id in banned_users:
                bot.reply_to(message, f"Пользователь с ID `{user_id}` уже заблокирован.", parse_mode='Markdown')
            else:
                banned_users.add(user_id)
                bot.reply_to(message, f"✅ Пользователь с ID `{user_id}` заблокирован.", parse_mode='Markdown')
        else:
            bot.reply_to(message, 'Некорректный формат ID пользователя.', parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Доступ запрещён.')

# Разблокировка пользователя по ID
@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id in admin_ids:
        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            bot.reply_to(message, 'Формат команды: `/unban <id пользователя>`', parse_mode="MarkdownV2")
            return

        user_id = parts[1].strip()
        if user_id.isdigit():
            user_id = int(user_id)
            if user_id in banned_users:
                banned_users.discard(user_id)
                bot.reply_to(message, f"✅ Пользователь с ID `{user_id}` разблокирован.", parse_mode='Markdown')
            else:
                bot.reply_to(message, f"Пользователь с ID `{user_id}` не заблокирован.", parse_mode='Markdown')
        else:
            bot.reply_to(message, 'Некорректный формат ID пользователя.', parse_mode='Markdown')
    else:
        bot.reply_to(message, 'Доступ запрещён.')

# Просмотр списка забаненных пользователей
@bot.message_handler(commands=['listbans'])
def list_banned_users(message):
    if message.from_user.id in admin_ids:
        if not banned_users:
            bot.reply_to(message, "Нет заблокированных пользователей.", parse_mode='Markdown')
            return

        ban_list = '🔥 *Список заблокированных пользователей:*\n\n'
        for user_id in banned_users:
            user = bot.get_chat(user_id)
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            full_name = f'{first_name} {last_name}'
            ban_list += f"• {user_id}: {full_name}\n"

        bot.send_message(message.chat.id, ban_list, parse_mode='Markdown')
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
