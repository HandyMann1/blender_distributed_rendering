import asyncio
import websockets
import json


async def send_file(websocket, filename):
    # Открываем указанный файл для чтения в бинарном режиме
    with open(filename, 'rb') as file:
        # Читаем содержимое файла как байты
        file_content = file.read()
    # Создаём словарь с именем файла и его содержимым для отправки
    data_to_send = {"filename": filename, "content": list(file_content)}
    # Превращаем словарь в строку JSON и отправляем её через WebSocket
    await websocket.send(json.dumps(data_to_send))


async def connect_to_server():
    data = "ping"
    async with websockets.connect("ws://127.0.0.1:5000/ws") as websocket:
        while True:
            await asyncio.sleep(1)
            await websocket.send(data)
            # Ждем сообщение от сервера
            response = await websocket.recv()
            if response == "pong" or response == "server received":
                print(response)
                data = "ping"
            else:
                print("file received")
                file = await render_file(json.loads(response))
                data = file


async def render_file(file):
    return file


asyncio.get_event_loop().run_until_complete(connect_to_server())
