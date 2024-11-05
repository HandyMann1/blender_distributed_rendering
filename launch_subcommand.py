import subprocess


def pack_blend_file(blend_file_path):
    BLENDER_PATH = "D:\\Steam\\steamapps\\common\\Blender\\blender.exe"
    blend_file_path = blend_file_path
    script_path = "D:\\python_prjs\\distributed\\client_master\\pack_blend.py"  # path to pack_blend.py

    command = [BLENDER_PATH, "--background", blend_file_path, "--python", script_path]

    # try:
    #     result = subprocess.run(command, check=True, capture_output=True, text=True)
    #     print("Blender output:", result.stdout)
    #     print("Blender errors:", result.stderr)
    # except subprocess.CalledProcessError as e:
    #     print(f"An error occurred: {e}")
    #     print("Output:", e.output)
    #     print("Return code:", e.returncode) ###logging nado sdelat po normalnomu
