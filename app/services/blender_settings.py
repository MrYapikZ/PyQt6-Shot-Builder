from textwrap import dedent
from string import Template


class BlenderSettings:
    def __init__(self, blender_file: str):
        self.blender_file = blender_file

    def generate_script(self, file_path:str, animation_file: str, collection_list: list, camera_collection: str,
                        start_frame: int, end_frame: int, output_path: str,
                        beauty_base_path: str, alpha_base_path: str) -> str:
        tpl = Template(dedent("""
            import bpy
            
            # Open master file
            bpy.ops.wm.open_mainfile(FILEPATH)
            
            
            # Define file paths and parameters
            
            def link_animation():
                # Link the animation file
                with bpy.data.libraries.load(ANIMATION_FILE, link=True) as (data_from, data_to):
                    collections_to_link = [COLLECTION_LIST]
                    for collection_name in collections_to_link:
                        if collection_name in data_from.collections:
                            print(f"Collection '{collection_name}' found in animation file, linking...")
                            data_to.collections.append(collection_name)
                        else:
                            available_collections = [col for col in data_from.collections]
                            print(
                                f"Collection '{collection_name}' not found in animation file. Available collections: {available_collections}")
            
            
            def append_camera():
                # Append 'camera' collection
                scene_data = bpy.data.scenes.get("Scene")
                with bpy.data.libraries.load(ANIMATION_FILE, link=False) as (data_from, data_to):
                    collections_to_append = [CAMERA_COLLECTION]
                    for collection_name in collections_to_append:
                        if collection_name in data_from.collections:
                            print(f"Collection '{collection_name}' found in animation file, appending...")
                            data_to.collections.append(collection_name)
                        else:
                            available_collections = [col for col in data_from.collections]
                            print(
                                f"Collection '{collection_name}' not found in animation file. Available collections: {available_collections}")
            
                # Set the active camera from the appended collection
                camera_collection = bpy.data.collections.get(CAMERA_COLLECTION)
                if camera_collection:
                    for obj in camera_collection.objects:
                        if obj.type == "CAMERA":
                            bpy.context.view_laer.objects.active = obj
                            scene_data.camera = obj
                            print(f"Active camera set to: {obj.name}")
                            break
            
                # Update camera settings
                active_camera = bpy.context.scene.camera
                if active_camera:
                    active_camera.data.dof.use_dof = False
                    active_camera.data.clip_end = 1000
                    print(f"Camera '{active_camera.name}' settings updated: DOF disabled, clip_end set to 1000")
                else:
                    print("No active camera found in the scene.")
            
            
            def set_duration():
                # Set the frame range based on the scene name
                scene_data = bpy.data.scenes.get("Scene")
                scene = bpy.context.scene
                scene.frame_start = START_FRAME
                scene.frame_end = END_FRAME
                print(f"Frame range set to: {START_FRAME} - {END_FRAME}")
            
                # Calculate and set frame step
                if scene_data:
                    frame_step_value = (scene_data.frame_end - scene_data.frame_start) / 2
            
                    if frame_step_value % 1 != 0:
                        frame_step_value -= 0.5
            
                    scene_data.frame_step = int(frame_step_value)
                    print(f"Frame step set to: {scene_data.frame_step}")
                else:
                    print("Scene 'Scene' not found.")
            
            
            def set_relative():
                # Make all file paths relative
                bpy.ops.path.rel()
                bpy.ops.file.make_paths_relative()
            
            
            def beauty_node():
                # Node Render Layer
                bpy.data.scenes["Scene"].node_tree.nodes.new("CompositorNodeRLayers").name = "beauty_layer"
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].label = "beauty_layer"
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].layer = "beauty"
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].location = (-600, 300)
            
                # Node Denoise
                bpy.data.scenes["Scene"].node_tree.nodes.new("CompositorNodeDenoise").name = "beauty_denoise"
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].label = "beauty_denoise"
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].location = (-350, 300)
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].quality = "HIGH"
            
                # Node Output File
                bpy.data.scenes["Scene"].node_tree.nodes.new("CompositorNodeOutputFile").name = "beauty_output"
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].label = "beauty_output"
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].location = (100, 300)
            
                # Slot file output untuk beauty pass
                bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].file_slots.clear()
                for p in [
                    "Image", "Alpha", "Depth", "Mist", "Emit", "Shadow", "AO", "Transparent",
                    "CryptoObject00", "CryptoObject01", "CryptoObject02",
                    "CryptoAsset00", "CryptoAsset01", "CryptoAsset02",
                    "CryptoMaterial00", "CryptoMaterial01", "CryptoMaterial02"
                ]:
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].file_slots.new(p)
            
                # Base path output file (contoh path, sesuai generator)
                bpy.data.scenes["Scene"].node_tree.nodes[
                    "beauty_output"].base_path = BEAUTY_BASE_PATH
                for slot in bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].file_slots:
                    slot.path = BEAUTY_BASE_PATH
            
                # Sambungan antar socket
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].outputs["Image"],
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].inputs["Image"]
                )
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].outputs["Denoising Normal"],
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].inputs["Normal"]
                )
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].outputs["Denoising Albedo"],
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].inputs["Albedo"]
                )
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].outputs["Image"],
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].inputs["Image"]
                )
            
                # Loop sambungan tambahan semua pass (selain Image)
                for p in [
                    "Alpha", "Depth", "Mist", "Emit", "Shadow", "AO", "Transparent",
                    "CryptoObject00", "CryptoObject01", "CryptoObject02",
                    "CryptoAsset00", "CryptoAsset01", "CryptoAsset02",
                    "CryptoMaterial00", "CryptoMaterial01", "CryptoMaterial02"
                ]:
                    bpy.data.scenes["Scene"].node_tree.links.new(
                        bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].outputs[p],
                        bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].inputs[p]
                    )
            
            
            def alpha_char_node():
                # Node Render Layer
                bpy.data.scenes["Scene"].node_tree.nodes.new("CompositorNodeRLayers").name = "alpha_chr_layer"
                bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_layer"].label = "alpha_chr_layer"
                bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_layer"].layer = "alpha_char"
                bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_layer"].location = (-600, -120)
            
                # Node Output File
                bpy.data.scenes["Scene"].node_tree.nodes.new("CompositorNodeOutputFile").name = "alpha_chr_output"
                bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].label = "alpha_chr_output"
                bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].location = (100, -120)
            
                # Slot file output untuk alpha pass
                bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].file_slots.clear()
                for p in ["Image", "Alpha"]:
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].file_slots.new(p)
            
                # Base path output file (contoh path, sesuai generator)
                bpy.data.scenes["Scene"].node_tree.nodes[
                    "alpha_chr_output"].base_path = ALPHA_BASE_PATH
                for slot in bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].file_slots:
                    slot.path = ALPHA_BASE_PATH
            
                # Sambungan antar socket
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_layer"].outputs["Image"],
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].inputs["Image"]
                )
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_layer"].outputs["Alpha"],
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].inputs["Alpha"]
                )
            
            
            # Save the modified Blender file
            bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
            print(f"File saved as: {OUTPUT_PATH}")
            
            # Quit Blender
            bpy.ops.wm.quit_blender()
        """))

        script = tpl.substitute(
            FILEPATH=file_path,
            ANIMATION_FILE=animation_file,
            COLLECTION_LIST=collection_list,
            CAMERA_COLLECTION=camera_collection,
            START_FRAME=start_frame,
            END_FRAME=end_frame,
            OUTPUT_PATH=output_path,
            BEAUTY_BASE_PATH=beauty_base_path,
            ALPHA_BASE_PATH=alpha_base_path,
        )

        return script
