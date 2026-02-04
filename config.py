# --------------------------------------------- #
# Plugin Name           : Telegram Support Bot  #
# Автор                 : fabston               #
# Файл                  : config.py             #
# --------------------------------------------- #

# Telegram
token = '8230675731:AAG802jRLKPhzsAbJ5Iv98N_sMHoh0f0nqk'      # Подробнее: https://core.telegram.org/bots#3-how-do-i-create-a-bot

# Support Chat (Chat ID)
support_chat = '-1003593410850'               # Пример: -1001429781350 | Узнать ID своего канала можно тут: https://t.me/getidsbot

# Прочие настройки
time_zone           = 'GMT+2'   # Настройка временной зоны
bad_words_toggle    = True      # Включить/отключить фильтрацию ненормативной лексики
spam_toggle         = True      # Включить/отключить защиту от спама
spam_protection     = 5         # Максимальное количество сообщений подряд без ответа команды
open_ticket_emoji   = 24        # Через X часов после последнего обращения появляется смайлик в списке "/tickets"

# Сообщения
text_messages = {
    'start': 'Здравствуйте {}, как мы можем Вам помочь?',
    'faqs': 'Здесь располагается ваш текст с частыми вопросами.',
    'support_response': 'Отправлено сотрудником: {}'  # Ответ службы поддержки добавляется автоматически. {} = заменяется именем сотрудника.
}

# Regular Expressions (https://regex101.com/)
regex_filter = {
    'bad_words': r'(?i)^(.*?(\b\w*fuck|shut up|dick|bitch|bastard|cunt|bollocks|bugger|rubbish|wanker|twat|suck|ass|pussy|arsch\w*\b)[^$]*)$'
}
