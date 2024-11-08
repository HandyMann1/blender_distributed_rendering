import requests


def upload_file(file_path):
    url = 'http://127.0.0.1:5000/upload'
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        # Сохраняем полученный файл
        with open('received_' + file_path.split('/')[-1], 'wb') as out_file:
            out_file.write(response.content)
        print(f"Файл '{file_path}' успешно загружен и получен обратно.")
    else:
        print(response.json())


if __name__ == '__main__':
    upload_file('file.txt')
