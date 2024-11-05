import requests
from launch_subcommand import pack_blend_file


def send_blend_file(server_url, blend_file_path, start_frame, end_frame):
    files = {'file': open(blend_file_path, 'rb')}
    data = {
        'start_frame': start_frame,
        'end_frame': end_frame
    }

    try:
        response = requests.post(server_url, files=files, data=data)

        if response.status_code == 200:
            print("File uploaded successfully!")
            print("Server response:", response.text)
        else:
            print(f"Failed to upload file. Status code: {response.status_code}")
            print("Response:", response.text)

    except Exception as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    server_url = 'http://localhost:5000/upload'
    blend_file_path = "D:\python_prjs\distributed\client_master\materials\zweihanderLowPolierRender.blend"
    pack_blend_file(blend_file_path)
    start_frame = 1
    end_frame = 25


    send_blend_file(server_url, blend_file_path, start_frame, end_frame)
