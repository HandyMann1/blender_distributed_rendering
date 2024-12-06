import threading

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, Query, Form
from fastapi.responses import FileResponse
import uvicorn
import os

app = FastAPI()

master_clients = []

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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    master_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        print("WebSocket connection closed:", e)
        master_clients.remove(websocket)


@app.get("/download_blend/{filename}")
async def download_blend(filename: str):
    filepath = os.path.join(UPLOAD_FOLDER, filename.split(sep=".")[0], filename)
    print(filepath)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/download_rendered/{filename}")
async def download_rendered(filename: str):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    print(f"Looking for file at: {filepath}")
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
    for client in master_clients:
        await client.send_text(f"New frame uploaded: {file.filename} for task {task_id}")

    return {"info": f"File '{file.filename}' uploaded successfully for task '{task_id}'"}


@app.get("/get_rendered_frames")
async def get_rendered_frames(file_name: str = None):
    rendered_frames = []
    if file_name:
        file_dir = file_name.split('.')[0]

        search_directory = os.path.join(UPLOAD_FOLDER, file_dir)
        print(search_directory)
    else:
        search_directory = UPLOAD_FOLDER
    if not os.path.exists(search_directory):
        raise HTTPException(status_code=404, detail=f"Directory not found: {search_directory}")

    for root, dirs, files in os.walk(search_directory):
        for file in files:
            if file.endswith(".png"):
                rendered_frames.append(os.path.join(root, file))
                print(os.path.join(root, file))
    return {"rendered_frames": rendered_frames}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5000)
