import requests
import subprocess
import os

# URL сервера
SERVER_URL = 'http://our/server'

# Директория для временного хранения файлов
TEMP_DIR = 'temp'

# Создаем директорию для временного хранения файлов, если она не существует
os.makedirs(TEMP_DIR, exist_ok=True)

def get_task():
    response = requests.get(f'{SERVER_URL}/get_task')
    if response.status_code == 200:
        return response.json()
    else:
        return None

def upload_rendered_frame(file_path, task_id):
    files = {'file': open(file_path, 'rb')}
    response = requests.post(f'{SERVER_URL}/upload_frame/{task_id}', files=files)
    return response.status_code == 200

def render_frame(blend_file, frame_number, output_file):
    command = [
        'blender',
        '-b', blend_file,
        '-o', output_file,
        '-f', str(frame_number)
    ]
    subprocess.run(command, check=True)

def main():
    while True:
        task = get_task()
        if task:
            blend_file = task['blend_file']
            frame_number = task['frame_number']
            task_id = task['task_id']

            response = requests.get(f'{SERVER_URL}/download_blend/{blend_file}')            # Скачиваем .blend файл
            if response.status_code == 200:
                blend_file_path = os.path.join(TEMP_DIR, blend_file)
                with open(blend_file_path, 'wb') as f:
                    f.write(response.content)

                output_file = os.path.join(TEMP_DIR, f'frame_{frame_number}.png')    # Рендер
                render_frame(blend_file_path, frame_number, output_file)

                if upload_rendered_frame(output_file, task_id):                # Возвращаем отрендеренный кадр на сервер
                    print(f'Frame {frame_number} rendered and uploaded successfully.')
                else:
                    print(f'Failed to upload frame {frame_number}.')

                os.remove(blend_file_path)                # Удаляем временные файлы
                os.remove(output_file)
            else:
                print(f'Failed to download blend file: {blend_file}')
        else:
            print('No tasks available.')

if __name__ == '__main__':
    main()