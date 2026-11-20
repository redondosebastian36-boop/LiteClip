import json
import os
import re
import subprocess
import threading
import tkinter as tk
import winsound
from datetime import datetime
from tkinter import messagebox, ttk
import keyboard
import pystray
from PIL import Image, ImageDraw

CONFIG_FILE = "config.json"
LOG_FILE = "ffmpeg_last_error.log"

DEFAULT_CONFIG = {
    "language": "en",
    "theme": "dark",
    "hotkey": "f9",
    "fps_mode": "30",
    "custom_fps": 30,
    "resolution_mode": "1280x720 (HD)",
    "custom_width": 1280,
    "custom_height": 720,
    "quality": "medium",           # "low", "medium", "high"
    "monitor_index": 1,
    "audio_backend": "wasapi",      # "wasapi" or "dshow"
    "system_audio_enabled": False,
    "system_audio_device": "",
    "system_volume": 150,
    "mic_enabled": False,
    "mic_device": "",
    "mic_volume": 120,
    "sound_effects": True,
    "run_in_background": True,
    "output_folder": "clips",
    "use_qsv": False
}

THEMES = {
    "dark": {"bg": "#18181B", "panel": "#27272A", "input_bg": "#18181B", "fg": "#F4F4F5", "muted": "#A1A1AA", "btn": "#3F3F46"},
    "purple": {"bg": "#1E1035", "panel": "#2E1A47", "input_bg": "#170B29", "fg": "#F5F3FF", "muted": "#C4B5FD", "btn": "#5B21B6"},
    "blue": {"bg": "#0F172A", "panel": "#1E293B", "input_bg": "#0B1120", "fg": "#F8FAFC", "muted": "#93C5FD", "btn": "#1D4ED8"},
    "red": {"bg": "#240B0E", "panel": "#3B1116", "input_bg": "#190608", "fg": "#FEF2F2", "muted": "#FCA5A5", "btn": "#991B1B"},
    "white": {"bg": "#F4F4F5", "panel": "#FFFFFF", "input_bg": "#E4E4E7", "fg": "#18181B", "muted": "#52525B", "btn": "#D4D4D8"}
}

THEME_NAMES = {
    "en": {"dark": "Dark", "purple": "Purple", "blue": "Blue", "red": "Red", "white": "White"},
    "es": {"dark": "Oscura", "purple": "Morada", "blue": "Azul", "red": "Roja", "white": "Blanca"},
    "fr": {"dark": "Sombre", "purple": "Violet", "blue": "Bleu", "red": "Rouge", "white": "Blanc"},
    "zh": {"dark": "深色", "purple": "紫色", "blue": "蓝色", "red": "红色", "white": "白色"},
    "ja": {"dark": "ダーク", "purple": "パープル", "blue": "ブルー", "red": "レッド", "white": "ホワイト"}
}

QUALITY_NAMES = {
    "en": {"low": "Low", "medium": "Medium", "high": "High"},
    "es": {"low": "Baja", "medium": "Media", "high": "Alta"},
    "fr": {"low": "Basse", "medium": "Moyenne", "high": "Haute"},
    "zh": {"low": "低", "medium": "中", "high": "高"},
    "ja": {"low": "低", "medium": "中", "high": "高"}
}

