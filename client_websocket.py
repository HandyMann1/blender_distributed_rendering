import asyncio
import websockets
import json

async def send_file(websocket, filename, save_as):
    # Открываем указанный файл для чтения в бинарном режиме
    with open(filename, 'rb') as file:
        # Читаем содержимое файла как байты
        file_content = file.read()
    # Создаём словарь с именем файла и его содержимым для отправки
    data_to_send = {"filename": save_as, "content": list(file_content)}
    # Превращаем словарь в строку JSON и отправляем её через WebSocket
    await websocket.send(json.dumps(data_to_send))

async def connect_to_server():
    async with websockets.connect("ws://127.0.0.1:5000/ws") as websocket:
        while True:
            # Ждем сообщение от сервера
            response = await websocket.recv()
            # Как получили обрабатываем изображение
            result_file = await render_file(response)
            # Отправляем файл, возможно надо будет отправить как то по другому (преобразовать перед отправкой)
            await websocket.send(result_file)


async def render_file(file):
    pass


asyncio.get_event_loop().run_until_complete(connect_to_server())
