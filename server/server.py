import os
import threading
import time

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, Query, Form
from fastapi.responses import FileResponse

app = FastAPI()

master_clients = []
tasks = []
active_tasks = []
task_num = 1
task_num_lock = threading.Lock()
heartbeat_timeout = 30

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

heartbeat_tracker = {}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), start_frame: int = Query(...), end_frame: int = Query(...)):
    global task_num

    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    # Save file
    base_filename = os.path.splitext(file.filename)[0]
    directory_path = os.path.join(UPLOAD_FOLDER, base_filename)
    filepath = os.path.join(directory_path, file.filename)
    os.makedirs(directory_path, exist_ok=True)

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    for frame_start in range(start_frame, end_frame + 1, 5):
        frame_end = min(frame_start + 4, end_frame)
        with task_num_lock:
            tasks.append({
                'blend_file': file.filename,
                'frame_numbers': list(range(frame_start, frame_end + 1)),
                'task_id': f'{task_num}'
            })
            task_num += 1

    return {"info": "File uploaded successfully", "tasks": tasks}


@app.get("/get_task")
async def get_task():
    if len(tasks) >= 1:
        task = tasks.pop(0)
        active_tasks.append(task)
        heartbeat_tracker[task['task_id']] = time.time()
        return task
    raise HTTPException(status_code=204)


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
    if os.path.exists(filepath):
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/download_rendered/{filename}")
async def download_rendered(filename: str):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
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

    for task in active_tasks:
        if task['task_id'] == task_id:
            active_tasks.remove(task)
            break

    for client in master_clients:
        await client.send_text(f"New frame uploaded: {file.filename} for task {task_id}")

    return {"info": f"File '{file.filename}' uploaded successfully for task '{task_id}'"}


@app.get("/get_rendered_frames")
async def get_rendered_frames(file_name: str = None):
    rendered_frames = []

    if file_name:
        file_dir = file_name.split('.')[0]
        search_directory = os.path.join(UPLOAD_FOLDER, file_dir)
    else:
        search_directory = UPLOAD_FOLDER

    if not os.path.exists(search_directory):
        raise HTTPException(status_code=404, detail=f"Directory not found: {search_directory}")

    for root, dirs, files in os.walk(search_directory):
        for file in files:
            if file.endswith(".png"):
                rendered_frames.append(os.path.join(root, file))

    return {"rendered_frames": rendered_frames}


@app.post("/heartbeat/{task_id}")
async def heartbeat(task_id: str):
    if task_id in heartbeat_tracker:
        heartbeat_tracker[task_id] = time.time()
        return {"status": "alive"}

    raise HTTPException(status_code=404, detail="Task ID not found")


def cleanup_tasks():
    while True:
        time.sleep(heartbeat_timeout)
        current_time = time.time()

        for task_id in list(heartbeat_tracker.keys()):
            if current_time - heartbeat_tracker[task_id] > heartbeat_timeout:
                for task in active_tasks:
                    if task['task_id'] == task_id:
                        active_tasks.remove(task)
                        tasks.append(task)
                        del heartbeat_tracker[task_id]
                        break


@app.post("/heartbeat")
async def heartbeat():
    return {"status": "alive"}


if __name__ == '__main__':
    threading.Thread(target=cleanup_tasks, daemon=True).start()
    uvicorn.run(app, host='127.0.0.1', port=5001)
