import requests
import subprocess
import os

# URL of the servers
LIST_OF_SERVER = ['http://localhost:5000', 'http://localhost:5001', 'http://localhost:5002']

# Directory for temporary file storage
TEMP_DIR = os.path.join(os.getcwd(),"temp")

os.makedirs(TEMP_DIR, exist_ok=True)


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

    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'blend_file_path': blend_file_path}

        for server_url in LIST_OF_SERVER:
            try:
                response = requests.post(f'{server_url}/upload_frame/{frame_number}', files=files, data=data)
                if response.status_code == 200:
                    print(f"Uploaded frame {frame_number} successfully to {server_url}.")
                    return True  # Successful upload
                else:
                    print(f"{server_url} returned status code {response.status_code}. Trying next server...")
            except requests.exceptions.RequestException as e:
                print(f"Error connecting to {server_url}: {e}")

    print(f"Failed to upload frame {frame_number} after trying all servers.")
    return False

def render_frame(blend_file, frame_number):
    command = [
        'blender',
        '-b', blend_file,
        '-o', os.path.join(TEMP_DIR, "frame_####"), "-F", "PNG",
        '-f', str(frame_number)
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Standard Output:", result.stdout.decode())
        print("Standard Error:", result.stderr.decode())
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while rendering: {e}")


def main():
    while True:
        task = get_task()
        if task:
            required_keys = ['blend_file', 'frame_number', 'task_id']
            if all(key in task for key in required_keys):
                blend_file = task['blend_file']
                frame_number = task['frame_number']
                task_id = task['task_id']
                print(f"Working on task: {task_id}")

                for server_url in LIST_OF_SERVER:
                    try:
                        response = requests.get(f'{server_url}/download_blend/{blend_file}')
                        if response.status_code == 200:
                            blend_file_path = os.path.join(TEMP_DIR, blend_file)
                            with open(blend_file_path, 'wb') as f:
                                f.write(response.content)

                            render_frame(blend_file_path, frame_number)

                            output_file = os.path.join(TEMP_DIR, f'frame_{frame_number:04d}.png')
                            base_filename = str(os.path.splitext(blend_file)[0])
                            if upload_rendered_frame(output_file, frame_number, base_filename):
                                print(f'Frame {frame_number} rendered and uploaded successfully.')
                            else:
                                print(f'Failed to upload frame {frame_number}.')

                            # os.remove(output_file)
                            break
                        else:
                            print(f'{server_url} failed to download blend file: {blend_file}')
                    except requests.exceptions.RequestException as e:
                        print(f"Error connecting to {server_url}: {e}")

            else:
                print('No tasks available.')
        else:
            print("All servers failed to provide a task.")


if __name__ == '__main__':
    main()