TRANSLATIONS = {
    "en": {
        "title": "LiteClip — Screen & Clip Recorder",
        "ready": "Ready",
        "recording": "Recording",
        "hotkey_label": "Hotkey (press Save to apply):",
        "monitor_label": "Monitor:",
        "quality_label": "Quality:",
        "res_label": "Resolution:",
        "fps_label": "FPS:",
        "custom_fps_label": "Custom FPS:",
        "qsv_label": "Use Intel QuickSync (h264_qsv)",
        "sound_label": "Play sound on start/stop",
        "bg_label": "Run in background (minimize to tray on close)",
        "lang_label": "Language:",
        "theme_label": "Theme:",
        "tab_capture": "Capture",
        "tab_audio": "Audio",
        "tab_ui": "Interface",
        "audio_backend_label": "Audio API (try WASAPI or DirectShow):",
        "sys_audio": "Record system audio",
        "sys_vol": "System volume (%):",
        "mic_audio": "Record microphone",
        "mic_vol": "Microphone volume (%):",
        "detect_btn": "Refresh audio devices",
        "start_btn": "Start recording",
        "stop_btn": "Stop recording",
        "clips_btn": "Open clips",
        "save_btn": "Save",
        "saved_msg": "Settings saved",
        "clip_saved": "Clip saved",
        "hud_rec": "RECORDING",
        "tray_open": "Open settings",
        "tray_toggle": "Start / Stop",
        "tray_clips": "Open clips folder",
        "tray_exit": "Exit",
        "no_audio_found": "No audio devices found for selected API.\nTry switching between WASAPI and DirectShow and click Refresh.",
        "devices_found": "Found {count} audio device(s).",
        "invalid_nums": "Width, height, FPS, monitor and volume must be valid numbers.",
        "ffmpeg_err": "Recording failed! Check ffmpeg_last_error.log"
    },
    "es": {
        "title": "LiteClip — Grabador de Clips",
        "ready": "Listo",
        "recording": "Grabando",
        "hotkey_label": "Tecla de atajo (pulsa Guardar para aplicar):",
        "monitor_label": "Monitor:",
        "quality_label": "Calidad:",
        "res_label": "Resolución:",
        "fps_label": "FPS:",
        "custom_fps_label": "FPS custom:",
        "qsv_label": "Usar Intel QuickSync (h264_qsv)",
        "sound_label": "Sonido al iniciar/detener",
        "bg_label": "Ejecutar en segundo plano (ir a bandeja al cerrar)",
        "lang_label": "Idioma:",
        "theme_label": "Tema:",
        "tab_capture": "Captura",
        "tab_audio": "Audio",
        "tab_ui": "Interfaz",
        "audio_backend_label": "API de Audio (prueba WASAPI o DirectShow):",
        "sys_audio": "Grabar audio del sistema",
        "sys_vol": "Volumen sistema (%):",
        "mic_audio": "Grabar micrófono",
        "mic_vol": "Volumen micrófono (%):",
        "detect_btn": "Detectar dispositivos de audio",
        "start_btn": "Iniciar grabación",
        "stop_btn": "Detener grabación",
        "clips_btn": "Abrir clips",
        "save_btn": "Guardar",
        "saved_msg": "Ajustes guardados",
        "clip_saved": "Clip guardado",
        "hud_rec": "GRABANDO",
        "tray_open": "Abrir panel",
        "tray_toggle": "Grabar / Detener",
        "tray_clips": "Abrir carpeta de clips",
        "tray_exit": "Salir",
        "no_audio_found": "No se detectaron dispositivos para esta API.\nPrueba cambiar entre WASAPI y DirectShow y pulsa Detectar.",
        "devices_found": "Se detectaron {count} dispositivo(s) de audio.",
        "invalid_nums": "Ancho, alto, FPS, monitor y volumen deben ser números válidos.",
        "ffmpeg_err": "¡Error al grabar! Revisa ffmpeg_last_error.log"
    },
    "fr": {
        "title": "LiteClip — Enregistreur d'écran",
        "ready": "Prêt",
        "recording": "Enregistrement",
        "hotkey_label": "Raccourci (cliquez sur Enregistrer pour appliquer) :",
        "monitor_label": "Écran :",
        "quality_label": "Qualité :",
        "res_label": "Résolution :",
        "fps_label": "IPS :",
        "custom_fps_label": "IPS perso :",
        "qsv_label": "Utiliser Intel QuickSync (h264_qsv)",
        "sound_label": "Son au démarrage / arrêt",
        "bg_label": "Exécuter en arrière-plan (barre système à la fermeture)",
        "lang_label": "Langue :",
        "theme_label": "Thème :",
        "tab_capture": "Capture",
        "tab_audio": "Audio",
        "tab_ui": "Interface",
        "audio_backend_label": "API Audio (WASAPI ou DirectShow) :",
        "sys_audio": "Enregistrer l'audio système",
        "sys_vol": "Volume système (%) :",
        "mic_audio": "Enregistrer le microphone",
        "mic_vol": "Volume micro (%) :",
        "detect_btn": "Actualiser les périphériques",
        "start_btn": "Démarrer",
        "stop_btn": "Arrêter",
        "clips_btn": "Ouvrir clips",
        "save_btn": "Enregistrer",
        "saved_msg": "Paramètres enregistrés",
        "clip_saved": "Clip enregistré",
        "hud_rec": "ENREGISTREMENT",
        "tray_open": "Ouvrir les paramètres",
        "tray_toggle": "Démarrer / Arrêter",
        "tray_clips": "Ouvrir le dossier des clips",
        "tray_exit": "Quitter",
        "no_audio_found": "Aucun périphérique détecté.\nEssayez WASAPI ou DirectShow puis actualisez.",
        "devices_found": "{count} périphérique(s) audio détecté(s).",
        "invalid_nums": "La largeur, hauteur, IPS, écran et volume doivent être des nombres.",
        "ffmpeg_err": "Erreur d'enregistrement ! Voir ffmpeg_last_error.log"
    },
    "zh": {
        "title": "LiteClip — 轻量录屏工具",
        "ready": "就绪",
        "recording": "录制中",
        "hotkey_label": "快捷键（点击保存后生效）：",
        "monitor_label": "显示器：",
        "quality_label": "画质：",
        "res_label": "分辨率：",
        "fps_label": "帧率：",
        "custom_fps_label": "自定义帧率：",
        "qsv_label": "使用 Intel QuickSync (h264_qsv)",
        "sound_label": "开始/停止时播放提示音",
        "bg_label": "后台运行（关闭窗口时最小化到托盘）",
        "lang_label": "语言：",
        "theme_label": "主题：",
        "tab_capture": "录制",
        "tab_audio": "音频",
        "tab_ui": "界面",
        "audio_backend_label": "音频接口（WASAPI 或 DirectShow）：",
        "sys_audio": "录制系统声音",
        "sys_vol": "系统音量 (%)：",
        "mic_audio": "录制麦克风",
        "mic_vol": "麦克风音量 (%)：",
        "detect_btn": "刷新音频设备",
        "start_btn": "开始录制",
        "stop_btn": "停止录制",
        "clips_btn": "打开文件夹",
        "save_btn": "保存",
        "saved_msg": "设置已保存",
        "clip_saved": "片段已保存",
        "hud_rec": "正在录制",
        "tray_open": "打开设置",
        "tray_toggle": "开始 / 停止",
        "tray_clips": "打开录制目录",
        "tray_exit": "退出",
        "no_audio_found": "未检测到音频设备。\n请切换 WASAPI 或 DirectShow 后刷新。",
        "devices_found": "检测到 {count} 个音频设备。",
        "invalid_nums": "宽度、高度、帧率、显示器和音量必须是有效数字。",
        "ffmpeg_err": "录制失败！请查看 ffmpeg_last_error.log"
    },
    "ja": {
        "title": "LiteClip — クリップ録画ツール",
        "ready": "待機中",
        "recording": "録画中",
        "hotkey_label": "ホットキー（保存で反映）：",
        "monitor_label": "モニター：",
        "quality_label": "画質：",
        "res_label": "解像度：",
        "fps_label": "FPS：",
        "custom_fps_label": "カスタムFPS：",
        "qsv_label": "Intel QuickSync を使用 (h264_qsv)",
        "sound_label": "開始/停止時に音を鳴らす",
        "bg_label": "バックグラウンド実行（閉じる時にトレイへ格納）",
        "lang_label": "言語：",
        "theme_label": "テーマ：",
        "tab_capture": "録画",
        "tab_audio": "オーディオ",
        "tab_ui": "表示",
        "audio_backend_label": "オーディオ API（WASAPI / DirectShow）：",
        "sys_audio": "システム音声を録音",
        "sys_vol": "システム音量 (%)：",
        "mic_audio": "マイク音声を録音",
        "mic_vol": "マイク音量 (%)：",
        "detect_btn": "オーディオ機器を更新",
        "start_btn": "録画開始",
        "stop_btn": "録画停止",
        "clips_btn": "フォルダを開く",
        "save_btn": "保存",
        "saved_msg": "設定を保存しました",
        "clip_saved": "クリップを保存しました",
        "hud_rec": "録画中",
        "tray_open": "設定を開く",
        "tray_toggle": "開始 / 停止",
        "tray_clips": "クリップフォルダを開く",
        "tray_exit": "終了",
        "no_audio_found": "オーディオ機器が見つかりません。\nWASAPI と DirectShow を切り替えて更新してください。",
        "devices_found": "{count} 件のオーディオ機器を検出しました。",
        "invalid_nums": "幅、高さ、FPS、モニター、音量は有効な数値で入力してください。",
        "ffmpeg_err": "録画エラー！ffmpeg_last_error.log を確認してください"
    }
}

