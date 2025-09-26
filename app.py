from flask import Flask, render_template, jsonify, request
import subprocess
import threading
import time
import shutil
import json
import os
from threading import Lock
import base64
from flask import Response


app = Flask(__name__)

# Simulator serial provided by user
SIM_SERIAL = "127.0.0.1:16384"

# config storage
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
_config_lock = Lock()


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"adb_path": None}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"adb_path": None}


def save_config(cfg):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


cfg = load_config()

# locate adb executable (either from config or PATH)
ADB_PATH = cfg.get('adb_path') or shutil.which('adb')


# Background worker control
worker_thread = None
worker_stop = threading.Event()


def adb_shell(cmd_args):
    """Run an adb command against the configured simulator serial and return (returncode, stdout, stderr).

    If adb is not found, return a non-zero code and an explanatory error message.
    """
    # resolve ADB_PATH dynamically from current config in case it was changed at runtime
    global ADB_PATH, cfg
    ADB_PATH = cfg.get('adb_path') or shutil.which('adb')
    if not ADB_PATH:
        return 127, "", "adb not found on PATH"
    base = [ADB_PATH, "-s", SIM_SERIAL]
    try:
        proc = subprocess.Popen(base + cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        return proc.returncode, out.strip(), err.strip()
    except Exception as e:
        return 1, "", str(e)


def check_adb_connection():
    rc, out, err = adb_shell(["get-state"])  # get-state returns 'device' when connected
    if rc == 127:
        return False, err
    if rc == 0 and out == "device":
        return True, "Connected"
    # fallback: try devices list and search for serial
    rc2, out2, err2 = adb_shell(["devices"])
    if rc2 == 127:
        return False, err2
    if SIM_SERIAL in out2:
        return True, "Connected (listed)"
    # return whichever message we have
    return False, err or err2 or out or "Unknown"


def worker_loop():
    """Dummy worker that simulates bot running. Replace with actual screen recognition & control."""
    print("Worker started")
    while not worker_stop.is_set():
        # placeholder: sleep and print heartbeat
        print("Worker heartbeat: running...")
        time.sleep(2)
    print("Worker stopping")


@app.route('/')
def index():
    return render_template('index.html', serial=SIM_SERIAL)


@app.route('/connect', methods=['POST'])
def connect():
    # Try to proactively restart adb server and connect to the target serial using configured adb
    global cfg
    ADB = cfg.get('adb_path') or shutil.which('adb')
    if not ADB:
        return jsonify({"ok": False, "msg": "adb not found on PATH or in config", "details": {}})

    details = {}
    # kill-server
    try:
        p = subprocess.Popen([ADB, 'kill-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(timeout=5)
        details['kill-server'] = {"rc": p.returncode, "out": out.strip(), "err": err.strip()}
    except Exception as e:
        details['kill-server'] = {"rc": 1, "out": "", "err": str(e)}

    # start-server
    try:
        p = subprocess.Popen([ADB, 'start-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(timeout=5)
        details['start-server'] = {"rc": p.returncode, "out": out.strip(), "err": err.strip()}
    except Exception as e:
        details['start-server'] = {"rc": 1, "out": "", "err": str(e)}

    # try connect
    try:
        p = subprocess.Popen([ADB, 'connect', SIM_SERIAL], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(timeout=8)
        details['connect'] = {"rc": p.returncode, "out": out.strip(), "err": err.strip()}
    except Exception as e:
        details['connect'] = {"rc": 1, "out": "", "err": str(e)}

    # list devices
    try:
        p = subprocess.Popen([ADB, 'devices', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate(timeout=5)
        details['devices'] = {"rc": p.returncode, "out": out.strip(), "err": err.strip()}
    except Exception as e:
        details['devices'] = {"rc": 1, "out": "", "err": str(e)}

    # determine success
    devices_out = details.get('devices', {}).get('out', '')
    success = SIM_SERIAL in devices_out
    msg = 'Connected' if success else 'Not connected'
    return jsonify({"ok": success, "msg": msg, "details": details})


@app.route('/config', methods=['GET'])
def get_config():
    # return current config
    return jsonify({"adb_path": cfg.get('adb_path')})


@app.route('/config', methods=['POST'])
def set_config():
    global cfg
    data = request.get_json() or {}
    adb_path = data.get('adb_path')
    with _config_lock:
        cfg['adb_path'] = adb_path
        ok = save_config(cfg)
    return jsonify({"ok": ok, "adb_path": adb_path})


@app.route('/screenshot', methods=['GET'])
def screenshot():
    """Return a PNG screenshot captured from the device via adb exec-out screencap -p"""
    global cfg
    ADB = cfg.get('adb_path') or shutil.which('adb')
    if not ADB:
        return jsonify({"ok": False, "msg": "adb not found on PATH or in config"}), 400

    try:
        # exec-out screencap -p outputs PNG bytes to stdout
        p = subprocess.Popen([ADB, '-s', SIM_SERIAL, 'exec-out', 'screencap', '-p'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=12)
        if p.returncode != 0 or not out:
            return jsonify({"ok": False, "msg": "screencap failed", "err": err.decode(errors='ignore') if isinstance(err, bytes) else err}), 500
        return Response(out, mimetype='image/png')
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "msg": "screencap timeout"}), 500
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route('/screenshot_base64', methods=['GET'])
def screenshot_base64():
    """Return a base64-encoded PNG (useful for JSON transport)."""
    global cfg
    ADB = cfg.get('adb_path') or shutil.which('adb')
    if not ADB:
        return jsonify({"ok": False, "msg": "adb not found on PATH or in config"}), 400
    try:
        p = subprocess.Popen([ADB, '-s', SIM_SERIAL, 'exec-out', 'screencap', '-p'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=12)
        if p.returncode != 0 or not out:
            return jsonify({"ok": False, "msg": "screencap failed", "err": err.decode(errors='ignore') if isinstance(err, bytes) else err}), 500
        b64 = base64.b64encode(out).decode('ascii')
        return jsonify({"ok": True, "image_base64": b64})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "msg": "screencap timeout"}), 500
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route('/start', methods=['POST'])
def start_worker():
    global worker_thread, worker_stop
    if worker_thread and worker_thread.is_alive():
        return jsonify({"ok": False, "msg": "Worker already running"})
    worker_stop.clear()
    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()
    return jsonify({"ok": True, "msg": "Worker started"})


@app.route('/stop', methods=['POST'])
def stop_worker():
    global worker_thread, worker_stop
    if not worker_thread or not worker_thread.is_alive():
        return jsonify({"ok": False, "msg": "Worker not running"})
    worker_stop.set()
    worker_thread.join(timeout=5)
    return jsonify({"ok": True, "msg": "Worker stopped"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)
