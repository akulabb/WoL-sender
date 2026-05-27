import gc
import network, socket, re
import time
import utelegram as utg
from secret import IP, WIFI_SSID, WIFI_PASSWORD, BOT_API, ADMIN_CHAT_IDS, USERNAME

bot = utg.ubot(BOT_API)



wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("Подключение к Wi-Fi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        pass
print("Wi-Fi подключен! IP-адрес:", wlan.ifconfig()[0])

def check_server_status(timeout=None):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 9000))
    sock.settimeout(timeout)

    print("created socket, waiting for server...")
    try:
        data, addr = sock.recvfrom(1024)
        data = data.strip()
        print(f"Получены данные от {addr}: {data}")
        if data.decode() == 'ON':
            sock.close()
            return 1
        else:
            sock.close()
            return 0

    except OSError as e:
        print("Время ожидания истекло! Данные не получены.")
        sock.close()
        return 0


def send_wol(mac_address, ip='192.168.1.255'):
    # Удаляем разделители (колоны, дефисы) и переводим в байты
    cleaned_mac = re.sub(r'[:.-]', '', mac_address)
    if len(cleaned_mac) != 12:
        raise ValueError("Неверный формат MAC-адреса")

    mac_bytes = bytes.fromhex(cleaned_mac)
    # Формируем Magic Packet: 6 байт 0xFF + MAC-адрес, повторенный 16 раз
    packet = b'\xff' * 6 + mac_bytes * 16

    #print(packet)

    # Отправляем как UDP-бродкаст на порт 9
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Отправляем на ограниченный бродкаст адрес
    sock.sendto(packet, (ip, 9))
    sock.close()
    print("Magic Packet отправлен на MAC:", mac_address)

def perform_action(message):
    t = time.localtime()
    current_time = f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
    
    chat_id = message['message']['chat']['id']
    print(f"[{current_time}] Команда получена от пользователя {chat_id}.")
    try:
        mac = message['message']['text'].split(' ')[1]
    except Exception as e:
        mac = ''
        bot.send(chat_id, "Provide a valid MAC address: /boot XX:XX:XX:XX:XX:XX")
        return
    #print(mac)
    if chat_id in ADMIN_CHAT_IDS:
        send_wol(mac)
        bot.send(chat_id, 'Sent boot request')
    else:
        bot.send(chat_id, f"Неправильный пользователь. {USERNAME}")
        bot.send(ADMIN_CHAT_IDS[0], f"[{current_time}] неавторизованная попытка запуска от: \n{message['message']['from']['first_name']} ({chat_id})")
        print(f"[{current_time}] неавторизованная попытка запуска от: \n{message['message']['from']['first_name']} ({chat_id})")
    print(f"[{current_time}] Действие завершено. Бот снова спит в ожидании.")

def reply_ping(message):
    bot.send(message['message']['chat']['id'], 'pong')

def boot_server(message):
    perform_action(message)


bot.register('/ping', reply_ping)
bot.register('/boot', boot_server)

print('starting bot')

server_is_offline = True

while True:
    while server_is_offline:
        print('server is offline')
        bot.read_once()
        if check_server_status(3.0) == 1:
            server_is_offline = False
        time.sleep(1)
        gc.collect()
    if check_server_status() == 0:
        server_is_offline = True
    else:
        server_is_offline = False
    gc.collect()


