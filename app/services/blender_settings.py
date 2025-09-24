from textwrap import dedent
from string import Template


class BlenderSettings:
    def __init__(self, blender_file: str):
        self.blender_file = blender_file

    @staticmethod
    def generate_lighting_script(master_file:str, animation_file: str, collection_list: list, camera_collection: str,
                        start_frame: int, end_frame: int, output_path: str,
                        beauty_base_path: str, alpha_base_path: str) -> str:
        tpl = Template(dedent("""
            import bpy

            # Open master file
            bpy.ops.wm.open_mainfile(filepath="$FILEPATH")
            
            
            # Utility functions for collection management
            def _unlink_collection_from(parent, target):
                for child in list(parent.children):
                    if child == target:
                        parent.children.unlink(child)
                    else:
                        _unlink_collection_from(child, target)
            
            
            def _force_remove_collection(name: str):
                coll = bpy.data.collections.get(name)
                if not coll:
                    return
                for scene in bpy.data.scenes:
                    _unlink_collection_from(scene.collection, coll)
                try:
                    bpy.data.collections.remove(coll)
                    print(f"Removed existing collection: {name}")
                except RuntimeError as e:
                    print(f"[WARNING] Could not remove '{name}': {e}")
            
            
            def ensure_parent_in_scene(name: str) -> bpy.types.Collection:
                if name != "$CAMERA_COLLECTION":
                    _force_remove_collection(name)
                    parent = bpy.data.collections.new(name)
                    bpy.context.scene.collection.children.link(parent)
                    print(f"Created and linked parent collection: {name}")
                    return parent
            
            
            # Holdout enable/disable
            def _find_layer_collection_by_coll(root_lc: bpy.types.LayerCollection,
                                               target_coll: bpy.types.Collection):
                if root_lc.collection == target_coll:
                    return root_lc
                for child in root_lc.children:
                    found = _find_layer_collection_by_coll(child, target_coll)
                    if found:
                        return found
                return None
            
            def _set_holdout_recursive(lc: bpy.types.LayerCollection, value: bool):
                lc.holdout = bool(value)
                for c in lc.children:
                    _set_holdout_recursive(c, value)
            
            
            def set_collection_holdout(collection_name: str, enabled: bool = True, all_view_layers: bool = False, recursive: bool = True, must_exist: bool = True,):
                scene = bpy.context.scene
                if not scene:
                    raise RuntimeError("No active scene found.")
            
                # Resolve collection argument
                if isinstance(collection_name, str):
                    coll = bpy.data.collections.get(collection_name)
                    if not coll:
                        raise ValueError(f"No collection named '{collection_name}'")
                    coll_name = collection_name
                elif isinstance(collection_name, bpy.types.Collection):
                    coll = collection_name
                    coll_name = coll.name
                else:
                    raise TypeError("`collection` must be a name (str) or a bpy.types.Collection")
            
                view_layers = scene.view_layers if all_view_layers else [bpy.context.view_layer]
            
                modified = 0
                for vl in view_layers:
                    root = vl.layer_collection
                    lc = _find_layer_collection_by_coll(root, coll)
                    if lc is None:
                        print(f"[INFO] Collection '{coll_name}' not found in layer '{vl.name}'.")
                        continue
            
                    if recursive:
                        _set_holdout_recursive(lc, enabled)
                    else:
                        lc.holdout = bool(enabled)
            
                    state = "ON" if enabled else "OFF"
                    scope = "including all sub-collections" if recursive else "only this collection"
                    print(f"[OK] Holdout {state} for '{coll_name}' ({scope}) in View Layer '{vl.name}'.")
                    modified += 1
            
                if must_exist and modified == 0:
                    raise ValueError(
                        f"Collection '{coll_name}' was not found in the targeted view layers. "
                        "Make sure the collection is linked into this scene and not excluded from the view layer."
                    )
            
                return modified
            
            
            # Define file paths and parameters
            
            def link_animation():
                # Link the animation file
                print("Animation file:", "$ANIMATION_FILE")
                parents = {}
                for name, prefix in $COLLECTION_LIST:
                    if name == "$CAMERA_COLLECTION":
                        _force_remove_collection("$CAMERA_COLLECTION")
                        continue
                    parents[name] = ensure_parent_in_scene(name)
            
                with bpy.data.libraries.load("$ANIMATION_FILE", link=True) as (data_from, data_to):
                    desired = {}
                    for parent_name, prefix in $COLLECTION_LIST:
                        if prefix is None:
                            # Special case: CAM → link exact 'CAM' if present
                            if "$CAMERA_COLLECTION" in data_from.collections:
                                desired[parent_name] = ["$CAMERA_COLLECTION"]
                                data_to.collections.append("$CAMERA_COLLECTION")
                            else:
                                desired[parent_name] = []
                                print("[WARNING] '$CAMERA_COLLECTION' collection not found in library")
                        else:
                            # Prefix case
                            names = [n for n in data_from.collections if n.startswith(prefix)]
                            desired[parent_name] = names
                            for n in names:
                                data_to.collections.append(n)
            
                for parent_name, child_names in desired.items():
                    if parent_name == "$CAMERA_COLLECTION":
                        # Just link CAM directly into the scene root
                        for cname in child_names:
                            coll = bpy.data.collections.get(cname)
                            if coll and cname not in bpy.context.scene.collection.children.keys():
                                bpy.context.scene.collection.children.link(coll)
                                print(f"Linked '{cname}' directly into the scene")
                    else:
                        # Normal parent bucket case
                        parent = parents[parent_name]
            
                        for cname in child_names:
                            # Try to find the collection by name
                            col = bpy.data.collections.get(cname)
                            if not col:
                                print(f"[WARNING] Expected linked collection missing: {cname}")
                                continue
            
                            # Ensure it's from the right library
                            if not (col.library and col.library.filepath == "$ANIMATION_FILE"):
                                col = next(
                                    (c for c in bpy.data.collections
                                     if c.name == cname and c.library and c.library.filepath == "$ANIMATION_FILE"),
                                    None
                                )
            
                            if not col:
                                print(f"[WARNING] No valid collection found for: {cname}")
                                continue
            
                            print(f"CHILD: {col.library.filepath}")
            
                            if cname not in parent.children.keys():
                                parent.children.link(col)
                                print(f"Added '{cname}' under '{parent_name}'")
                            else:
                                print(f"'{cname}' already under '{parent_name}'")
            
            
            def update_camera():
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
                scene.frame_start = $START_FRAME
                scene.frame_end = $END_FRAME
                print(f"Frame range set to: {$START_FRAME} - {$END_FRAME}")
            
            
            def set_relative():
                # Make all file paths relative
                bpy.context.preferences.filepaths.use_relative_paths = True
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
                    "beauty_output"].base_path = "$BEAUTY_BASE_PATH"
                for slot in bpy.data.scenes["Scene"].node_tree.nodes["beauty_output"].file_slots:
                    slot.path = "$BEAUTY_BASE_PATH"
            
                # Sambungan antar socket
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].outputs["Image"],
                    bpy.data.scenes["Scene"].node_tree.nodes["beauty_denoise"].inputs["Image"]
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
                        bpy.data.scenes["Scene"].node_tree.nodes["beauty_layer"].outputs[("Transp" if p == "Transparent" else p)],
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
                    "alpha_chr_output"].base_path = "$ALPHA_BASE_PATH"
                for slot in bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].file_slots:
                    slot.path = "$ALPHA_BASE_PATH"
            
                # Sambungan antar socket
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_layer"].outputs["Image"],
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].inputs["Image"]
                )
                bpy.data.scenes["Scene"].node_tree.links.new(
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_layer"].outputs["Alpha"],
                    bpy.data.scenes["Scene"].node_tree.nodes["alpha_chr_output"].inputs["Alpha"]
                )
            
                # Enable holdout
                target_layer_name = "alpha_char"
                target_layer = bpy.context.scene.view_layers.get(target_layer_name)
                if target_layer is None:
                    raise ValueError(f"View layer '{target_layer_name}' not found in the current scene.")
                bpy.context.window.view_layer = target_layer
                print(f"Switched to view layer: {target_layer_name}")
                set_collection_holdout("SET")
            
            
            def cleanup_node():
                scene = bpy.context.scene
                tree = scene.node_tree
                for node in list(tree.nodes):
                    tree.nodes.remove(node)
            
            
            # Execute functions
            link_animation()
            update_camera()
            set_duration()
            set_relative()
            cleanup_node()
            beauty_node()
            alpha_char_node()
            print("All operations completed successfully.")
            
            # Save the modified Blender file
            bpy.ops.wm.save_as_mainfile(filepath="$OUTPUT_PATH")
            print("File saved as: $OUTPUT_PATH")
            
            # Quit Blender
            bpy.ops.wm.quit_blender()
        """))

        script = tpl.substitute(
            FILEPATH=master_file,
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
