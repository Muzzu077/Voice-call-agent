import os
import urllib.request
import sys

print("Downloading Kokoro ONNX v1.0 model files...")

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

def download_file(url, filename):
    print(f"Downloading {filename} from {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response, open(filename, 'wb') as out_file:
            # We want to download the entire file in chunks to show progress
            total_size_in_bytes= int(response.info().get('Content-Length', 0))
            block_size = 1024 * 1024 # 1 Megabyte
            downloaded = 0
            while True:
                data = response.read(block_size)
                if not data:
                    break
                downloaded += len(data)
                out_file.write(data)
                if total_size_in_bytes > 0:
                    percent = downloaded * 100 / total_size_in_bytes
                    sys.stdout.write(f"\rDownloaded {downloaded // (1024*1024)}MB of {total_size_in_bytes // (1024*1024)}MB ({percent:.1f}%)")
                    sys.stdout.flush()
            print()
        print(f"Saved {filename}")
    except Exception as e:
        print(f"\nFailed to download {filename}: {e}")
        if os.path.exists(filename):
            os.remove(filename)

if not os.path.exists("kokoro-v1.0.onnx"):
    download_file(MODEL_URL, "kokoro-v1.0.onnx")
else:
    print("kokoro-v1.0.onnx already exists.")

if not os.path.exists("voices-v1.0.bin"):
    download_file(VOICES_URL, "voices-v1.0.bin")
else:
    print("voices-v1.0.bin already exists.")

print("Download complete! You can now start the server.")
