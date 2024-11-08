from flask import Flask, request, send_file, jsonify
import os

app = Flask(__name__)

# Папка для сохранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Сохраняем файл
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Отправляем файл обратно клиенту
    return send_file(filepath, as_attachment=True)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
