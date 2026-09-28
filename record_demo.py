import os
import time
import glob
from playwright.sync_api import sync_playwright

def record_demo():
    output_dir = "/config/.gemini/antigravity/brain/a82cade4-c937-4efe-ad10-78629e6db2f2"
    os.makedirs(output_dir, exist_ok=True)
    temp_video_dir = "/tmp/playwright_videos"
    os.makedirs(temp_video_dir, exist_ok=True)

    print("Starting Playwright demo recording script...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=temp_video_dir,
            record_video_size={"width": 1280, "height": 800},
        )
        page = context.new_page()

        url = "http://127.0.0.1:8080"
        print(f"Navigating to local web application: {url}")
        page.goto(url, wait_until="networkidle")
        time.sleep(3)

        # Action 1: Click the example prompt chip for inventory lookup
        print("Clicking example prompt chip: 🌿 What plants are in stock?")
        page.click(".prompt-chip:nth-child(1)")

        # Wait for agent response to complete
        print("Waiting for response 1...")
        page.wait_for_selector(".msg-row.agent", timeout=45000)
        time.sleep(6)

        # Action 2: Rich prompt showing tool calls and image generation
        prompt2 = "💧 Calculate a watering schedule for my Monstera Deliciosa and generate a visual preview photo."
        print(f"Sending Prompt 2: {prompt2}")
        page.fill("#input", prompt2)
        time.sleep(1)
        page.keyboard.press("Enter")

        # Wait for second response (including image generation & A2UI card)
        print("Waiting for response 2...")
        page.wait_for_selector(".msg-row.agent:nth-of-type(4)", timeout=60000)
        time.sleep(8)

        # Scroll chat log to ensure full card and image are visible
        page.evaluate("document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight")
        time.sleep(4)

        context.close()
        browser.close()

    # Find recorded video file and save as demo_recording.webm in artifacts
    videos = glob.glob(os.path.join(temp_video_dir, "*.webm"))
    if videos:
        latest_video = videos[0]
        target_path = os.path.join(output_dir, "demo_recording.webm")
        os.system(f"cp '{latest_video}' '{target_path}'")
        print(f"SUCCESS: Demo video saved to {target_path} (size: {os.path.getsize(target_path)} bytes)")
    else:
        print("ERROR: No video recorded by Playwright.")

if __name__ == "__main__":
    record_demo()
