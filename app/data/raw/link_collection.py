import bpy

# ---------------- helpers ----------------

def _unlink_collection_from(parent, target):
    """Recursively unlink target from a parent collection tree."""
    for child in list(parent.children):
        if child == target:
            parent.children.unlink(child)
        else:
            _unlink_collection_from(child, target)

def _force_remove_collection(name: str):
    """Unlink from all scenes, then remove the datablock if it exists."""
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
    """Create a fresh parent collection with 'name' and link it to the active scene."""
    if name != "CAM":
        _force_remove_collection(name)
        parent = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(parent)
        print(f"Created and linked parent collection: {name}")
        return parent

# ---------------- main op ----------------

def link_buckets():
    """
    Create new parent collections (CHAR/PROP/VEH/CAM).
    - For CHAR/PROP/VEH: link *all* library collections that start with c-/p-/v-.
    - For CAM: link the *exact* 'CAM' collection (no prefix matching).
    """
    libpath = "/mnt/J/02_production/03_animation/ep999/ep999_sq01/ep999_sq01_sh0120/jgt_ep999_sq01_sh0120_anm.blend"
    print("Animation file:", libpath)

    mapping = [
        ("CHAR", "c-"),
        ("PROP", "p-"),
        ("SET",  "s-"),
        ("VEH",  "v-"),
        ("CAM",  None),   # None => special case: link 'CAM' exactly
    ]

    # 1) Make fresh parents in scene
    parents = {}
    for name, prefix in mapping:
        if name == "CAM":
            _force_remove_collection("CAM")
            continue
        parents[name] = ensure_parent_in_scene(name)

    # 2) Link requested children from library
    with bpy.data.libraries.load(libpath, link=True) as (data_from, data_to):
        desired = {}
        for parent_name, prefix in mapping:
            if prefix is None:
                # Special case: CAM → link exact 'CAM' if present
                if "CAM" in data_from.collections:
                    desired[parent_name] = ["CAM"]
                    data_to.collections.append("CAM")
                else:
                    desired[parent_name] = []
                    print("[WARNING] 'CAM' collection not found in library")
            else:
                # Prefix case
                names = [n for n in data_from.collections if n.startswith(prefix)]
                desired[parent_name] = names
                for n in names:
                    data_to.collections.append(n)

    # 3) Parent linked children under their bucket parents
    for parent_name, child_names in desired.items():
        if parent_name == "CAM":
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
                if not (col.library and col.library.filepath == libpath):
                    col = next(
                        (c for c in bpy.data.collections
                         if c.name == cname and c.library and c.library.filepath == libpath),
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


# run it
link_buckets()
