import telebot, time, requests, subprocess
from telebot.types import Message
from secret import BOT_API, IP, ADMIN_CHAT_IDS


bot = telebot.TeleBot(BOT_API)


def request_wol(mac_address):
    data = {"mac" : mac_address}
    response = requests.post(IP, json=data)
    print(f"server responded: {response}")
    if response.status_code == 200:
        return 0
    else:
        return response

def perform_action(message: Message):
    print(f"[{time.strftime('%H:%M:%S')}] Команда получена от пользователя {message.chat.id}.")
    mac = message.text.split(' ')[1]
    #print(mac)
    if message.chat.id in ADMIN_CHAT_IDS:
        status = request_wol(mac)
        if status == 0:
            bot.send_message(message.chat.id, "Boot request sended")
            print("сервер запущен")
        else:
            print(f"ERROR: {status}")
            bot.send_message(message.chat.id, f"Boot request error {status}")
    else:
        bot.send_message(message.chat.id, "Неправильный пользователь. @Akula_nad")
        print(f"неавторизованная попытка запуска от {message.chat.id}")
    print(f"[{time.strftime('%H:%M:%S')}] Действие завершено. Бот снова спит в ожидании.")


@bot.message_handler(commands=['boot', 'wake'])
def handle_action_command(message: Message):
    perform_action(message)


if __name__ == '__main__':
    print("Бот успешно запущен на сервере и ожидает команду /boot...")
    bot.polling(non_stop=True, interval=3)