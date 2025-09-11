import bpy
import os
import sys
import csv
import re

def read_csv_and_set_frame_range(csv_file_path, shot_name):
    # Baca CSV dan cari baris dengan nama shot yang cocok
    with open(csv_file_path, mode='r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            combined_name = f"{row[0]}_{row[1]}_{row[2]}"  # Gabungkan nilai dari kolom 0, 1, dan 2 dengan underscore
            if combined_name == shot_name:  # Cocokkan dengan nama shot di kolom pertama
                start_frame = int(row[3])
                end_frame = int(row[4])
                print(f"Shot '{shot_name}' ditemukan di CSV dengan start_frame: {start_frame} dan end_frame: {end_frame}")

                # Set frame range di Blender
                bpy.context.scene.frame_start = start_frame
                bpy.context.scene.frame_end = end_frame
                return True
        print(f"Shot '{shot_name}' tidak ditemukan di CSV.")
        return False

def link_and_save(master_file, animation_file, lighting_file, csv_file):
    # Open the master file
    bpy.ops.wm.open_mainfile(filepath=master_file)
    print(master_file)

    # Link the animation file
    with bpy.data.libraries.load(animation_file, link=True) as (data_from, data_to):
        # Check collections in the animation file
        collections_to_link = ['character', '3dprop', 'vehicle']  # Expected collections
        for collection_name in collections_to_link:
            if collection_name in data_from.collections:
                print(f"Collection '{collection_name}' found in animation file, linking...")
                data_to.collections.append(collection_name)
            else:
                available_collections = [col for col in data_from.collections]
                print(f"Collection '{collection_name}' not found in animation file. Available collections: {available_collections}")
    
    # Append 'camera' collection
    with bpy.data.libraries.load(animation_file, link=False) as (data_from, data_to):
        collections_to_append = ['camera']  # Collection to append
        for collection_name in collections_to_append:
            if collection_name in data_from.collections:
                print(f"Collection '{collection_name}' found in animation file, appending...")
                data_to.collections.append(collection_name)
            else:
                available_collections = [col for col in data_from.collections]
                print(f"Collection '{collection_name}' not found in animation file. Available collections: {available_collections}")

    # Now, you need to explicitly add the appended 'camera' collection to the scene.
    # for collection_name in collections_to_append:
    #     if collection_name in bpy.data.collections:
    #         collection = bpy.data.collections[collection_name]
    #         if collection not in bpy.context.scene.collection.children:
    #             bpy.context.scene.collection.children.link(collection)
    #             print(f"Appended '{collection_name}' collection added to the scene.")
    #         else:
    #             print(f"'{collection_name}' collection already exists in the scene.")
   
    # # Add collections to the scene
    # turbine_containers = bpy.data.collections.get('TURBINE_CONTAINERS')
    #
    # if turbine_containers is None:
    #     print("Collection 'TURBINE_CONTAINERS' not found. Creating new collection.")
    #     turbine_containers = bpy.data.collections.new('TURBINE_CONTAINERS')
    #     bpy.context.scene.collection.children.link(turbine_containers)
    #
    # for collection in bpy.data.collections:
    #     if collection.name in ['character', '3dprop', 'vehicle']:
    #         turbine_containers.children.link(collection)
    #         print(f"Added collection '{collection.name}' to 'TURBINE_CONTAINERS'.")
    #     elif collection.name == 'camera':
    #         bpy.context.scene.collection.children.link(collection)

    # # Activate camera overscan if not already active
    scene = bpy.data.scenes.get("Scene")
    # if scene:
    #     if not scene.camera_overscan.RO_Activate:
    #         print("Camera overscan is not active, activating it.")
    #         scene.camera_overscan.RO_Activate = True
    #     else:
    #         print("Camera overscan is already active.")
    #
    # Set the active camera from the 'camera' collection
    camera_collection = bpy.data.collections.get('camera')
    if camera_collection:
        for obj in camera_collection.objects:
            if obj.type == 'CAMERA':
                bpy.context.view_layer.objects.active = obj  # Set the camera as active
                scene.camera = obj  # Set the active camera for the scene
                print(f"Set '{obj.name}' as the active camera.")
                break

    active_camera = bpy.context.scene.camera
    if active_camera:
        # Set Depth of Field menjadi False
        active_camera.data.dof.use_dof = False
        
        # Set clip_end menjadi 1000
        active_camera.data.clip_end = 1000
        
        print(f"Active camera '{active_camera.name}' updated: Depth of Field = {active_camera.data.dof.use_dof}, Clip End = {active_camera.data.clip_end}")
    else:
        print("No active camera found.")
        
    # Generate the shot name from the animation file (e.g., epXXX_seqXXXX_shXXXX)
    shot_name_match = re.search(r'(ep\d{3}_seq\d{4}_sh\d{4})', animation_file)
    if shot_name_match:
        shot_name = shot_name_match.group(1)
        print(shot_name)
    else:
        print("Shot name not found in animation file name.")
        return

    # Baca file CSV dan set frame range berdasarkan shot_name
    if csv_file:
        if read_csv_and_set_frame_range(csv_file, shot_name):
            print(f"Frame range untuk '{shot_name}' berhasil diatur berdasarkan CSV.")
        else:
            print(f"Frame range untuk shot '{shot_name}' tidak ditemukan di CSV.")

    # Save as the lighting file
    bpy.ops.wm.save_as_mainfile(filepath=lighting_file)
    print(f"File saved as: {lighting_file}")
        
    # variable scene untuk frame
    scene = bpy.data.scenes.get("Scene")
    if scene:
        # Hitung frame_step_value sebagai (frame_end - frame_start) / 2
        frame_step_value = (scene.frame_end - scene.frame_start) / 2
        
        # Periksa apakah frame_step_value adalah float/desimal
        if frame_step_value % 1 != 0:
            frame_step_value -= 0.5
        
        # Set frame_step dengan nilai yang telah dikonversi ke integer
        scene.frame_step = int(frame_step_value)
        print(f"Frame step set to: {scene.frame_step}")
    else:
        print("Scene 'Scene' not found.")

    # matiin overscan camera
    # scene.camera_overscan.RO_Activate = False

    # Generate Linux paths before saving
    bpy.ops.path.rel()  # Memanggil operator untuk set Linux path

    # nyalain lagi overscan camera
    # scene.camera_overscan.RO_Activate = True

    # Pastikan semua path menjadi relatif
    bpy.ops.file.make_paths_relative()

    # Simpan lagi setelah path di-update
    bpy.ops.wm.save_mainfile()

    # Quit Blender
    bpy.ops.wm.quit_blender()

if __name__ == "__main__":
    master_file = sys.argv[sys.argv.index('--') + 1]
    animation_file = sys.argv[sys.argv.index('--') + 2]
    lighting_file = sys.argv[sys.argv.index('--') + 3]
    csv_file = sys.argv[sys.argv.index('--') + 4]  # Path CSV dari user

    link_and_save(master_file, animation_file, lighting_file, csv_file)
