import asyncio
import json

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket
from fastapi.responses import FileResponse
import uvicorn
import os

app = FastAPI()

# Папка для сохранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

filepath = None


async def send_file(websocket, filename):
    # Открываем указанный файл для чтения в бинарном режиме
    with open(filename, 'rb') as file:
        # Читаем содержимое файла как байты
        file_content = file.read()
    # Создаём словарь с именем файла и его содержимым для отправки
    data_to_send = {"filename": filename, "content": list(file_content)}
    # Превращаем словарь в строку JSON и отправляем её через WebSocket
    await websocket.send(json.dumps(data_to_send))


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global filepath
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    # Сохраняем файл
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    # Тут должен быть код, который разбивает файл на несколько файлов и рассылает его клиентам-обработчикам

    asyncio.sleep(2)
    filepath = None

    # Отправляем файл обратно клиенту
    return FileResponse(filepath, media_type='application/octet-stream', filename=file.filename)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    print(websocket)
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        if filepath is not None:
            await send_file(websocket, filepath)


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
