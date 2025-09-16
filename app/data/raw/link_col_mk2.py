import bpy
import sys
import os

# --- Ambil argumen setelah "--"
argv = sys.argv
argv = argv[argv.index("--") + 1:]

if len(argv) < 3:
    print("Usage: blender --background --python script.py -- <master.blend> <anim.blend> <output_dir>")
    sys.exit(1)

master_file = argv[0]
anim_file = argv[1]
output_dir = argv[2]
output_file = os.path.join(output_dir, "test.blend")

print(">>> Master file:", master_file)
print(">>> Anim file  :", anim_file)
print(">>> Output file:", output_file)

# --- 1. Buka master file
bpy.ops.wm.open_mainfile(filepath=master_file)

scene_root = bpy.context.scene.collection

# --- Fungsi untuk reset collection (hapus kalau ada, buat ulang)
def recreate_collection(name: str):
    coll = bpy.data.collections.get(name)
    if coll:
        bpy.data.collections.remove(coll)
        print(f"Collection {name} dihapus.")
    new_coll = bpy.data.collections.new(name)
    scene_root.children.link(new_coll)
    print(f"Collection {name} dibuat ulang.")
    return new_coll

# --- 2. Siapkan collections utama
master_colls = {
    "CHAR": recreate_collection("CHAR"),
    "PROP": recreate_collection("PROP"),
    "SET": recreate_collection("SET"),
    "VEH": recreate_collection("VEH"),
}

# --- 3. Link collections dari anim sesuai prefix (termasuk CAM)
linked_names = []
with bpy.data.libraries.load(anim_file, link=True) as (data_from, data_to):
    for col_name in data_from.collections:
        if (
            col_name.startswith(("c-", "p-", "s-", "v-"))  # CHAR, PROP, SET, VEH
            or col_name == "CAM"                           # Kamera
        ):
            data_to.collections.append(col_name)
            linked_names.append(col_name)

# --- 4. Masukkan hasil link ke collection utama (pilih versi yang berasal dari anim_file)
for name in linked_names:
    candidates = [c for c in bpy.data.collections if c.name == name]
    if not candidates:
        continue

    # pilih koleksi yang benar-benar linked dari anim_file
    col = None
    for c in candidates:
        if c.library and os.path.basename(c.library.filepath) == os.path.basename(anim_file):
            col = c
            break
    # fallback kalau tidak ketemu (ambil yang pertama)
    if not col:
        col = candidates[0]

    if name.startswith("c-"):
        master_colls["CHAR"].children.link(col)
        print(f"Linked {name} ke CHAR (from {col.library.filepath if col.library else 'local'})")
    elif name.startswith("p-"):
        master_colls["PROP"].children.link(col)
        print(f"Linked {name} ke PROP")
    elif name.startswith("s-"):
        master_colls["SET"].children.link(col)
        print(f"Linked {name} ke SET")
    elif name.startswith("v-"):
        master_colls["VEH"].children.link(col)
        print(f"Linked {name} ke VEH")
    elif name == "CAM":
        scene_root.children.link(col)
        print("Collection CAM ditambahkan ke scene.")

# --- 5. Save as test.blend
bpy.ops.wm.save_as_mainfile(filepath=output_file)
print(">>> Selesai, file tersimpan:", output_file)
