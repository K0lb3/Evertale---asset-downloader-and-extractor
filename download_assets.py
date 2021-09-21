from json.decoder import JSONDecodeError
from UnityPy import AssetsManager
import requests
import json
import os
import re
import AssetBatchConverter

ROOT = os.path.dirname(os.path.realpath(__file__))
MASTER = os.path.join(ROOT, "master")
ASSETS = os.path.join(ROOT, "assets")
LOC = os.path.join(ROOT, "localization")
os.makedirs(MASTER, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(LOC, exist_ok=True)

def download(path):
    url = f"https://prd.evertaleserver.com/Prd2_3/{path}"
    headers = {
        "X-Unity-Version":	"2018.4.30f1",
        "User-Agent":	"Dalvik/2.1.0 (Linux; U; Android 5.1.1; ASUS_I001DA Build/LMY49I)",
        "Host":	"prd.evertaleserver.com",
        "Connection":	"Keep-Alive",
        "Accept-Encoding":	"gzip"
    }
    return requests.get(url, headers=headers)

def download_asset(path):
    return download(f"Android2018LTS/{path}")

def download_localization(path):
    return download(f"Localization/{path}")

def load_json(fp):
    if os.path.exists(fp):
        with open(fp, "rt", encoding="utf8") as f:
            ret = json.load(f)
        return ret
    else:
        return {}

def save_json(fp, obj):
    with open(fp, "wt", encoding="utf8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)

def main():
    update_master(MASTER)
    update_localization(LOC)
    update_assets(ASSETS)

def update_master(path):
    hashs_fp = os.path.join(path, "Manifest.json")
    hashs_local = load_json(hashs_fp)
    hashs_online = download("Manifest.json").json()
    update = False
    for main, items in hashs_online.items():
        for name, hash in items.items():
            fp = os.path.join(path, f"{name}.json")

            if hashs_local.get(main,{}).get(name, None) != hash or not os.path.exists(fp):
                print(name)
                data = download(f"{name}.json").content
                with open(fp, "wb") as f:
                    f.write(data)
                update = True
    
    if update:
        save_json(hashs_fp, hashs_online)

def update_localization(path):
    hashs_fp = os.path.join(path, "FileHashes.json")
    hashs_local = load_json(hashs_fp)
    hashs_online = download_localization("FileHashes.json").json()
    update = False
    for name, hash in hashs_online.items():
        fp = os.path.join(path, f"{name}.json")
        if hashs_local.get(name,"") != hash or not os.path.exists(fp):
            print(name)
            data = download_localization(f"{name}").content
            with open(fp, "wb") as f:
                f.write(data)
            update = True
    
    if update:
        save_json(hashs_fp, hashs_online)

def update_assets(path):
    hashs_fp = os.path.join(path, "filehashes.json")
    hashs_local = load_json(hashs_fp)
    hashs_online = download_asset("hashes.json").json()
    update = False

    AssetBatchConverter.DST = path
    for name, detail in hashs_online.items():
        if not isinstance(detail, dict):
            continue
        hash = detail["hash"]
        
        if hashs_local.get(name,{}).get("hash","") != hash:
            print(name)
            data = download_asset(name).content
            AssetBatchConverter.extract_assets(data)
            update = True
    
    if update:
        save_json(hashs_fp, hashs_online)


if __name__ == "__main__":
    main()