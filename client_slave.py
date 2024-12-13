import os
import subprocess
import threading
import time
import requests

LIST_OF_SERVER = ['http://localhost:5000', 'http://localhost:5001', 'http://localhost:5002']

def send_heartbeat():
    while True:
        for server_url in LIST_OF_SERVER:
            try:
                response = requests.post(f'{server_url}/heartbeat')
                if response.status_code == 200:
                    print(f'Heartbeat from {server_url} sent successfully.')
                else:
                    print(f'Failed to send heartbeat from {server_url}.')
            except requests.RequestException as e:
                print(f'Heartbeat request from {server_url} failed: {e}')
        time.sleep(10)

heartbeat_thread = threading.Thread(target=send_heartbeat)
heartbeat_thread.daemon = True
heartbeat_thread.start()

TEMP_DIR = os.path.join(os.getcwd(), "temp")
try:
    os.makedirs(TEMP_DIR, exist_ok=True)
except OSError as e:
    print(f"Failed to create temp directory: {e}")

def get_task():
    for server_url in LIST_OF_SERVER:
        try:
            response = requests.get(f'{server_url}/get_task')
            if response.status_code == 200:
                print(f"Task received from {server_url}: {response.json()}")
                return response.json()
            else:
                print(f"{server_url} returned status code {response.status_code}. Trying next server...")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {server_url}: {e}")

    print("All servers failed to provide a task.")
    return None

def upload_rendered_frame(file_path: str, frame_number: int, blend_file_path: str):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'blend_file_path': blend_file_path}

            for server_url in LIST_OF_SERVER:
                try:
                    response = requests.post(f'{server_url}/upload_frame/{frame_number}', files=files, data=data)
                    if response.status_code == 200:
                        print(f"Uploaded frame {frame_number} successfully to {server_url}.")
                        return True
                    else:
                        print(f"{server_url} returned status code {response.status_code}. Trying next server...")
                except requests.exceptions.RequestException as e:
                    print(f"Error connecting to {server_url}: {e}")
    except IOError as e:
        print(f"Failed to open file {file_path}: {e}")

    print(f"Failed to upload frame {frame_number} after trying all servers.")
    return False

def render_frames(blend_file, start_frame, end_frame):
    command = [
        'blender',
        '-b', blend_file,
        '-o', os.path.join(TEMP_DIR, "frame_####"),
        '-F', 'PNG',
        '-s', str(start_frame),
        '-e', str(end_frame),
        '-a'
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Standard Output:", result.stdout.decode())
        print("Standard Error:", result.stderr.decode())
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while rendering: {e}")
    except FileNotFoundError as e:
        print(f"Blender executable not found: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    while True:
        try:
            task = get_task()
            if task:
                required_keys = ['blend_file', 'frame_numbers', 'task_id']
                if all(key in task for key in required_keys):
                    blend_file = task['blend_file']
                    frame_numbers = task['frame_numbers']
                    task_id = task['task_id']
                    print(f"Working on task: {task_id}")

                    for server_url in LIST_OF_SERVER:
                        try:
                            response = requests.get(f'{server_url}/download_blend/{blend_file}')
                            if response.status_code == 200:
                                blend_file_path = os.path.join(TEMP_DIR, blend_file)
                                with open(blend_file_path, 'wb') as f:
                                    f.write(response.content)

                                start_frame = min(frame_numbers)
                                end_frame = max(frame_numbers)

                                render_frames(blend_file_path, start_frame, end_frame)

                                for frame_number in range(start_frame, end_frame + 1):
                                    output_file = os.path.join(TEMP_DIR, f'frame_{frame_number:04d}.png')
                                    base_filename = str(os.path.splitext(blend_file)[0])
                                    if upload_rendered_frame(output_file, frame_number, base_filename):
                                        print(f'Frame {frame_number} rendered and uploaded successfully.')
                                    else:
                                        print(f'Failed to upload frame {frame_number}.')
                                break
                            else:
                                print(
                                    f'{server_url} failed to download blend file: {blend_file}. Status code: {response.status_code}')
                        except requests.exceptions.RequestException as e:
                            print(f"Error connecting to {server_url}: {e}")

                else:
                    print('No tasks available.')
            else:
                print("All servers failed to provide a task.")
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")

if __name__ == '__main__':
    main()