LANG_NAMES = {"English": "en", "Español": "es", "Français": "fr", "中文": "zh", "日本語": "ja"}
LANG_CODES_TO_NAME = {v: k for k, v in LANG_NAMES.items()}


def t(key):
    lang = CONFIG.get("language", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def get_theme_palette():
    return THEMES.get(CONFIG.get("theme", "dark"), THEMES["dark"])


def normalize_quality(val):
    s = str(val or "medium").strip().lower()
    if s in ("low", "baja", "basse", "低"):
        return "low"
    if s in ("high", "alta", "haute", "高"):
        return "high"
    return "medium"


def get_quality_maps():
    lang = CONFIG.get("language", "en")
    qmap = QUALITY_NAMES.get(lang, QUALITY_NAMES["en"])
    return {v: k for k, v in qmap.items()}, {k: v for k, v in qmap.items()}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = {**DEFAULT_CONFIG, **data}
                merged["quality"] = normalize_quality(merged.get("quality", "medium"))
                return merged
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


CONFIG = load_config()
os.makedirs(CONFIG["output_folder"], exist_ok=True)

ffmpeg_process = None
current_output_path = None
is_recording = False
hotkey_paused = False
tray_icon = None
main_gui_win = None
gui_status_var = None
gui_record_btn = None
hud_label = None
hud_frame = None
state_lock = threading.Lock()


def play_cue(kind="start"):
    if not CONFIG.get("sound_effects", True):
        return

    def _tone():
        try:
            if kind == "start":
                winsound.Beep(840, 95)
                winsound.Beep(1120, 110)
            elif kind == "stop":
                winsound.Beep(740, 100)
                winsound.Beep(520, 130)
            elif kind == "error":
                winsound.Beep(300, 200)
        except Exception:
            pass

    threading.Thread(target=_tone, daemon=True).start()


def create_icon_image(color):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 56, 56), fill=color)
    return img


def update_hud(text, bg="#18181B", fg="#F4F4F5", stay_open=False, auto_ms=2200):
    def _apply():
        global hud_label, hud_frame
        if not main_gui_win or not main_gui_win.winfo_exists():
            return
        try:
            if not hud_frame or not hud_frame.winfo_exists():
                hud_frame = tk.Toplevel(main_gui_win)
                hud_frame.overrideredirect(True)
                hud_frame.attributes("-topmost", True)
                sw = hud_frame.winfo_screenwidth()
                hud_frame.geometry(f"290x46+{max(10, sw - 310)}+24")
                hud_label = tk.Label(hud_frame, font=("Segoe UI", 9, "bold"), padx=10, pady=8, wraplength=270)
                hud_label.pack(fill="both", expand=True)

            hud_frame.configure(bg=bg)
            hud_label.configure(text=text, bg=bg, fg=fg)
            hud_frame.deiconify()

            if hasattr(hud_frame, "_hide_job") and hud_frame._hide_job:
                hud_frame.after_cancel(hud_frame._hide_job)
                hud_frame._hide_job = None

            if not stay_open and auto_ms:
                hud_frame._hide_job = hud_frame.after(auto_ms, hud_frame.withdraw)
        except Exception:
            pass

    if main_gui_win and main_gui_win.winfo_exists():
        try:
            main_gui_win.after(0, _apply)
        except Exception:
            pass


