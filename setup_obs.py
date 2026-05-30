"""
setup_obs.py
既存OBSシーンコレクション(Akari_TwitCasting_Min.json)に
emotion-overlayブラウザソースを追加する。
何度実行しても安全（重複チェックあり）。
"""
import json, shutil, uuid
from pathlib import Path

SCENES_DIR = Path.home() / "AppData/Roaming/obs-studio/basic/scenes"
TARGET = SCENES_DIR / "Akari_TwitCasting_Min.json"
OVERLAY_NAME = "emotion-overlay"
OVERLAY_URL  = "http://localhost:8765/overlay"

def patch():
    if not TARGET.exists():
        print(f"[setup_obs] NOT FOUND: {TARGET}")
        return False

    # バックアップ
    bak = TARGET.with_suffix(".json.akari_bak")
    if not bak.exists():
        shutil.copy2(TARGET, bak)
        print(f"[setup_obs] backup -> {bak.name}")

    with open(TARGET, encoding="utf-8") as f:
        data = json.load(f)

    sources = data.get("sources", [])

    # 既存チェック
    if any(s["name"] == OVERLAY_NAME for s in sources):
        print("[setup_obs] emotion-overlay already exists. skip.")
        return True

    # ─── overlayソースを追加 ───
    overlay_uuid = str(uuid.uuid4())
    overlay_source = {
        "prev_ver": 503316482,
        "name": OVERLAY_NAME,
        "uuid": overlay_uuid,
        "id": "browser_source",
        "versioned_id": "browser_source",
        "settings": {
            "url": OVERLAY_URL,
            "width": 1280,
            "height": 720,
            "fps_custom": True,
            "fps": 60,
            "css": "",
            "reroute_audio": False,
            "restart_when_active": False,
            "shutdown": False,
            "webpage_control_level": 1
        },
        "mixers": 0, "sync": 0, "flags": 0,
        "volume": 1.0, "balance": 0.5,
        "enabled": True, "muted": False,
        "push-to-mute": False, "push-to-mute-delay": 0,
        "push-to-talk": False, "push-to-talk-delay": 0,
        "hotkeys": {"ObsBrowser.Refresh": []},
        "deinterlace_mode": 0, "deinterlace_field_order": 0,
        "monitoring_type": 0, "private_settings": {}
    }
    sources.append(overlay_source)

    # ─── 全シーンのitemsリストに overlay を追加 ───
    for source in sources:
        if source.get("id") != "scene":
            continue

        scene_settings = source.get("settings", {})
        items = scene_settings.get("items", [])

        # id_counter を読んで次のIDを決定
        id_counter = scene_settings.get("id_counter", len(items))
        new_id = id_counter + 1
        scene_settings["id_counter"] = new_id

        # overlayアイテムを最前面（リスト末尾）に追加
        items.append({
            "name": OVERLAY_NAME,
            "source_uuid": overlay_uuid,
            "visible": True,
            "locked": True,
            "rot": 0.0,
            "pos": {"x": 0.0, "y": 0.0},
            "scale": {"x": 1.0, "y": 1.0},
            "align": 5,
            "bounds_type": 2,   # OBS_BOUNDS_SCALE_INNER
            "bounds_align": 0,
            "bounds": {"x": 1280.0, "y": 720.0},
            "crop_left": 0, "crop_top": 0,
            "crop_right": 0, "crop_bottom": 0,
            "id": new_id,
            "group_item_backup": False,
            "scale_filter": "disable",
            "blend_method": "default",
            "blend_type": "normal",
            "show_transition": {"duration": 0},
            "hide_transition": {"duration": 0},
            "private_settings": {}
        })
        scene_settings["items"] = items
        print(f"[setup_obs] added to scene: {source['name']}")

    data["sources"] = sources

    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"[setup_obs] done. {TARGET.name} updated.")
    return True

if __name__ == "__main__":
    ok = patch()
    if not ok:
        input("Press Enter to close...")
