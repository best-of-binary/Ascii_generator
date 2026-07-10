#!/usr/bin/env python3
import sys
import os
import time
import shutil
import subprocess
import multiprocessing as mp
import cv2
import numpy as np

CONFIG = {
    "GRID_SIZE": 25,
    "FONT_SCALE": 1.3,
    "THICKNESS": 1,
    "SUPERSAMPLE": 4,
    "ASCII_CHARS": "  .,:;i1tfLCG08@",
    "GAMMA": 1.0,
    "GLYPH_COLOUR": [255, 255, 255],
    "CLAHE_CLIP_LIMIT": 2.0,
    "CLAHE_TILE_SIZE": 4,
    "N_WORKERS_CAP": 8,
    "CRF": 15,
    "PRESET": "slow",
    "MAXRATE_MBPS": 24,
    "BUFSIZE_MBPS": 48,
    "OUTPUT_DIR": "/storage/emulated/0/ASCII/OUTPUT",
}

AUTHOR = "@best_of_binary"
INSTAGRAM_URL = "https://www.instagram.com/best_of_binary"
GITHUB_URL = "https://github.com/best-of-binary/"

def _supports_color():
    if os.environ.get("NO_COLOR"): return False
    try: return sys.stdout.isatty()
    except Exception: return False

class C:
    _on = _supports_color()
    RESET = "\033[0m" if _on else ""
    BOLD = "\033[1m" if _on else ""
    DIM = "\033[2m" if _on else ""
    RED = "\033[31m" if _on else ""
    GREEN = "\033[32m" if _on else ""
    YELLOW = "\033[33m" if _on else ""
    CYAN = "\033[36m" if _on else ""
    B_GREEN = "\033[92m" if _on else ""
    B_CYAN = "\033[96m" if _on else ""
    B_MAGENTA = "\033[95m" if _on else ""
    B_YELLOW = "\033[93m" if _on else ""
    B_RED = "\033[91m" if _on else ""

def get_term_size():
    try:
        cols, rows = os.get_terminal_size(sys.stdout.fileno())
        return cols, rows
    except:
        return 60, 24

def box_width():
    cols, _ = get_term_size()
    return max(32, min(cols - 2, 78))

def clear_screen():
    sys.stdout.write("\033[H\033[2J\033[3J")
    sys.stdout.flush()

def hyperlink(url, text=None):
    text = text or url
    if not C._on: return f"{text} ({url})"
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

def _visible_len(s):
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] == "\033":
            j, k = s.find("\\", i), s.find("m", i)
            end = min(x for x in (j, k) if x != -1) if (j != -1 or k != -1) else -1
            if end == -1: break
            i = end + 1
        else:
            out.append(s[i])
            i += 1
    return len(out)

def print_box(lines, title=None, color=C.CYAN):
    w = box_width()
    inner = w - 2
    print(f"{color}┌{'─' * inner}┐{C.RESET}")
    if title:
        t = f" {title} "
        pad = max(0, inner - len(t))
        left = pad // 2
        right = pad - left
        print(f"{color}│{C.RESET}{' ' * left}{C.BOLD}{t}{C.RESET}{' ' * right}{color}│{C.RESET}")
        print(f"{color}├{'─' * inner}┤{C.RESET}")
    for line in lines:
        vis = _visible_len(line)
        pad = max(0, inner - vis - 2)
        print(f"{color}│{C.RESET}  {line}{' ' * pad}{color}│{C.RESET}")
    print(f"{color}└{'─' * inner}┘{C.RESET}")

