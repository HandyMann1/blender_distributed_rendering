import math

import requests
from launch_subcommand import pack_blend_file
import tkinter as tk
from tkinter import filedialog, messagebox


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
            messagebox.showinfo("Success", "File uploaded successfully!")
        else:
            print(f"Failed to upload file. Status code: {response.status_code}")
            print("Response:", response.text)
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


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Blend File Uploader")

    server_url = 'http://localhost:5000/upload'

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
    end_frame_spinbox = tk.Spinbox(frame_selection_frame, from_=1, to=math.inf, width=5,textvariable=default_end_frame)
    end_frame_spinbox.pack(side=tk.LEFT)

    frame_selection_frame.pack()

    upload_button = tk.Button(root, text="Upload Blend File", command=on_upload)
    upload_button.pack(pady=20)

    root.mainloop()
