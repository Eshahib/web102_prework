#!/usr/bin/env python3
"""Capture site screenshots and build walkthrough.gif for README submission."""
import http.server
import socketserver
import threading
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
OUTPUT = ROOT / "walkthrough.gif"


def start_server():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

    httpd = socketserver.TCPServer(("", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def main():
    import os

    os.chdir(ROOT)
    httpd = start_server()
    url = f"http://127.0.0.1:{PORT}/index.html"
    frames_dir = ROOT / ".walkthrough_frames"
    frames_dir.mkdir(exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(800)

            steps = [
                ("all-games", None),
                ("unfunded", "#unfunded-btn"),
                ("funded", "#funded-btn"),
                ("all-again", "#all-btn"),
            ]
            paths = []
            for i, (_, selector) in enumerate(steps):
                if selector:
                    page.click(selector)
                    page.wait_for_timeout(600)
                path = frames_dir / f"frame_{i:02d}.png"
                page.screenshot(path=str(path), full_page=True)
                paths.append(path)

            browser.close()

        images = [Image.open(p).convert("RGB") for p in paths]
        # Duplicate each frame so the GIF is easier to read
        gif_frames = []
        for img in images:
            gif_frames.extend([img] * 4)

        gif_frames[0].save(
            OUTPUT,
            save_all=True,
            append_images=gif_frames[1:],
            duration=900,
            loop=0,
            optimize=True,
        )
        print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    finally:
        httpd.shutdown()
        for f in frames_dir.glob("*.png"):
            f.unlink()
        frames_dir.rmdir()


if __name__ == "__main__":
    main()