def get_audio_devices(backend=None):
    api = (backend or CONFIG.get("audio_backend", "wasapi")).lower()
    devices = []
    try:
        if api != "dshow":
            devices.append("default")
        res = subprocess.run(
            ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        for line in (res.stderr or "").splitlines():
            if "(audio)" in line.lower() and '"' in line:
                m = re.search(r'"([^"]+)"', line)
                if m and m.group(1).strip() not in devices:
                    devices.append(m.group(1).strip())
    except Exception:
        pass
    return devices


def get_fps_value():
    mode = str(CONFIG.get("fps_mode", "30")).strip()
    if mode in ("Custom", "Personalizado"):
        try:
            return max(1, min(240, int(CONFIG.get("custom_fps", 30))))
        except Exception:
            return 30
    try:
        return max(1, min(240, int(mode)))
    except Exception:
        return 30


def even_dim(val, fallback):
    try:
        n = int(val)
    except Exception:
        n = fallback
    n = max(320, n)
    return n - (n % 2)


def get_resolution_and_bitrate():
    mode = str(CONFIG.get("resolution_mode", "1280x720 (HD)")).strip()
    q = normalize_quality(CONFIG.get("quality", "medium"))

    if q == "low":
        bitrate = ["-b:v", "2200k", "-maxrate", "2600k", "-bufsize", "4000k"]
    elif q == "high":
        bitrate = ["-b:v", "7500k", "-maxrate", "9500k", "-bufsize", "15000k"]
    else:
        bitrate = ["-b:v", "4200k", "-maxrate", "5200k", "-bufsize", "8500k"]

    w, h = None, None
    if "1280x720" in mode:
        w, h = 1280, 720
    elif "1366x768" in mode:
        w, h = 1366, 768
    elif "1920x1080" in mode:
        w, h = 1920, 1080
    elif mode in ("Custom", "Personalizada"):
        w = even_dim(CONFIG.get("custom_width", 1280), 1280)
        h = even_dim(CONFIG.get("custom_height", 720), 720)

    vf_args = ["-vf", f"scale={w}:{h}:flags=fast_bilinear"] if (w and h) else []
    return vf_args + bitrate


def get_monitor_args():
    try:
        mon = max(1, int(CONFIG.get("monitor_index", 1)))
    except Exception:
        mon = 1

    if mon <= 1:
        return []

    try:
        sw = main_gui_win.winfo_screenwidth() if main_gui_win else 1920
        sh = main_gui_win.winfo_screenheight() if main_gui_win else 1080
    except Exception:
        sw, sh = 1920, 1080

    offset_x = (mon - 1) * sw
    return ["-offset_x", str(offset_x), "-offset_y", "0", "-video_size", f"{sw}x{sh}"]


def append_audio_input(cmd, api, dev_name, is_system=False):
    clean_name = (dev_name or "").strip() or "default"
    if api == "dshow":
        cmd += ["-thread_queue_size", "512", "-f", "dshow", "-i", f"audio={clean_name}"]
    else:
        if is_system and clean_name.lower() == "default":
            cmd += ["-thread_queue_size", "512", "-f", "wasapi", "-loopback", "1", "-i", "default"]
        elif is_system:
            cmd += ["-thread_queue_size", "512", "-f", "wasapi", "-loopback", "1", "-i", clean_name]
        else:
            cmd += ["-thread_queue_size", "512", "-f", "wasapi", "-i", clean_name]


def build_ffmpeg_command(output_path):
    fps = str(get_fps_value())
    cmd = [
        "ffmpeg",
        "-y",
        "-thread_queue_size", "512",
        "-f", "gdigrab",
        "-framerate", fps,
        "-draw_mouse", "1",
    ]
    cmd += get_monitor_args()
    cmd += ["-i", "desktop"]

    api = str(CONFIG.get("audio_backend", "wasapi")).lower()
    audio_streams = []
    input_idx = 1

    if bool(CONFIG.get("system_audio_enabled", False)):
        sys_dev = (CONFIG.get("system_audio_device", "") or "").strip() or "default"
        append_audio_input(cmd, api, sys_dev, is_system=True)
        vol = max(0.0, min(5.0, float(CONFIG.get("system_volume", 150)) / 100.0))
        audio_streams.append((input_idx, vol))
        input_idx += 1

    if bool(CONFIG.get("mic_enabled", False)):
        mic_dev = (CONFIG.get("mic_device", "") or "").strip() or "default"
        append_audio_input(cmd, api, mic_dev, is_system=False)
        vol = max(0.0, min(5.0, float(CONFIG.get("mic_volume", 120)) / 100.0))
        audio_streams.append((input_idx, vol))
        input_idx += 1

    if CONFIG.get("use_qsv"):
        cmd += ["-c:v", "h264_qsv", "-preset", "veryfast"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "ultrafast"]

    cmd += get_resolution_and_bitrate()
    cmd += ["-pix_fmt", "yuv420p"]

    if len(audio_streams) == 2:
        idx1, vol1 = audio_streams[0]
        idx2, vol2 = audio_streams[1]
        fc = (
            f"[{idx1}:a]volume={vol1:.2f}[a1];"
            f"[{idx2}:a]volume={vol2:.2f}[a2];"
            f"[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    elif len(audio_streams) == 1:
        idx1, vol1 = audio_streams[0]
        cmd += ["-af", f"volume={vol1:.2f}", "-map", "0:v", "-map", f"{idx1}:a", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-map", "0:v"]

    cmd.append(output_path)
    return cmd


def sync_ui_state():
    def _update():
        try:
            if gui_status_var:
                if is_recording:
                    gui_status_var.set(f"● {t('recording')} ({CONFIG['hotkey'].upper()})")
                else:
                    gui_status_var.set(f"{t('ready')} · {CONFIG['hotkey'].upper()}")
            if gui_record_btn:
                gui_record_btn.config(
                    text=t("stop_btn") if is_recording else t("start_btn"),
                    bg="#B91C1C" if is_recording else "#15803D",
                    fg="#FFFFFF"
                )
        except Exception:
            pass

    if main_gui_win and main_gui_win.winfo_exists():
        try:
            main_gui_win.after(0, _update)
        except Exception:
            pass


def start_recording():
    global ffmpeg_process, current_output_path, is_recording
    if hotkey_paused:
        return

    with state_lock:
        if is_recording or ffmpeg_process is not None:
            return

        os.makedirs(CONFIG["output_folder"], exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = os.path.join(CONFIG["output_folder"], f"clip_{timestamp}.mp4")
        current_output_path = output_path

        cmd = build_ffmpeg_command(output_path)
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        try:
            log_handle = open(LOG_FILE, "w", encoding="utf-8", errors="ignore")
            ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=log_handle,
                creationflags=creation_flags
            )
            ffmpeg_process._log_handle = log_handle
            is_recording = True
            if tray_icon:
                tray_icon.icon = create_icon_image("#DC2626")
            sync_ui_state()
            play_cue("start")
            update_hud(f"● {t('hud_rec')} ({CONFIG['hotkey'].upper()})", bg="#7F1D1D", stay_open=True)
        except Exception as e:
            is_recording = False
            ffmpeg_process = None
            sync_ui_state()
            play_cue("error")
            update_hud(str(e)[:45], bg="#450A0A", stay_open=False, auto_ms=3000)


def stop_recording():
    global ffmpeg_process, current_output_path, is_recording
    with state_lock:
        if not is_recording and ffmpeg_process is None:
            return

        proc = ffmpeg_process
        out_path = current_output_path
        ffmpeg_process = None
        current_output_path = None
        is_recording = False

        if proc:
            try:
                if proc.stdin:
                    try:
                        proc.stdin.write(b"q\n")
                        proc.stdin.flush()
                    except Exception:
                        pass
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            finally:
                try:
                    if hasattr(proc, "_log_handle") and proc._log_handle:
                        proc._log_handle.close()
                except Exception:
                    pass

        if tray_icon:
            tray_icon.icon = create_icon_image("#16A34A")
        sync_ui_state()

        has_valid_file = bool(out_path and os.path.exists(out_path) and os.path.getsize(out_path) > 1024)
        if has_valid_file:
            play_cue("stop")
            update_hud(t("clip_saved"), bg="#14532D", stay_open=False, auto_ms=2200)
        else:
            if out_path and os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except Exception:
                    pass
            play_cue("error")
            update_hud(t("ffmpeg_err"), bg="#7F1D1D", stay_open=False, auto_ms=4000)


def toggle_recording():
    if hotkey_paused:
        return
    if not is_recording:
        start_recording()
    else:
        stop_recording()


def apply_hotkey():
    try:
        keyboard.unhook_all()
        hk = CONFIG.get("hotkey", "f9").strip().lower() or "f9"
        CONFIG["hotkey"] = hk
        keyboard.add_hotkey(hk, toggle_recording, suppress=False)
    except Exception:
        pass


def exit_app_completely():
    if is_recording:
        stop_recording()
    try:
        keyboard.unhook_all()
    except Exception:
        pass
    try:
        if tray_icon:
            tray_icon.stop()
    except Exception:
        pass
    os._exit(0)


def get_theme_display_map():
    lang = CONFIG.get("language", "en")
    names = THEME_NAMES.get(lang, THEME_NAMES["en"])
    return {v: k for k, v in names.items()}, {k: v for k, v in names.items()}


def build_and_run_gui():
    global main_gui_win, gui_status_var, gui_record_btn, hotkey_paused

    win = tk.Tk()
    main_gui_win = win
    win.title(t("title"))
    win.geometry("485x580")
    win.resizable(False, False)

    style = ttk.Style(win)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    top_bar = tk.Frame(win, padx=14, pady=10)
    top_bar.pack(fill="x")

    brand_lbl = tk.Label(top_bar, text="LiteClip", font=("Segoe UI", 12, "bold"))
    brand_lbl.pack(side="left")

    gui_status_var = tk.StringVar(value=f"{t('ready')} · {CONFIG['hotkey'].upper()}")
    status_lbl = tk.Label(top_bar, textvariable=gui_status_var, font=("Segoe UI", 9))
    status_lbl.pack(side="right")

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True, padx=12, pady=(0, 8))

    # --- Tab 1: Capture ---
    tab_cap = ttk.Frame(notebook, padding=14)
    notebook.add(tab_cap, text=t("tab_capture"))

    lbl_hk = ttk.Label(tab_cap, text=t("hotkey_label"))
    lbl_hk.pack(anchor="w")
    hotkey_var = tk.StringVar(value=CONFIG.get("hotkey", "f9"))
    hk_entry = tk.Entry(tab_cap, textvariable=hotkey_var, relief="flat")
    hk_entry.pack(fill="x", pady=(3, 10), ipady=3)

    def _pause_hk(event=None):
        global hotkey_paused
        hotkey_paused = True

    def _resume_hk(event=None):
        global hotkey_paused
        hotkey_paused = False

    hk_entry.bind("<FocusIn>", _pause_hk)
    hk_entry.bind("<FocusOut>", _resume_hk)

    row1 = tk.Frame(tab_cap)
    row1.pack(fill="x", pady=(0, 10))

    c_mon = tk.Frame(row1)
    c_mon.pack(side="left", fill="x", expand=True, padx=(0, 6))
    lbl_mon = ttk.Label(c_mon, text=t("monitor_label"))
    lbl_mon.pack(anchor="w")
    mon_var = tk.StringVar(value=str(CONFIG.get("monitor_index", 1)))
    ttk.Combobox(c_mon, textvariable=mon_var, values=["1", "2", "3"], state="readonly").pack(fill="x", pady=(3, 0))

    c_qual = tk.Frame(row1)
    c_qual.pack(side="left", fill="x", expand=True, padx=(6, 0))
    lbl_qual = ttk.Label(c_qual, text=t("quality_label"))
    lbl_qual.pack(anchor="w")
    _, key_to_qual_label = get_quality_maps()
    qual_var = tk.StringVar()
    qual_combo = ttk.Combobox(c_qual, textvariable=qual_var, values=list(key_to_qual_label.values()), state="readonly")
    qual_combo.set(key_to_qual_label.get(normalize_quality(CONFIG.get("quality", "medium")), key_to_qual_label["medium"]))
    qual_combo.pack(fill="x", pady=(3, 0))

    lbl_res = ttk.Label(tab_cap, text=t("res_label"))
    lbl_res.pack(anchor="w")
    res_choices = ["1280x720 (HD)", "1366x768 (HD+)", "1920x1080 (FHD)", "Custom"]
    res_var = tk.StringVar(value=CONFIG.get("resolution_mode", res_choices[0]))
    ttk.Combobox(tab_cap, textvariable=res_var, values=res_choices, state="readonly").pack(fill="x", pady=(3, 6))

    res_custom_row = tk.Frame(tab_cap)
    res_custom_row.pack(fill="x", pady=(0, 10))
    w_var = tk.StringVar(value=str(CONFIG.get("custom_width", 1280)))
    h_var = tk.StringVar(value=str(CONFIG.get("custom_height", 720)))
    lbl_w = ttk.Label(res_custom_row, text="W:")
    lbl_w.pack(side="left")
    w_entry = tk.Entry(res_custom_row, textvariable=w_var, width=6, relief="flat")
    w_entry.pack(side="left", padx=(3, 10))
    lbl_h = ttk.Label(res_custom_row, text="H:")
    lbl_h.pack(side="left")
    h_entry = tk.Entry(res_custom_row, textvariable=h_var, width=6, relief="flat")
    h_entry.pack(side="left", padx=(3, 0))

    lbl_fps = ttk.Label(tab_cap, text=t("fps_label"))
    lbl_fps.pack(anchor="w")
    fps_row = tk.Frame(tab_cap)
    fps_row.pack(fill="x", pady=(3, 10))
    fps_var = tk.StringVar(value=str(CONFIG.get("fps_mode", "30")))
    ttk.Combobox(fps_row, textvariable=fps_var, values=["24", "30", "60", "Custom"], state="readonly", width=12).pack(side="left")
    lbl_cfps = ttk.Label(fps_row, text=t("custom_fps_label"))
    lbl_cfps.pack(side="left", padx=(10, 4))
    cfps_var = tk.StringVar(value=str(CONFIG.get("custom_fps", 30)))
    cfps_entry = tk.Entry(fps_row, textvariable=cfps_var, width=6, relief="flat")
    cfps_entry.pack(side="left")

    qsv_var = tk.BooleanVar(value=CONFIG.get("use_qsv", False))
    cb_qsv = ttk.Checkbutton(tab_cap, text=t("qsv_label"), variable=qsv_var)
    cb_qsv.pack(anchor="w")

    # --- Tab 2: Audio ---
    tab_aud = ttk.Frame(notebook, padding=14)
    notebook.add(tab_aud, text=t("tab_audio"))

    lbl_api = ttk.Label(tab_aud, text=t("audio_backend_label"))
    lbl_api.pack(anchor="w")
    api_var = tk.StringVar(value=CONFIG.get("audio_backend", "wasapi"))
    api_combo = ttk.Combobox(tab_aud, textvariable=api_var, values=["wasapi", "dshow"], state="readonly")
    api_combo.pack(fill="x", pady=(3, 10))

    devices = get_audio_devices(api_var.get())

    sys_en_var = tk.BooleanVar(value=CONFIG.get("system_audio_enabled", False))
    sys_dev_var = tk.StringVar(value=CONFIG.get("system_audio_device", "default"))
    sys_vol_var = tk.StringVar(value=str(CONFIG.get("system_volume", 150)))

    mic_en_var = tk.BooleanVar(value=CONFIG.get("mic_enabled", False))
    mic_dev_var = tk.StringVar(value=CONFIG.get("mic_device", "default"))
    mic_vol_var = tk.StringVar(value=str(CONFIG.get("mic_volume", 120)))

    cb_sys = ttk.Checkbutton(tab_aud, text=t("sys_audio"), variable=sys_en_var)
    cb_sys.pack(anchor="w")
    sys_combo = ttk.Combobox(tab_aud, textvariable=sys_dev_var, values=devices, state="readonly")
    sys_combo.pack(fill="x", pady=(3, 6))

    sys_vol_row = tk.Frame(tab_aud)
    sys_vol_row.pack(fill="x", pady=(0, 12))
    lbl_svol = ttk.Label(sys_vol_row, text=t("sys_vol"))
    lbl_svol.pack(side="left")
    svol_entry = tk.Entry(sys_vol_row, textvariable=sys_vol_var, width=6, relief="flat")
    svol_entry.pack(side="left", padx=6)

    cb_mic = ttk.Checkbutton(tab_aud, text=t("mic_audio"), variable=mic_en_var)
    cb_mic.pack(anchor="w")
    mic_combo = ttk.Combobox(tab_aud, textvariable=mic_dev_var, values=devices, state="readonly")
    mic_combo.pack(fill="x", pady=(3, 6))

    mic_vol_row = tk.Frame(tab_aud)
    mic_vol_row.pack(fill="x", pady=(0, 12))
    lbl_mvol = ttk.Label(mic_vol_row, text=t("mic_vol"))
    lbl_mvol.pack(side="left")
    mvol_entry = tk.Entry(mic_vol_row, textvariable=mic_vol_var, width=6, relief="flat")
    mvol_entry.pack(side="left", padx=6)

    def refresh_audio(event=None):
        found = get_audio_devices(api_var.get())
        sys_combo["values"] = found
        mic_combo["values"] = found
        if not found:
            messagebox.showwarning("LiteClip", t("no_audio_found"))
        elif event is None:
            messagebox.showinfo("LiteClip", t("devices_found").format(count=len(found)))

    api_combo.bind("<<ComboboxSelected>>", refresh_audio)
    detect_btn = tk.Button(tab_aud, text=t("detect_btn"), command=refresh_audio, relief="flat", padx=10, pady=5)
    detect_btn.pack(anchor="w")

    # --- Tab 3: Interface ---
    tab_ui = ttk.Frame(notebook, padding=14)
    notebook.add(tab_ui, text=t("tab_ui"))

    lbl_lang = ttk.Label(tab_ui, text=t("lang_label"))
    lbl_lang.pack(anchor="w")
    lang_combo = ttk.Combobox(tab_ui, values=list(LANG_NAMES.keys()), state="readonly")
    lang_combo.set(LANG_CODES_TO_NAME.get(CONFIG.get("language", "en"), "English"))
    lang_combo.pack(fill="x", pady=(3, 10))

    lbl_theme = ttk.Label(tab_ui, text=t("theme_label"))
    lbl_theme.pack(anchor="w")
    _, key_to_theme_label = get_theme_display_map()
    theme_combo = ttk.Combobox(tab_ui, values=list(key_to_theme_label.values()), state="readonly")
    theme_combo.set(key_to_theme_label.get(CONFIG.get("theme", "dark"), key_to_theme_label["dark"]))
    theme_combo.pack(fill="x", pady=(3, 12))

    snd_var = tk.BooleanVar(value=CONFIG.get("sound_effects", True))
    cb_snd = ttk.Checkbutton(tab_ui, text=t("sound_label"), variable=snd_var)
    cb_snd.pack(anchor="w", pady=(0, 8))

    bg_var = tk.BooleanVar(value=CONFIG.get("run_in_background", True))
    cb_bg = ttk.Checkbutton(tab_ui, text=t("bg_label"), variable=bg_var)
    cb_bg.pack(anchor="w")

    # --- Bottom bar ---
    bottom = tk.Frame(win, padx=12, pady=10)
    bottom.pack(fill="x")

    entries = [hk_entry, w_entry, h_entry, cfps_entry, svol_entry, mvol_entry]
    tk_frames = [top_bar, row1, c_mon, c_qual, res_custom_row, fps_row, sys_vol_row, mic_vol_row, bottom]

    def apply_theme_and_texts():
        p = get_theme_palette()
        win.configure(bg=p["bg"])
        win.title(t("title"))

        style.configure("TNotebook", background=p["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=p["panel"], foreground=p["fg"], padding=[12, 6], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", p["btn"])], foreground=[("selected", p["fg"])])
        style.configure("TFrame", background=p["panel"])
        style.configure("TLabel", background=p["panel"], foreground=p["fg"], font=("Segoe UI", 9))
        style.configure("TCheckbutton", background=p["panel"], foreground=p["fg"], font=("Segoe UI", 9))

        for fr in tk_frames:
            fr.configure(bg=p["bg"] if fr in (top_bar, bottom) else p["panel"])

        brand_lbl.configure(bg=p["bg"], fg=p["fg"])
        status_lbl.configure(bg=p["bg"], fg=p["muted"])

        for ent in entries:
            ent.configure(bg=p["input_bg"], fg=p["fg"], insertbackground=p["fg"])

        for b in (detect_btn, clips_btn, save_btn):
            b.configure(bg=p["btn"], fg=p["fg"])

        notebook.tab(0, text=t("tab_capture"))
        notebook.tab(1, text=t("tab_audio"))
        notebook.tab(2, text=t("tab_ui"))
        lbl_hk.config(text=t("hotkey_label"))
        lbl_mon.config(text=t("monitor_label"))
        lbl_qual.config(text=t("quality_label"))
        lbl_res.config(text=t("res_label"))
        lbl_fps.config(text=t("fps_label"))
        lbl_cfps.config(text=t("custom_fps_label"))
        cb_qsv.config(text=t("qsv_label"))
        lbl_api.config(text=t("audio_backend_label"))
        cb_sys.config(text=t("sys_audio"))
        lbl_svol.config(text=t("sys_vol"))
        cb_mic.config(text=t("mic_audio"))
        lbl_mvol.config(text=t("mic_vol"))
        detect_btn.config(text=t("detect_btn"))
        lbl_lang.config(text=t("lang_label"))
        lbl_theme.config(text=t("theme_label"))
        cb_snd.config(text=t("sound_label"))
        cb_bg.config(text=t("bg_label"))
        clips_btn.config(text=t("clips_btn"))
        save_btn.config(text=t("save_btn"))

        _, q_map = get_quality_maps()
        qual_combo["values"] = list(q_map.values())
        qual_combo.set(q_map.get(normalize_quality(CONFIG.get("quality", "medium")), q_map["medium"]))

        _, t_map = get_theme_display_map()
        theme_combo["values"] = list(t_map.values())
        theme_combo.set(t_map.get(CONFIG.get("theme", "dark"), t_map["dark"]))
        sync_ui_state()

    def on_save():
        global hotkey_paused
        hotkey_paused = False
        try:
            cw = even_dim(w_var.get(), 1280)
            ch = even_dim(h_var.get(), 720)
            cfps = max(1, min(240, int(cfps_var.get())))
            mon_i = max(1, int(mon_var.get()))
            svol = max(0, min(500, int(sys_vol_var.get())))
            mvol = max(0, min(500, int(mic_vol_var.get())))
        except ValueError:
            messagebox.showerror("LiteClip", t("invalid_nums"))
            return

        CONFIG["language"] = LANG_NAMES.get(lang_combo.get(), "en")
        theme_to_key, _ = get_theme_display_map()
        CONFIG["theme"] = theme_to_key.get(theme_combo.get(), CONFIG.get("theme", "dark"))

        qual_to_key, _ = get_quality_maps()
        CONFIG["quality"] = qual_to_key.get(qual_combo.get(), normalize_quality(qual_combo.get()))

        raw_hk = hotkey_var.get().strip().lower()
        CONFIG["hotkey"] = raw_hk if raw_hk else "f9"
        CONFIG["monitor_index"] = mon_i
        CONFIG["resolution_mode"] = res_var.get()
        CONFIG["custom_width"] = cw
        CONFIG["custom_height"] = ch
        w_var.set(str(cw))
        h_var.set(str(ch))
        CONFIG["fps_mode"] = fps_var.get()
        CONFIG["custom_fps"] = cfps
        CONFIG["use_qsv"] = qsv_var.get()
        CONFIG["sound_effects"] = snd_var.get()
        CONFIG["run_in_background"] = bg_var.get()
        CONFIG["audio_backend"] = api_var.get()
        CONFIG["system_audio_enabled"] = bool(sys_en_var.get())
        CONFIG["system_audio_device"] = sys_dev_var.get() if sys_en_var.get() else ""
        CONFIG["system_volume"] = svol
        CONFIG["mic_enabled"] = bool(mic_en_var.get())
        CONFIG["mic_device"] = mic_dev_var.get() if mic_en_var.get() else ""
        CONFIG["mic_volume"] = mvol
        save_config(CONFIG)

        apply_hotkey()
        apply_theme_and_texts()
        update_hud(t("saved_msg"), bg="#1E293B", stay_open=False, auto_ms=1800)

    gui_record_btn = tk.Button(
        bottom,
        text=t("start_btn"),
        command=toggle_recording,
        bg="#15803D",
        fg="#FFFFFF",
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=10,
        pady=5
    )
    gui_record_btn.pack(side="left")

    clips_btn = tk.Button(
        bottom,
        text=t("clips_btn"),
        command=lambda: os.startfile(os.path.abspath(CONFIG["output_folder"])),
        relief="flat",
        padx=9,
        pady=5
    )
    clips_btn.pack(side="left", padx=6)

    save_btn = tk.Button(
        bottom,
        text=t("save_btn"),
        command=on_save,
        relief="flat",
        font=("Segoe UI", 9, "bold"),
        padx=12,
        pady=5
    )
    save_btn.pack(side="right")

    def on_close():
        global hotkey_paused
        hotkey_paused = False
        if CONFIG.get("run_in_background", True):
            win.withdraw()
        else:
            exit_app_completely()

    win.protocol("WM_DELETE_WINDOW", on_close)
    apply_theme_and_texts()
    win.mainloop()


def show_gui_from_tray():
    if main_gui_win and main_gui_win.winfo_exists():
        try:
            main_gui_win.after(0, lambda: (main_gui_win.deiconify(), main_gui_win.lift(), main_gui_win.focus_force()))
        except Exception:
            pass


def setup_tray():
    global tray_icon
    menu = pystray.Menu(
        pystray.MenuItem(t("tray_open"), lambda icon, item: show_gui_from_tray(), default=True),
        pystray.MenuItem(t("tray_toggle"), lambda icon, item: toggle_recording()),
        pystray.MenuItem(t("tray_clips"), lambda icon, item: os.startfile(os.path.abspath(CONFIG["output_folder"]))),
        pystray.MenuItem(t("tray_exit"), lambda icon, item: exit_app_completely())
    )
    tray_icon = pystray.Icon(
        "LiteClip",
        create_icon_image("#16A34A"),
        "LiteClip",
        menu
    )
    tray_icon.run()


if __name__ == "__main__":
    apply_hotkey()
    threading.Thread(target=setup_tray, daemon=True).start()
    build_and_run_gui()