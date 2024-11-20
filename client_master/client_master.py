import math
import os
import threading

import requests
from launch_subcommand import pack_blend_file
import tkinter as tk
from tkinter import filedialog, messagebox
import websockets
import asyncio

current_prj = {'file_name': None, 'start_frame': None,
               'end_frame': None}


def send_blend_file(server_url, blend_file_path: str, start_frame, end_frame):
    global current_prj
    files = {'file': open(blend_file_path, 'rb')}
    data = {
        'start_frame': start_frame,
        'end_frame': end_frame
    }
    current_prj = {'file_name': blend_file_path.split("/")[-1], 'start_frame': data["start_frame"],
                   'end_frame': data["end_frame"]}
    print(current_prj)
    try:
        response = requests.post(server_url + "/upload", files=files, params=data)

        if response.status_code == 200:
            print("File uploaded successfully!")
            messagebox.showinfo("Success", "File uploaded successfully!")
        else:
            print(f"Failed to upload file. Status code: {response.status_code}")
            messagebox.showerror("Error", f"Failed to upload file. Status code: {response.status_code}")

    except Exception as e:
        print("An error occurred:", e)
        messagebox.showerror("Error", f"An error occurred: {e}")


def browse_files():
    filename = filedialog.askopenfilename(
        title="Select a .blend file",
        filetypes=(("Blend files", "*.blend"), ("All files", "*.*"))
    )
    blend_file_path_entry.delete(0, tk.END)
    blend_file_path_entry.insert(0, filename)


def download_rendered_frames():
    if current_prj['file_name'] is not None:
        response = requests.get(f'{server_url}/get_rendered_frames', params={'file_name': current_prj['file_name']})
        if response.status_code == 200:
            frames = response.json().get("rendered_frames", [])
            print(f"Found {len(frames)} rendered frames.")

            for frame in frames:
                file_name = os.path.basename(frame)
                base_directory = str(current_prj["file_name"]).split('.')[0]  # Get project name without .blend
                os.makedirs(base_directory, exist_ok=True)

                file_path = os.path.join(base_directory, file_name)

                print(f"Downloading frame: {file_name} from {file_path}")

                frame_response = requests.get(f'{server_url}/download_rendered/{file_path}')
                if frame_response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(frame_response.content)
                    print(f"Downloaded {file_name} successfully.")
                else:
                    print(f"Failed to download {file_name}. Status code: {frame_response.status_code}")
        else:
            print(f"Failed to retrieve rendered frames. Status code: {response.status_code}")
    else:
        messagebox.showwarning("Warning", "Please, upload your .blend file")

def on_upload():
    blend_file_path = blend_file_path_entry.get()
    if not blend_file_path:
        messagebox.showwarning("Warning", "Please enter a valid .blend file path.")
        return

    try:
        start_frame = int(start_frame_spinbox.get())
        end_frame = int(end_frame_spinbox.get())

        if start_frame > end_frame:
            messagebox.showwarning("Warning", "Start frame must be less than or equal to end frame.")
            return

        pack_blend_file(blend_file_path)
        send_blend_file(server_url, blend_file_path, start_frame, end_frame)

    except ValueError:
        messagebox.showwarning("Warning", "Please enter valid frame numbers.")


async def listen_for_updates():
    async with websockets.connect('ws://localhost:5000/ws') as websocket:
        while True:
            message = await websocket.recv()
            print("Received message:", message)


def start_websocket_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen_for_updates())


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Blend File Uploader")

    server_url = 'http://localhost:5000'

    # Label for file path entry
    blend_file_path_lbl = tk.Label(root, text="Enter .blend file path:")
    blend_file_path_lbl.pack(pady=10)

    # Entry for file path
    blend_file_path_entry = tk.Entry(root, width=50)
    blend_file_path_entry.pack(pady=5)

    # Button to browse files
    browse_button = tk.Button(root, text="Browse Files", command=browse_files)
    browse_button.pack(pady=5)

    frame_selection_frame = tk.Frame(root)

    frame_selection_lbl = tk.Label(frame_selection_frame, text="Select Start and End Frames:")
    frame_selection_lbl.pack(pady=10)

    start_frame_spinbox = tk.Spinbox(frame_selection_frame, from_=1, to=math.inf, width=5)
    start_frame_spinbox.pack(side=tk.LEFT, padx=(20, 10))

    default_end_frame = tk.IntVar(frame_selection_frame)
    default_end_frame.set(25)
    end_frame_spinbox = tk.Spinbox(frame_selection_frame, from_=1, to=math.inf, width=5, textvariable=default_end_frame)
    end_frame_spinbox.pack(side=tk.LEFT)

    frame_selection_frame.pack()

    upload_button = tk.Button(root, text="Upload Blend File", command=on_upload)
    upload_button.pack(pady=10)
    download_frames_button = tk.Button(root, text="Download Rendered Frames", command=download_rendered_frames)
    download_frames_button.pack(pady=5)

    websocket_thread = threading.Thread(target=start_websocket_listener)
    websocket_thread.daemon = True
    websocket_thread.start()

    root.mainloop()
