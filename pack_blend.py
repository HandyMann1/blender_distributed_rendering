import bpy

if bpy.data.is_saved:
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_mainfile()
    print("All external data has been packed into the .blend file.")
else:
    print("Please save the file before packing.")
