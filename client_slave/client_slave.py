import requests
import subprocess
import os

# URL сервера
LIST_OF_SERVER = ['http://localhost:5000']

# Директория для временного хранения файлов
TEMP_DIR = "D:\\abobus\\distributed_calc\\client_slave\\blender_distributed_rendering\\temp"

# Создаем директорию для временного хранения файлов, если она не существует
os.makedirs(TEMP_DIR, exist_ok=True)


def get_task():
    for server_url in LIST_OF_SERVER:
        response = requests.get(f'{server_url}/get_task')
        if response.status_code == 200:
            return response.json()
        else:
            print(server_url, "unavailable!")


def upload_rendered_frame(file_path: str, frame_number: int, blend_file_path: str):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'blend_file_path': blend_file_path}

        for server_url in LIST_OF_SERVER:
            response = requests.post(f'{server_url}/upload_frame/{frame_number}', files=files,
                                     data=data)
            if response.status_code == 200:
                break
            print(f"Response Code: {response.status_code}")
            print(f"Response Content: {response.text}")
    return response.status_code == 200


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
                print(f"working on task: {task_id}")

                for server_url in LIST_OF_SERVER:
                    response = requests.get(f'{server_url}/download_blend/{blend_file}')  # Скачиваем .blend файл
                    if response.status_code == 200:
                        blend_file_path = os.path.join(TEMP_DIR, blend_file)
                        with open(blend_file_path, 'wb') as f:
                            f.write(response.content)

                        render_frame(blend_file_path, frame_number)  # Рендерим

                        output_file = os.path.join(TEMP_DIR, f'frame_{frame_number:04d}.png')
                        base_filename = str(os.path.splitext(blend_file)[0])
                        if upload_rendered_frame(output_file, frame_number,
                                                 base_filename):  # Возвращаем отрендеренный кадр на сервер
                            print(f'Frame {frame_number} rendered and uploaded successfully.')
                        else:
                            print(f'Failed to upload frame {frame_number}.')

                        # os.remove(blend_file_path)  # Удаляем временные файлы
                        os.remove(output_file)
                        break
                    else:
                        print(f'{server_url} Failed to download blend file: {blend_file}')

            else:
                print('No tasks available.')


if __name__ == '__main__':
    main()
