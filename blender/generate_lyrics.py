import bpy
from pathlib import Path
import sys, re
import json

"""

Tested in Blender 2.8.
The expected line format is:

    8:1:I've; tried,; tried,; tried,; and i’ve; tried; even; more

"""

FONT_SIZE = 0.5
SPACE_SIZE = 0.2
LINES_SPACE = 0.5
FPS = 24
LOAD_FROM_FILE = False

LYRICS = (
    "2:1:Lyssna;inte;på;mig\n"
    "3:1:Jag har tagit allt för givet, jag bara faller\n"
    "4:1:Sen så fort hitta ord, jag måste blunda lite"
)

if LOAD_FROM_FILE:
    LYRICS_FILE = Path(r"C:\Users\mc\Desktop\no_more_fucks\lyrics.txt")
    # Something fails with this regex.
    REGEX_PATTERN = re.compile(
        r"(?P<timing>[0-9]*\.?[0-9]):(?P<phase>[0-9]*):(?P<lyrics>.*)"
    )

    with LYRICS_FILE.open("r", encoding="utf-8") as f:
        LYRICS = f.read()

LYRICS_PARSED = []


class LyricsLine:
    """docstring for LyricsLine"""

    def __init__(self, text: list, phase: int, anim_start: float, anim_length: float):
        self.text = text
        self.phase = phase
        self.anim_start = anim_start
        self.anim_length = anim_length


for l in LYRICS.split("\n"):
    ll = l.split(":")
    timing = float(ll[0])
    phase = int(ll[1])
    text_split = ll[2].split(";")
    LYRICS_PARSED.append(LyricsLine(text_split, phase, timing, 50))


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


def get_text_object(
    idx: int,
    text: str,
    phase: int,
    anim_start: int,
    anim_length: int,
    position: tuple = (0.0, 0.0, 0.0),
):
    # Create the text parts.
    font_data = bpy.data.curves.new(name=f"line_{idx}", type="FONT")
    obj = bpy.data.objects.new(f"line_part_{idx}", font_data)
    obj.data.size = FONT_SIZE
    obj.data.body = text
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
    alpha_node.outputs[0].default_value = 0.0
    alpha_node.outputs[0].keyframe_insert(data_path="default_value", frame=anim_start)
    alpha_node.outputs[0].default_value = 1.0
    alpha_node.outputs[0].keyframe_insert(
        data_path="default_value", frame=(anim_start + 10)
    )
    alpha_node.outputs[0].keyframe_insert(
        data_path="default_value", frame=(anim_start + 10 + anim_length)
    )
    alpha_node.outputs[0].default_value = 0.0
    alpha_node.outputs[0].keyframe_insert(
        data_path="default_value", frame=(anim_start + 10 + anim_length + 10)
    )
    return (obj, obj.dimensions)


def drop_lyrics(lyrics):
    for idx, lyr in enumerate(LYRICS_PARSED):
        # Create an empty, being a parent for all the line parts.
        lyrics_line = bpy.data.objects.new(f"lyrics_line_{idx}", None)
        lyrics_line.empty_display_size = 2
        lyrics_line.empty_display_type = "PLAIN_AXES"
        lyrics_line.parent = anchor
        collection.objects.link(lyrics_line)
        # Keeping track of words offset.
        spacing_accumlator = 0.0
        for idx2, t in enumerate(lyr.text):
            o, d_dimension = get_text_object(
                idx,
                t,
                lyr.phase,
                lyr.anim_start * FPS,
                lyr.anim_length,
                (spacing_accumlator + idx2 * SPACE_SIZE, 0, 0),
            )
            spacing_accumlator += d_dimension[0]
            o.parent = lyrics_line
            collection.objects.link(o)


if "Fonts" not in bpy.data.collections:
    print("Collection doesn't exist")
    sys.stdout.flush()
else:
    drop_lyrics(LYRICS)
