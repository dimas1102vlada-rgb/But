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

# Глобальные словари для хранения данных о пользователях и тикетах
users_data = {}
tickets_data = []

# Эмулируем создание фейковых билетов (для наглядности)
for i in range(1, 6):
    tickets_data.append({
        'user_id': i,
        'ticket_id': i,
        'timestamp': datetime.utcnow(),
        'link': f"https://example.com/ticket/{i}"
    })

# Вспомогательная функция для отправки сообщений FAQ
def send_faq(chat_id):
    bot.send_message(chat_id, config.text_messages['faqs'], parse_mode='Markdown', disable_web_page_preview=True)

# Обработчик обратных вызовов
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == "faqCallbackdata":
            send_faq(call.message.chat.id)

# Команда старта
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        chat_id = message.chat.id
        users_data.setdefault(chat_id, {'tickets': []})
        bot.send_message(chat_id,
                         config.text_messages['start'].format(message.from_user.first_name),
                         parse_mode='Markdown', disable_web_page_preview=True)
    else:
        bot.reply_to(message, 'Пожалуйста, отправьте личное сообщение, если хотите связаться с командой поддержки.')

# Команда помощи (FAQ)
@bot.message_handler(commands=['faq'])
def help_command(message):
    if message.chat.type == 'private':
        send_faq(message.chat.id)

# Список открытых тикетов
@bot.message_handler(commands=['tickets', 't'])
def list_tickets(message):
    if message.chat.type == 'private':
        chat_id = message.chat.id
        open_tickets = [
            t for t in tickets_data if t['user_id'] == chat_id and t['resolved'] is False
        ]
        if len(open_tickets) == 0:
            bot.send_message(chat_id, "Все ваши тикеты закрыты.")
        else:
            tickets_list = "\n".join([f"{t['ticket_id']} ({arrow.get(t['timestamp']).humanize()}): {t['link']}" for t in open_tickets])
            bot.send_message(chat_id, f"Ваши активные тикеты:\n{tickets_list}", parse_mode='Markdown')

# Закрыть тикет вручную
@bot.message_handler(commands=['close', 'c'])
def close_ticket(message):
    if message.chat.type == 'private':
        chat_id = message.chat.id
        args = message.text.strip().split()[1:]
        if len(args) > 0:
            ticket_id = int(args[0])  # Предполагаем, что номер тикета передан первым аргументом
            matching_tickets = [t for t in tickets_data if t['ticket_id'] == ticket_id and t['user_id'] == chat_id]
            if len(matching_tickets) > 0:
                ticket = matching_tickets[0]
                ticket['resolved'] = True
                bot.send_message(chat_id, f"Тикет №{ticket_id} закрыт.")
            else:
                bot.send_message(chat_id, f"Тикет №{ticket_id} не найден или принадлежит другому пользователю.")
        else:
            bot.send_message(chat_id, "Укажите ID тикета для закрытия.")

# Общая обработка входящих сообщений
@bot.message_handler(func=lambda message: message.chat.type == 'private', content_types=['text', 'photo', 'document'])
def handle_private_message(message):
    chat_id = message.chat.id
    users_data.setdefault(chat_id, {'tickets': []})
    bot.reply_to(message, "Получено ваше сообщение, скоро свяжемся с вами.", parse_mode="Markdown")

# Главный цикл прослушивания сообщений
if __name__ == "__main__":
    print("Telegram Support Bot запущен...")
    bot.polling(none_stop=True)
