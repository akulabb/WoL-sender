import telebot, time, requests, subprocess
from telebot.types import Message, User
from secret import BOT_API, IP, ADMIN_CHAT_IDS, USERNAME


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
    try:
        mac = message.text.split(' ')[1]
    except Exception as e:
        mac = ''
        bot.send_message(message.chat.id, "Provide a valid MAC adress: /boot XX:XX:XX:XX:XX:XX")
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
        bot.send_message(message.chat.id, f"Неправильный пользователь. {USERNAME}")
        print(f"[{time.strftime('%H:%M:%S')}] неавторизованная попытка запуска от: \n{message.from_user.first_name} Username: {message.from_user.username}({message.from_user.id})")
    print(f"[{time.strftime('%H:%M:%S')}] Действие завершено. Бот снова спит в ожидании.")


@bot.message_handler(commands=['boot', 'wake'])
def handle_action_command(message: Message):
    perform_action(message)


if __name__ == '__main__':
    print("Бот успешно запущен на сервере и ожидает команду /boot...")
    bot.polling(non_stop=True, interval=3)