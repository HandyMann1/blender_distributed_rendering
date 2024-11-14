from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket
from fastapi.responses import FileResponse
import uvicorn
import os

app = FastAPI()

# Папка для сохранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    # Сохраняем файл
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    #Тут должен быть код который разбивает файл на несколько файлов и рассылает его клиентам-обработчикам

    # Отправляем файл обратно клиенту
    return FileResponse(filepath, media_type='application/octet-stream', filename=file.filename)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    print(websocket)
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(data)
        await websocket.send_text(f"Message text was: {data}")


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