def print_banner():
    w = box_width()
    title = "A S C I I   V I D E O   C O N V E R T E R"
    print(f"{C.B_MAGENTA}{'═' * w}{C.RESET}")
    pad = max(0, (w - len(title)) // 2)
    print(f"{C.B_CYAN}{C.BOLD}{' ' * pad}{title}{C.RESET}")
    sub = f"by {AUTHOR}"
    pad2 = max(0, (w - len(sub)) // 2)
    print(f"{C.DIM}{' ' * pad2}{sub}{C.RESET}")
    print(f"{C.B_MAGENTA}{'═' * w}{C.RESET}")

def pause(msg="Press Enter to continue..."):
    try: input(f"{C.DIM}{msg}{C.RESET}")
    except (EOFError, KeyboardInterrupt): pass

def prompt(msg):
    try: return input(f"{C.B_YELLOW} > {msg}{C.RESET}").strip()
    except (EOFError, KeyboardInterrupt): return ""

def get_cpu_cores():
    try:
        with open("/proc/cpuinfo") as f:
            return sum(1 for line in f if line.startswith("processor"))
    except Exception:
        return os.cpu_count() or 4

def run_ffmpeg_with_progress(cmd, duration_s, label):
    full_cmd = cmd[:-1] + ["-progress", "pipe:1", "-nostats"] + [cmd[-1]]
    process = subprocess.Popen(full_cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1)
    last_percent = -1
    out_time_s = 0.0
    bar_len = 30

    while True:
        line = process.stdout.readline()
        if not line:
            if process.poll() is not None: break
            continue
        line = line.strip()

        if line.startswith("out_time_ms="):
            try: out_time_s = int(line.split("=")[1]) / 1_000_000
            except Exception: pass
        elif line.startswith("out_time="):
            try:
                h, m, s = line.split("=")[1].split(":")
                out_time_s = int(h) * 3600 + int(m) * 60 + float(s)
            except Exception: pass
        elif line == "progress=end":
            out_time_s = duration_s

        percent = min(100, int(out_time_s / duration_s * 100)) if duration_s > 0 else 0
        if percent != last_percent:
            last_percent = percent
            filled = int(bar_len * percent / 100)
            bar = "#" * filled + "-" * (bar_len - filled)
            sys.stdout.write(f"\r{C.B_CYAN}{label} [{bar}] {percent}%{C.RESET}")
            sys.stdout.flush()

        if line == "progress=end": break

    stderr_output = process.stderr.read()
    process.wait()
    print()
    return process.returncode, stderr_output

def get_optimal_grid(ascii_chars, font_scale, thickness):
    """Calculates the tightest bounding box for the given font scale."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    max_w, max_h = 0, 0
    for ch in ascii_chars:
        if ch == ' ': continue
        (tw, th), baseline = cv2.getTextSize(ch, font, font_scale, thickness)
        max_w = max(max_w, tw)
        max_h = max(max_h, th + baseline)
    return max(1, max_w + 1), max(1, max_h + 1)

def build_glyph_bank(ascii_chars, grid_w, grid_h, font_scale, thickness, supersample):
    font = cv2.FONT_HERSHEY_SIMPLEX
    n_chars = len(ascii_chars)
    hi_w = grid_w * supersample
    hi_h = grid_h * supersample

    glyphs = np.zeros((n_chars, grid_h, grid_w), dtype=np.uint8)
    for idx, ch in enumerate(ascii_chars):
        if ch == ' ':
            continue
        hi_tile = np.zeros((hi_h, hi_w), dtype=np.uint8)
        
        hi_font_scale = font_scale * supersample 
        hi_thickness = max(1, thickness * supersample)

        (tw, th), baseline = cv2.getTextSize(ch, font, hi_font_scale, hi_thickness)
        
        tx = max(0, (hi_w - tw) // 2)
        ty = min(hi_h - 1, (hi_h + th) // 2)

        cv2.putText(hi_tile, ch, (tx, ty), font, hi_font_scale, 255,
                    hi_thickness, lineType=cv2.LINE_AA)

        glyphs[idx] = cv2.resize(hi_tile, (grid_w, grid_h), interpolation=cv2.INTER_AREA)

    return glyphs

def process_chunk(chunk_id, start_frame, end_frame, input_path,
                   width, height, cols, rows, grid_w, grid_h, fps,
                   font_scale, thickness, ascii_chars, gamma, glyph_colour,
                   clahe_clip_limit, clahe_tile_size, supersample,
                   raw_chunk_path, progress_queue):

    n_chars = len(ascii_chars)
    lut = np.array([min(255, int((i / 255.0) ** gamma * 255)) for i in range(256)], dtype=np.uint8)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_tile_size, clahe_tile_size))

    glyphs = build_glyph_bank(ascii_chars, grid_w, grid_h, font_scale, thickness, supersample)

    cap = cv2.VideoCapture(input_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    raw_chunk_path = os.path.splitext(raw_chunk_path)[0] + ".avi"
    fourcc = cv2.VideoWriter_fourcc(*'HFYU')
    out = cv2.VideoWriter(raw_chunk_path, fourcc, fps, (width, height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(raw_chunk_path, fourcc, fps, (width, height))

    gw, gh = cols * grid_w, rows * grid_h
    canvas = np.zeros((height, width), dtype=np.uint8)

    drawn, skipped = 0, 0
    frame_idx = start_frame

    while frame_idx < end_frame:
        ret, frame = cap.read()
        if not ret: break

        small = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = clahe.apply(gray)
        gray = cv2.LUT(gray, lut)
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

        char_index = (gray.astype(np.float32) / 255.0 * n_chars).astype(np.int32)
        np.clip(char_index, 0, n_chars - 1, out=char_index)

        tiles = glyphs[char_index]
        canvas[:gh, :gw] = tiles.transpose(0, 2, 1, 3).reshape(gh, gw)

        frame_bgr = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
        if tuple(glyph_colour) != (255, 255, 255):
            mask = canvas > 0
            for c in range(3): frame_bgr[:, :, c][mask] = glyph_colour[c]

        out.write(frame_bgr)
        blank_mask = (char_index == 0)
        sk = int(np.count_nonzero(blank_mask))
        skipped += sk
        drawn += cols * rows - sk

        frame_idx += 1
        progress_queue.put(("progress", chunk_id, 1))

    cap.release()
    out.release()
    progress_queue.put(("done", chunk_id, drawn, skipped, raw_chunk_path))

def run_conversion():
    temp_input = os.path.join(os.path.expanduser("~"), "_ascii_input_tmp.mp4")
    if os.path.exists(temp_input):
        os.remove(temp_input)

    print(f"\n{C.CYAN}Opening Android file picker... select your video.{C.RESET}")
    picker = subprocess.run(["termux-storage-get", temp_input])
    if picker.returncode != 0:
        print(f"{C.B_RED}File picker canceled.{C.RESET}")
        pause()
        return

    max_wait, poll, waited, last_size = 30, 0.5, 0, -1
    while waited < max_wait:
        if os.path.exists(temp_input):
            size = os.path.getsize(temp_input)
            if size > 0 and size == last_size: break
            last_size = size
        time.sleep(poll)
        waited += poll

    if not os.path.exists(temp_input) or os.path.getsize(temp_input) == 0:
        print(f"{C.B_RED}No video file selected.{C.RESET}")
        pause()
        return

    os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
    clear_screen()
    print_banner()
    print_box(["File loaded. Ready to convert."], title="PROCESSING CORE", color=C.B_GREEN)

    custom_name = prompt("Enter output name (without extension): ")
    if not custom_name:
        custom_name = f"ascii_render_{int(time.time())}"
    if custom_name.lower().endswith(".mp4"):
        custom_name = custom_name[:-4]

    output_path = os.path.join(CONFIG["OUTPUT_DIR"], f"{custom_name}.mp4")
    input_path = temp_input

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_s = total_frames / fps if fps > 0 else 0
    cap.release()

    opt_w, opt_h = get_optimal_grid(CONFIG["ASCII_CHARS"], CONFIG["FONT_SCALE"], CONFIG["THICKNESS"])
    
    # Use GRID_SIZE for width, but scale height to maintain optimal font aspect ratio
    grid_w = CONFIG["GRID_SIZE"]
    aspect_ratio = opt_h / opt_w if opt_w > 0 else 2.0
    grid_h = max(1, int(grid_w * aspect_ratio))
    
    cols = max(1, width // grid_w)
    rows = max(1, height // grid_h)
    cpu_cores = get_cpu_cores()

    n_workers = max(1, min(cpu_cores, CONFIG["N_WORKERS_CAP"]))
    n_workers = min(n_workers, total_frames) if total_frames > 0 else 1

    chunk_dir = os.path.join(os.path.expanduser("~"), "_ascii_chunks")
    shutil.rmtree(chunk_dir, ignore_errors=True)
    os.makedirs(chunk_dir, exist_ok=True)

    frames_per_chunk = total_frames // n_workers
    chunk_bounds, start = [], 0
    for w in range(n_workers):
        end = start + frames_per_chunk if w < n_workers - 1 else total_frames
        chunk_bounds.append((start, end))
        start = end

    progress_queue = mp.Queue()
    processes = []
    raw_chunk_paths = [None] * n_workers

    print(f"\n{C.DIM}Spawning {n_workers} worker processes...{C.RESET}")
    for chunk_id, (s, e) in enumerate(chunk_bounds):
        raw_chunk_path = os.path.join(chunk_dir, f"chunk_{chunk_id:03d}.avi")
        p = mp.Process(
            target=process_chunk,
            args=(chunk_id, s, e, input_path, width, height, cols, rows,
                  grid_w, grid_h, fps, CONFIG["FONT_SCALE"], CONFIG["THICKNESS"],
                  CONFIG["ASCII_CHARS"], CONFIG["GAMMA"], CONFIG["GLYPH_COLOUR"],
                  CONFIG["CLAHE_CLIP_LIMIT"], CONFIG["CLAHE_TILE_SIZE"],
                  CONFIG["SUPERSAMPLE"],
                  raw_chunk_path, progress_queue)
        )
        processes.append(p)
        p.start()

    chunk_progress = {i: 0 for i in range(n_workers)}
    chunk_results = {}
    loop_start = time.time()
    last_log_time = 0

    while len(chunk_results) < n_workers:
        try: msg = progress_queue.get(timeout=1.0)
        except Exception: msg = None

        if msg is not None:
            if msg[0] == "progress":
                chunk_progress[msg[1]] += msg[2]
            elif msg[0] == "done":
                chunk_results[msg[1]] = (msg[2], msg[3])
                raw_chunk_paths[msg[1]] = msg[4]

        current_frame = sum(chunk_progress.values())
        now = time.time()
        if now - last_log_time >= 1.0:
            last_log_time = now
            elapsed_s = now - loop_start
            proc_fps = current_frame / elapsed_s if elapsed_s > 0 else 0
            remaining = total_frames - current_frame
            eta_s = remaining / proc_fps if proc_fps > 0 else 0
            eta_str = f"{int(eta_s // 60)}m {int(eta_s % 60)}s"

            sys.stdout.write(
                f"\r{C.B_CYAN}Rendering Frames {current_frame}/{total_frames}  "
                f"ETA {eta_str}  ({proc_fps:.2f}fps){C.RESET}"
            )
            sys.stdout.flush()

    for p in processes: p.join()
    print()

    concat_list_path = os.path.join(chunk_dir, "concat_list.txt")
    with open(concat_list_path, "w") as f:
        for path in raw_chunk_paths: f.write(f"file '{path}'\n")

    raw_merged_path = os.path.join(os.path.expanduser("~"), "_ascii_merged_tmp.avi")
    if os.path.exists(raw_merged_path): os.remove(raw_merged_path)

    run_ffmpeg_with_progress(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
         "-c", "copy", raw_merged_path], duration_s, "Merging Chunks "
    )

    compress_rc, _ = run_ffmpeg_with_progress(
        ["ffmpeg", "-y", "-i", raw_merged_path, "-i", input_path,
         "-c:v", "libx264", "-preset", CONFIG["PRESET"], "-crf", str(CONFIG["CRF"]),
         "-maxrate", f"{CONFIG['MAXRATE_MBPS']}M", "-bufsize", f"{CONFIG['BUFSIZE_MBPS']}M",
         "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0?",
         "-threads", str(cpu_cores),
         "-pix_fmt", "yuv420p", "-shortest", output_path], duration_s, "Compressing    "
    )

    if compress_rc == 0 and os.path.exists(output_path):
        os.remove(raw_merged_path)
        shutil.rmtree(chunk_dir, ignore_errors=True)
        if os.path.exists(temp_input): os.remove(temp_input)
        print_box([f"File successfully saved to:", output_path], title="DONE", color=C.B_GREEN)
    else:
        print_box(["FFmpeg encountered an error during compression."], title="ERROR", color=C.B_RED)
    
    pause()

def settings_menu():
    while True:
        clear_screen()
        print_banner()
        print_box([
            f"{C.B_GREEN}[1]{C.RESET} Grid Size   (current: {CONFIG['GRID_SIZE']})",
            f"{C.B_GREEN}[2]{C.RESET} Font Size   (current: {CONFIG['FONT_SCALE']})",
            f"{C.B_GREEN}[3]{C.RESET} Back",
        ], title="SETTINGS", color=C.B_MAGENTA)

        choice = prompt("Select option: ")
        if choice == "1":
            val = prompt(f"New grid size (8-100, current {CONFIG['GRID_SIZE']}): ")
            try:
                v = int(val)
                if 8 <= v <= 100:
                    CONFIG["GRID_SIZE"] = v
                    print(f"{C.B_GREEN}Grid size updated to {v}{C.RESET}")
            except ValueError: pass
            pause()
        elif choice == "2":
            val = prompt(f"New font size (0.3-3.0, current {CONFIG['FONT_SCALE']}): ")
            try:
                v = float(val)
                if 0.3 <= v <= 3.0:
                    CONFIG["FONT_SCALE"] = v
                    print(f"{C.B_GREEN}Font size updated to {v}{C.RESET}")
            except ValueError: pass
            pause()
        elif choice == "3" or choice == "":
            return

def links_menu():
    while True:
        clear_screen()
        print_banner()
        print_box([
            f"{C.B_GREEN}[1]{C.RESET} Instagram — {hyperlink(INSTAGRAM_URL)}",
            f"{C.B_GREEN}[2]{C.RESET} Patreon   — {hyperlink(PATREON_URL)}",
            f"{C.B_GREEN}[3]{C.RESET} Back",
        ], title="LINKS", color=C.B_MAGENTA)

        choice = prompt("Select option: ")
        if choice == "1":
            subprocess.run(["termux-open", INSTAGRAM_URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pause()
        elif choice == "2":
            subprocess.run(["termux-open", PATREON_URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pause()
        elif choice == "3" or choice == "":
            return

def main_menu():
    while True:
        clear_screen()
        print_banner()
        print_box([
            f"{C.B_GREEN}[1]{C.RESET} Select Video",
            f"{C.B_GREEN}[2]{C.RESET} Settings",
            f"{C.B_GREEN}[3]{C.RESET} Links",
            f"{C.B_GREEN}[4]{C.RESET} Exit",
        ], title="MAIN MENU", color=C.B_CYAN)

        choice = prompt("Select option: ")
        if choice == "1": run_conversion()
        elif choice == "2": settings_menu()
        elif choice == "3": links_menu()
        elif choice == "4":
            clear_screen()
            sys.exit(0)

def main():
    if shutil.which("ffmpeg") is None:
        print(f"{C.B_RED}Error: ffmpeg is not installed.{C.RESET}")
        sys.exit(1)
    if shutil.which("termux-storage-get") is None:
        print(f"{C.B_RED}Error: termux-api is not installed.{C.RESET}")
        sys.exit(1)
    
    mp.freeze_support()
    main_menu()

if __name__ == "__main__":
    main()
    