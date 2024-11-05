from flask import Flask, request, redirect, url_for
import os

app = Flask(__name__)

# Define the uploads directory
UPLOAD_FOLDER = 'uploads'

# Ensure the uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def home():
    return redirect(url_for('upload_file'))


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return "No file part", 400

        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400

        # Save the uploaded .blend file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        return f"File '{file.filename}' uploaded successfully!", 200

    except Exception as e:
        return f"Internal Server Error: {str(e)}", 500


if __name__ == '__main__':
    app.run(port=5000)
