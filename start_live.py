"""
start_live.py
ダブルクリック1回 → バックグラウンドで全部起動 → OBSだけ開く
黒いウィンドウは一切出ない
"""
import subprocess
import sys
import time
import ctypes
from pathlib import Path

ROOT = Path(__file__).parent
PYTHON = r"C:\Python314\python.exe"
OBS = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW


def alert(msg):
    ctypes.windll.user32.MessageBoxW(0, msg, "Akari LIVE", 0x10)


def run_bg(args, cwd=None):
    return subprocess.Popen(
        args,
        cwd=cwd or str(ROOT),
        creationflags=NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def port_in_use(port):
    import socket
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    # 1. OBSシーン設定にoverlayを注入
    try:
        import setup_obs
        setup_obs.patch()
    except Exception as e:
        alert(f"OBSセットアップ失敗:\n{e}")
        sys.exit(1)

    # 2. emotion-bus (port 8765)
    if not port_in_use(8765):
        run_bg([PYTHON, "-m", "uvicorn", "server.main:app",
                "--host", "0.0.0.0", "--port", "8765"])
        time.sleep(3)

    # 3. mic-emitter
    run_bg([PYTHON, "agents/mic_emitter.py"])

    # 4. あかりの家 (port 3456)
    if not port_in_use(3456):
        run_bg([PYTHON, "-m", "http.server", "3456",
                "--directory", "akari-house-stream"])

    # 5. OBS起動
    subprocess.Popen(
        [OBS, "--collection", "Akari_TwitCasting_Min", "--minimize-to-tray"],
        creationflags=NO_WINDOW,
    )


if __name__ == "__main__":
    main()
