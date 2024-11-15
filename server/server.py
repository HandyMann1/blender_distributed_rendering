import threading

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, Query, Form
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import os

app = FastAPI()

tasks = []
task_num = 1
task_num_lock = threading.Lock()

# Папка для сохранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), start_frame: int = Query(...), end_frame: int = Query(...)):
    global task_num

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    # Сохраняем файл
    base_filename = os.path.splitext(file.filename)[0]
    directory_path = os.path.join(UPLOAD_FOLDER, base_filename)

    filepath = os.path.join(directory_path, file.filename)
    os.makedirs(directory_path, exist_ok=True)
    print(f"Saving file to: {filepath}")

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())
    for frame_number in range(start_frame, end_frame + 1):
        with task_num_lock:
            tasks.append({
                'blend_file': file.filename,
                'frame_number': frame_number,
                'task_id': f'{task_num}'
            })
            task_num += 1

    return {"info": "File uploaded successfully", "tasks": tasks}


@app.get("/get_task")
async def get_task():
    if len(tasks) >= 1:
        return tasks.pop(0)
    return HTTPException(status_code=204)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    print(websocket)
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(data)
        await websocket.send_text(f"Message text was: {data}")


@app.get("/download_blend/{filename}")
async def download_blend(filename: str):
    filepath = os.path.join(UPLOAD_FOLDER, filename.split(sep=".")[0], filename)
    print(filepath)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="File not found")


@app.post("/upload_frame/{task_id}")
async def upload_frame(task_id: str, blend_file_path: str = Form(...), file: UploadFile = File(...)):
    directory_path = os.path.join(UPLOAD_FOLDER, blend_file_path)
    os.makedirs(directory_path, exist_ok=True)

    file_location = os.path.join(directory_path, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return {"info": f"File '{file.filename}' uploaded successfully for task '{task_id}'"}


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=5000)
