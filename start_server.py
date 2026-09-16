import os
import subprocess
import sys
import urllib.request
import json
import time

def ensure_pot_provider():
    exe_name = "bgutil-pot.exe"
    if not os.path.exists(exe_name):
        print("Downloading bgutil-ytdlp-pot-provider-rs for YouTube POT token support...")
        try:
            req = urllib.request.Request("https://api.github.com/repos/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest")
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read())
                url = next(a["browser_download_url"] for a in data["assets"] if a["name"] == "bgutil-pot-windows-x86_64.exe")
            print(f"Downloading from {url}...")
            urllib.request.urlretrieve(url, exe_name)
            print("Download complete.")
        except Exception as e:
            print(f"Failed to download POT provider: {e}")
            print("YouTube downloads might fail.")
            return None
    return exe_name

def main():
    pot_exe = ensure_pot_provider()
    pot_process = None
    if pot_exe:
        print("Starting POT provider on port 4416...")
        pot_process = subprocess.Popen([pot_exe, "server", "--host", "127.0.0.1", "--port", "4416"])
        time.sleep(2)
    
    print("\nStarting Uvicorn server...")
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"])
    except KeyboardInterrupt:
        pass
    finally:
        if pot_process:
            print("Terminating POT provider...")
            pot_process.terminate()

if __name__ == "__main__":
    main()
