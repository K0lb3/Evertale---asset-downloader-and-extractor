import os
import UnityPy
from PIL import Image
import json
from UnityPy.enums import ClassIDType
from UnityPy.classes import Object, PPtr

TYPES = [
    # Text (filish)
    "TextAsset",
    "Shader",
    "MonoBehaviour",
    "Mesh"
    # Font
    "Font",
    # Audio
    "AudioClip",
    # Images
    "Sprite",
    "Texture2D",
    # Specific for this game
    "GameObject",
]

ROOT = os.path.dirname(os.path.realpath(__file__))
DST = os.path.join(ROOT, "extracted")
IGNOR_DIR_COUNT = 2


def extract_assets(src):
    # load source
    env = UnityPy.load(src)

    for fp, obj in sorted(
        env.container.items(),
        key=lambda item: TYPES.index(item[1].type.name)
        if item[1].type.name in TYPES
        else 999,
    ):
        if fp.endswith(".prefab"):
            refs = crawl_obj(obj)
            if any(x.type == ClassIDType.Texture2D for x in l.values()):
                print(f, key)
        else:
            export_obj(obj, os.path.join(DST, *fp.split("/")[IGNOR_DIR_COUNT:]), False)


def export_obj(obj, fp: str, append_name: bool = False) -> list:
    if obj.type.name not in TYPES:
        return []

    data = obj.read()

    if append_name:
        fp = os.path.join(fp, data.name)

    fp, extension = os.path.splitext(fp)
    os.makedirs(os.path.dirname(fp), exist_ok=True)

    # streamlineable types
    if obj.type.name == "GameObject":
        for component in data.get("m_Components", []):
            if component.type == "MonoBehaviour":
                component = component.read()
                texture = component.get("m_Texture", None)
                if texture:
                    return export_obj(texture, f"{fp}_tex")

    export = None
    if obj.type.name == "TextAsset":
        if not extension:
            extension = ".txt"
        export = data.script

    elif obj.type.name == "Font":
        if data.m_FontData:
            extension = ".ttf"
            if data.m_FontData[0:4] == b"OTTO":
                extension = ".otf"
            export = data.m_FontData
        else:
            return [obj.path_id]

    elif obj.type.name == "Mesh":
        extension = ".obf"
        export = data.export().encode("utf8")

    elif obj.type.name == "Shader":
        extension = ".txt"
        export = data.export().encode("utf8")

    elif obj.type.name == "MonoBehaviour":
        # The data structure of MonoBehaviours is custom
        # and is stored as nodes
        # If this structure doesn't exist,
        # it might still help to at least save the binary data,
        # which can then be inspected in detail.
        if obj.serialized_type.nodes:
            extension = ".json"
            export = json.dumps(
                obj.read_typetree(), indent=4, ensure_ascii=False
            ).encode("utf8")
        else:
            extension = ".bin"
            export = data.raw_data

    if export:
        with open(f"{fp}{extension}", "wb") as f:
            f.write(export)

    # non-streamlineable types
    if obj.type.name == "Sprite":
        data.image.save(f"{fp}.png")

        return [
            obj.path_id,
            data.m_RD.texture.path_id,
            getattr(data.m_RD.alphaTexture, "path_id", None),
        ]

    elif obj.type.name == "Texture2D":
        if data.m_Width:
            # textures can have size 0.....
            if os.path.exists(f"{fp}.png"):
                img = Image.open(f"{fp}.png")
                if img.size != (data.m_Width, data.m_Height):
                    data.image.save(f"{fp}_tex.png")
                return [obj.path_id]
            else:
                data.image.save(f"{fp}.png")

    elif obj.type.name == "AudioClip":
        samples = data.samples
        if len(samples) == 0:
            pass
        elif len(samples) == 1:
            with open(f"{fp}.wav", "wb") as f:
                f.write(list(data.samples.values())[0])
        else:
            os.makedirs(fp, exist_ok=True)
            for name, clip_data in samples.items():
                with open(os.path.join(fp, f"{name}.wav"), "wb") as f:
                    f.write(clip_data)
    return [obj.path_id]

def crawl_obj(obj: Object, ret: dict = None) -> dict:
    """Crawls through the data struture of the object and returns a list of all the components."""
    if not ret:
        ret = {}

    if isinstance(obj, PPtr):
        try:
            obj = obj.read()
        except AttributeError:
            return ret
    else:
        return ret
    ret[obj.path_id] = obj

    if obj.type == ClassIDType.MonoBehaviour:
        data = obj.read_typetree()
    else:
        data = obj.__dict__.values()

    for value in flatten(data):
        if isinstance(value, (PPtr, Object)):
            if value.path_id in ret:
                continue
            crawl_obj(value, ret)

    return ret

def flatten(l):
    for el in list(l):
        if isinstance(el, (list, tuple)):
            yield from flatten(el)
        elif isinstance(el, dict):
            yield from flatten(el.values())
        else:
            yield el