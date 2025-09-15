bl_info = {
    "name": "Compositor Tools",
    "author": "Hafid",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "Compositor > Sidebar > Compositor Tools",
    "description": "Apply scene prefs and generate compositor nodes with auto output paths",
    "category": "Compositing",
}

import bpy
import os
import re

# -----------------------------
# Helpers: parse & path build
# -----------------------------
def parse_ep_sq_sh_from_blendname(name_noext: str):
    m = re.search(r"(ep\d+).*?(sq\d+).*?(sh\d+)", name_noext, re.IGNORECASE)
    if not m:
        return ("ep000", "sq00", "sh0000")
    ep, sq, sh = m.groups()
    return ep.lower(), sq.lower(), sh.lower()

def drive_letter_prefix(name_noext: str):
    n = name_noext.lower()
    if n.startswith("jgt"):
        return "K"
    if n.startswith("rmb"):
        return "O"
    return "K"  # fallback

def prefix_title(name_noext: str):
    n = name_noext.lower()
    if n.startswith("jgt"):
        return "jgt"
    if n.startswith("rmb"):
        return "rmb"
    return ""  # fallback

def gen_ouput_path(layer_name: str):
    blend_path = bpy.data.filepath
    name_noext = os.path.splitext(os.path.basename(blend_path))[0] if blend_path else ""

    if not name_noext:
        drive = "K"
        ep, sq, sh = "ep000", "sq00", "sh0000"
        title = ""
    else:
        drive = drive_letter_prefix(name_noext)
        ep, sq, sh = parse_ep_sq_sh_from_blendname(name_noext)
        title = prefix_title(name_noext)

    # Folder berjenjang + exr + nama layer
    dir_path = f"/mnt/{drive}/{ep}/{ep}_{sq}/{ep}_{sq}_{sh}/exr/{layer_name}/{title}_{ep}_{sq}_{sh}_{layer_name}_####"
    return dir_path

# -----------------------------
# Prefs dari preset-mu (diringkas)
# -----------------------------
def apply_scene_settings(scene):
    scene.use_nodes = True

    #Volumes
    scene.eevee.volumetric_tile_size = "16"
    scene.eevee.volumetric_samples = 200
    scene.eevee.volumetric_sample_distribution = 1
    scene.eevee.volumetric_ray_depth = 16

    scene.eevee.use_volume_custom_range = True
    scene.eevee.volumetric_start = 30
    scene.eevee.volumetric_end = 200

    # Sampling / Viewport
    scene.eevee.taa_samples = 32
    scene.eevee.use_taa_reprojection = True
    scene.eevee.use_shadow_jitter_viewport = True

    # Render
    scene.eevee.taa_render_samples = 64
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "ARRI K1S1"

    #Default output path in format tab
    scene.render.filepath = "/tmp/"

    # Shadows
    scene.eevee.use_volumetric_shadows = True
    scene.eevee.shadow_resolution_scale = 0.3
    scene.eevee.light_threshold = 0.1

    # Raytracing
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_options.screen_trace_quality = 0.5
    scene.eevee.ray_tracing_options.trace_max_roughness = 0.01

    # Simplify
    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 0

    # Film
    scene.render.film_transparent = True

    # Performance
    scene.render.compositor_device = "GPU"

    # Format
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.use_border = False
    scene.render.fps = 24
    scene.render.use_stamp = False
    scene.render.use_sequencer = False

    # Output defaults (global)
    scene.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    scene.render.image_settings.exr_codec = "PIZ"
    scene.render.image_settings.color_management = "FOLLOW_SCENE"

    # View Layer: beauty
    if "beauty" in scene.view_layers:
        vl = scene.view_layers["beauty"]
        vl.use = True
        scene.render.use_single_layer = False

        vl.use_pass_combined = True
        vl.use_pass_z = True
        vl.use_pass_mist = True
        vl.use_pass_normal = False
        vl.use_pass_position = False
        vl.use_pass_vector = False
        vl.use_pass_grease_pencil = False

        vl.use_pass_diffuse_direct = False
        vl.use_pass_diffuse_color = False

        vl.use_pass_glossy_direct = False
        vl.use_pass_glossy_color = False

        if hasattr(vl, "eevee") and hasattr(vl.eevee, "use_pass_volume_direct"):
            vl.eevee.use_pass_volume_direct = False

        vl.use_pass_emit = True
        vl.use_pass_environment = False
        vl.use_pass_shadow = True
        vl.use_pass_ambient_occlusion = True
        if hasattr(vl, "eevee") and hasattr(vl.eevee, "use_pass_transparent"):
            vl.eevee.use_pass_transparent = True

        vl.use_pass_cryptomatte_object = True
        vl.use_pass_cryptomatte_material = True
        vl.use_pass_cryptomatte_asset = True
        vl.pass_cryptomatte_depth = 6

    # GTAO
    scene.eevee.gtao_distance = 5.8

