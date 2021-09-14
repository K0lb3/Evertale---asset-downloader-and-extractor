import os
import UnityPy
from collections import Counter
import json

TYPES = [
    # Images
    'Sprite',
    'Texture2D',
    # Text (filish)
    'TextAsset',
    'Shader',
    'MonoBehaviour',
    'Mesh'
    # Font
    'Font',
    # Audio
    'AudioClip',
]

ROOT = os.path.dirname(os.path.realpath(__file__))
DST = os.path.join(ROOT, "extracted")
IGNOR_DIR_COUNT=2

def extract_assets(src):
    # load source
    env = UnityPy.load(src)

    for fp, obj in env.container.items():
        export_obj(obj, os.path.join(DST, *fp.split("/")[IGNOR_DIR_COUNT:]), False)

def export_obj(obj, fp: str, append_name: bool = False) -> list:
    if obj.type not in TYPES:
        return []

    data = obj.read()
    if append_name:
        fp = os.path.join(fp, data.name)

    fp, extension = os.path.splitext(fp)
    os.makedirs(os.path.dirname(fp), exist_ok=True)

    # streamlineable types
    export = None
    if obj.type == 'TextAsset':
        if not extension:
            extension = '.txt'
        export = data.script

    elif obj.type == "Font":
        if data.m_FontData:
            extension = ".ttf"
            if data.m_FontData[0:4] == b"OTTO":
                extension = ".otf"
            export = data.m_FontData
        else:
            return [obj.path_id]

    elif obj.type == "Mesh":
        extension = ".obf"
        export = data.export().encode("utf8")

    elif obj.type == "Shader":
        extension = ".txt"
        export = data.export().encode("utf8")

    elif obj.type == "MonoBehaviour":
        # The data structure of MonoBehaviours is custom
        # and is stored as nodes
        # If this structure doesn't exist,
        # it might still help to at least save the binary data,
        # which can then be inspected in detail.
        if obj.serialized_type.nodes:
            extension = ".json"
            export = json.dumps(
                obj.read_typetree(),
                indent=4,
                ensure_ascii=False
            ).encode("utf8")
        else:
            extension = ".bin"
            export = data.raw_data

    if export:
        with open(f"{fp}{extension}", "wb") as f:
            f.write(export)

    # non-streamlineable types
    if obj.type == "Sprite":
        data.image.save(f"{fp}.png")

        return [obj.path_id, data.m_RD.texture.path_id, getattr(data.m_RD.alphaTexture, 'path_id', None)]

    elif obj.type == "Texture2D":
        if not os.path.exists(fp) and data.m_Width:
            # textures can have size 0.....
            data.image.save(f"{fp}.png")

    elif obj.type == "AudioClip":
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


if __name__ == '__main__':
    main()
