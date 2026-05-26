import network
import socket
import json
import gc
import re
from secret import IP, WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("Подключение к Wi-Fi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    while not wlan.isconnected():
        pass
print("Wi-Fi подключен! IP-адрес:", wlan.ifconfig()[0])


# 2. Функция отправки Magic Packet (WoL)
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


# 3. Запуск HTTP-сервера
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))  # Слушаем 80-й порт
s.listen(5)

print("HTTP-сервер запущен и готов принимать запросы...")

#send_wol(MAC, '192.168.1.255')

while True:
    try:
        gc.collect()  # Очистка памяти, важная для ESP8266
        conn, addr = s.accept()
        request = conn.recv(1024).decode('utf-8')

        headers_end = request.find("\r\n\r\n")

        if headers_end != -1:
            headers = request[:headers_end]
            body = request[headers_end + 4:]  # То, что уже успело считаться в body

            # Ищем в заголовках Content-Length
            content_length = 0
            for line in headers.split("\r\n"):
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":")[1].strip())
                    break

            # КРИТИЧЕСКИ ВАЖНО: добираем оставшиеся байты тела, если они не влезли
            while len(body.encode('utf-8')) < content_length:
                body += conn.recv(1024).decode('utf-8')

            print("Итоговый JSON получен:", body)


        # Проверяем, что это POST запрос
        if "POST /wake" in headers:
            try:
                data = json.loads(body)
                mac = data.get("mac")

                if mac:
                    send_wol(mac)
                    response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\":\"success\"}"
                else:
                    response = "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n{\"error\":\"Missing MAC\"}"
            except Exception as e:
                response = "HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n{\"error\":\"Invalid JSON\"}"
                print(e)
        else:
            response = "HTTP/1.1 404 Not Found\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"

        conn.send(response)
        conn.close()
    except Exception as e:
        print("Ошибка сервера:", e)