# -----------------------------
# Node builder
# -----------------------------
def build_nodes(scene):
    scene.use_nodes = True
    tree = scene.node_tree

    for node in list(tree.nodes):
        tree.nodes.remove(node)

    links = tree.links

    # Beauty
    beauty_layer = tree.nodes.new("CompositorNodeRLayers")
    beauty_layer.location = (-600, 300)
    beauty_layer.name = "beauty_layer"
    beauty_layer.label = "beauty_layer"
    beauty_layer.layer = "beauty"

    beauty_denoise = tree.nodes.new("CompositorNodeDenoise")
    beauty_denoise.location = (-350, 300)
    beauty_denoise.name = "beauty_denoise"
    beauty_denoise.label = "beauty_denoise"
    if hasattr(beauty_denoise, "quality"):
        beauty_denoise.quality = 'HIGH'

    beauty_output = tree.nodes.new("CompositorNodeOutputFile")
    beauty_output.location = (100, 300)
    beauty_output.name = "beauty_output"
    beauty_output.label = "beauty_output"

    beauty_passes = [
        "Image", "Alpha", "Depth", "Mist", "Emit", "Shadow", "AO", "Transparent",
        "CryptoObject00", "CryptoObject01", "CryptoObject02",
        "CryptoAsset00", "CryptoAsset01", "CryptoAsset02",
        "CryptoMaterial00", "CryptoMaterial01", "CryptoMaterial02"
    ]
    beauty_output.file_slots.clear()
    for p in beauty_passes:
        beauty_output.file_slots.new(p)

    # Path (dir + stub) → set ke SEMUA slot
    beauty_dir = gen_ouput_path("beauty")
    beauty_output.base_path = beauty_dir
    for slot in beauty_output.file_slots:
        slot.path = beauty_dir

    if "Image" in beauty_layer.outputs:
        links.new(beauty_layer.outputs["Image"], beauty_denoise.inputs["Image"])
    if "Denoising Normal" in beauty_layer.outputs:
        links.new(beauty_layer.outputs["Denoising Normal"], beauty_denoise.inputs["Normal"])
    if "Denoising Albedo" in beauty_layer.outputs:
        links.new(beauty_layer.outputs["Denoising Albedo"], beauty_denoise.inputs["Albedo"])
    if "Image" in beauty_output.inputs:
        links.new(beauty_denoise.outputs["Image"], beauty_output.inputs["Image"])

    for p in beauty_passes:
        if p != "Image" and p in beauty_layer.outputs.keys() and p in beauty_output.inputs.keys():
            links.new(beauty_layer.outputs[p], beauty_output.inputs[p])

    try:
        rl_socket = beauty_layer.outputs[7]
        fo_socket = beauty_output.inputs[7]
        if not fo_socket.is_linked:
            links.new(rl_socket, fo_socket)
    except Exception:
        pass

    # Alpha Char
    alpha_layer = tree.nodes.new("CompositorNodeRLayers")
    alpha_layer.location = (-600, -120)
    alpha_layer.name = "alpha_chr_layer"
    alpha_layer.label = "alpha_chr_layer"
    alpha_layer.layer = "alpha_char"

    alpha_output = tree.nodes.new("CompositorNodeOutputFile")
    alpha_output.location = (100, -120)
    alpha_output.name = "alpha_chr_output"
    alpha_output.label = "alpha_chr_output"

    alpha_output.file_slots.clear()
    for p in ["Image", "Alpha"]:
        alpha_output.file_slots.new(p)

    alpha_dir = gen_ouput_path("alpha_char")
    alpha_output.base_path = alpha_dir
    for slot in alpha_output.file_slots:
        slot.path = alpha_dir

    if "Image" in alpha_layer.outputs:
        links.new(alpha_layer.outputs["Image"], alpha_output.inputs["Image"])
    if "Alpha" in alpha_layer.outputs:
        links.new(alpha_layer.outputs["Alpha"], alpha_output.inputs["Alpha"])

# -----------------------------
# Operator & Panel
# -----------------------------
class COMPOSITOR_OT_node_generator(bpy.types.Operator):
    bl_idname = "compositor_tools.node_generator"
    bl_label = "Node Generator"

    def execute(self, context):
        scene = context.scene
        apply_scene_settings(scene)
        build_nodes(scene)
        self.report({'INFO'}, "Prefs applied, nodes generated, paths set")
        return {'FINISHED'}

class COMPOSITOR_PT_tools(bpy.types.Panel):
    bl_label = "Compositor Tools"
    bl_idname = "COMPOSITOR_PT_tools"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Compositor Tools"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'

    def draw(self, context):
        layout = self.layout
        layout.operator("compositor_tools.node_generator", text="Node Generator")

# -----------------------------
# Register
# -----------------------------
classes = [COMPOSITOR_OT_node_generator, COMPOSITOR_PT_tools]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
