from pathlib import Path
import sys, re
import json
import math

try:
    import bpy
except ModuleNotFoundError:
    print("Couldn't import bpy... expect some fun!")

"""

Tested in Blender 2.8. Check `example.json` for the input data format.

"""

# Load the JSON describing the lyrics.
SCRIPT_PATH = Path(bpy.context.space_data.text.filepath).parent
LYRICS_FILE_DATA = (SCRIPT_PATH / Path("example.json")).read_text()
LYRICS = json.loads(LYRICS_FILE_DATA)

# Some constants. Probably should be moved.
FONT_SIZE = 0.5
SPACE_SIZE = 0.2
LINES_SPACE = 0.5
FPS = 24


# Find the collection.
collection = None
try:
    collection = bpy.data.collections["Fonts"]
except:
    collection = bpy.data.collections.new("Fonts")
    bpy.context.scene.collection.children.link(collection)
assert collection


# Find the anchor.
anchor = None
try:
    anchor = bpy.data.objects["anchor"]
except:
    anchor = bpy.data.objects.new("anchor", None)
    anchor.empty_display_size = 2
    anchor.empty_display_type = "PLAIN_AXES"
    collection.objects.link(anchor)
assert anchor

ANCHOR_LOCATION = anchor.location
ANCHOR_ORIENTATION = anchor.rotation_euler

# Build a shared grp_shared.
grp_shared = bpy.data.node_groups.new("grp_shared", type="ShaderNodeTree")
g_i = grp_shared.inputs.new("NodeSocketFloat", "alpha")
g_i.min_value = 0.0
g_i.max_value = 1.0
g_i.default_value = 1.0
grp_shared.outputs.new("NodeSocketShader", "out")

input = grp_shared.nodes.new("NodeGroupInput")
input.location = (-350, 0)

output = grp_shared.nodes.new("NodeGroupOutput")
output.location = (350, 0)

group_shader = grp_shared.nodes.new("ShaderNodeBsdfPrincipled")
group_shader.location = (0, 0)

grp_shared.links.new(input.outputs["alpha"], group_shader.inputs["Alpha"])
grp_shared.links.new(group_shader.outputs[0], output.inputs["out"])


def get_text_object(idx: int, segment: dict, position: tuple = (0.0, 0.0, 0.0)):
    # Create the text parts.
    font_data = bpy.data.curves.new(name=f"segment_{idx}", type="FONT")
    obj = bpy.data.objects.new(f"segment_{idx}", font_data)
    obj.data.size = FONT_SIZE
    obj.data.body = segment["text"]
    # location is in the parent coordinate system.
    obj.location = (
        0.0 + position[0],
        -(LINES_SPACE * (idx % 3)) + position[1],
        0.0 + position[2],
    )
    obj.rotation_euler = ANCHOR_ORIENTATION
    # Setup the material.
    material = bpy.data.materials.new(name="mat__")
    material.use_nodes = True
    material.blend_method = "BLEND"
    # Remove the default shader node.
    material.node_tree.nodes.remove(material.node_tree.nodes[1])
    # Setup material nodes.
    shared = material.node_tree.nodes.new(type="ShaderNodeGroup")
    shared.node_tree = grp_shared
    alpha_node = material.node_tree.nodes.new(type="ShaderNodeValue")
    shared.name = "grp_shared"
    alpha_node.name = "node_alpha"
    # Position the nodes.
    material.node_tree.nodes[0].location = (300, 0)
    shared.location = (0, 0)
    alpha_node.location = (-300, 0)
    # Link nodes
    material.node_tree.links.new(
        shared.outputs[0], material.node_tree.nodes["Material Output"].inputs[0]
    )
    material.node_tree.links.new(alpha_node.outputs[0], shared.inputs[0])
    # Add material.
    obj.data.materials.append(material)
    # Add keyframes.
    for k in segment["keys"]:
        alpha_node.outputs[0].default_value = k["value"]
        alpha_node.outputs[0].keyframe_insert(
            data_path="default_value", frame=math.floor(k["offset"] * FPS / 100.0)
        )
    return (obj, obj.dimensions)


def drop_lyrics(lyrics):
    for idx, line in enumerate(LYRICS["lines"]):
        # Create an empty, being a parent for all the line parts.
        lyrics_line = bpy.data.objects.new(f"lyrics_line_{idx}", None)
        lyrics_line.empty_display_size = 2
        lyrics_line.empty_display_type = "PLAIN_AXES"
        lyrics_line.parent = anchor
        collection.objects.link(lyrics_line)
        # Keeping track of words offset.
        spacing_accumlator = 0.0
        for idx2, segment in enumerate(line["segments"]):
            o, d_dimension = get_text_object(
                idx, segment, (spacing_accumlator + idx2 * SPACE_SIZE, 0, 0)
            )
            spacing_accumlator += d_dimension[0]
            o.parent = lyrics_line
            collection.objects.link(o)


if "Fonts" not in bpy.data.collections:
    print("Collection doesn't exist")
    sys.stdout.flush()
else:
    drop_lyrics(LYRICS)
