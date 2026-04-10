"""
start_server.py — College Management System Network Launcher
============================================================
Run from backend so the uv virtual environment is used:

  cd backend
  uv run python ..\\start_server.py           # LAN access only
  uv run python ..\\start_server.py --tunnel  # LAN + internet tunnel

Dependencies (qrcode, Pillow) are installed via:
  uv pip install -r requirements.txt
"""

import sys
try: sys.stdout.reconfigure(encoding='utf-8')
except AttributeError: pass
import os
import socket
import subprocess
import time
import argparse
import re

import qrcode

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT       = os.path.dirname(os.path.abspath(__file__))
BACKEND    = os.path.join(ROOT, "backend")
FRONTEND   = os.path.join(ROOT, "frontend")
WHATSAPP   = os.path.join(ROOT, "whatsapp_service")
BACKEND_PORT  = 6000
FRONTEND_PORT = 9000
WHATSAPP_PORT = 4000

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_lan_ip():
    """Return the machine's primary LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_qr(url, label):
    """Print a QR code for the given URL in the terminal."""
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    print(f"\n  ┌─ {label} ─────────────────────────────────────")
    print(f"  │  URL: {url}")
    qr.print_ascii(invert=True)
    print(f"  └────────────────────────────────────────────────\n")

def run_frontend_server():
    """Start the Python HTTP server for the frontend."""
    print(f"[frontend] Starting HTTP server on 0.0.0.0:{FRONTEND_PORT} ...")
    subprocess.Popen(
        [sys.executable, "-m", "http.server", str(FRONTEND_PORT), "--bind", "0.0.0.0"],
        cwd=FRONTEND,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def run_backend_server():
    """Start the Flask backend using uv run (uses the venv in backend)."""
    print(f"[backend]  Starting Flask API on 0.0.0.0:{BACKEND_PORT} ...")
    subprocess.Popen(
        ["uv", "run", "python", "run.py"],
        cwd=BACKEND,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def run_whatsapp_service():
    """Start the Node.js WhatsApp automated microservice."""
    print(f"[whatsapp] Starting WhatsApp Node.js service on 0.0.0.0:{WHATSAPP_PORT} ...")
    
    # Check if node modules exist
    node_modules_path = os.path.join(WHATSAPP, "node_modules")
    if not os.path.exists(node_modules_path):
        print("[whatsapp] ⚠️  node_modules not found. Installing dependencies first...")
        subprocess.run(["npm", "install"], cwd=WHATSAPP, shell=True)

    subprocess.Popen(
        ["node", "index.js"],
        cwd=WHATSAPP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True # Required on Windows to resolve 'node' from PATH in Popen easily
    )

def start_cloudflare_tunnel(port):
    """
    Start a Cloudflare Quick Tunnel and return the public HTTPS URL.
    No Cloudflare account needed — Quick Tunnels are built-in.
    """
    print("[tunnel]  Starting Cloudflare Quick Tunnel (no account needed)...")

    # Try to find cloudflared or download it
    cloudflared = _find_or_download_cloudflared()
    if not cloudflared:
        print("[tunnel]  ⚠️  Could not find or download cloudflared. Skipping tunnel.")
        return None

    proc = subprocess.Popen(
        [cloudflared, "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Parse the public URL from cloudflared output
    url_pattern = re.compile(r"https://[a-z0-9\-]+\.trycloudflare\.com")
    start = time.time()
    while time.time() - start < 30:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.2)
            continue
        match = url_pattern.search(line)
        if match:
            return match.group(0), proc
    print("[tunnel]  ⚠️  Timed out waiting for tunnel URL.")
    return None, proc

def _find_or_download_cloudflared():
    """Find cloudflared in PATH, or download the Windows binary to a temp location."""
    # Check PATH first
    result = subprocess.run(["where", "cloudflared"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().splitlines()[0]

    # Try winget install silently
    print("[tunnel]  cloudflared not found. Trying winget install...")
    r = subprocess.run(
        ["winget", "install", "--id", "Cloudflare.cloudflared", "-e", "--silent"],
        capture_output=True, text=True
    )
    result2 = subprocess.run(["where", "cloudflared"], capture_output=True, text=True)
    if result2.returncode == 0:
        return result2.stdout.strip().splitlines()[0]

    # Download binary directly as fallback
    print("[tunnel]  Downloading cloudflared binary directly...")
    import urllib.request
    bin_path = os.path.join(ROOT, "cloudflared.exe")
    if not os.path.exists(bin_path):
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        try:
            urllib.request.urlretrieve(url, bin_path)
            print(f"[tunnel]  Downloaded to {bin_path}")
        except Exception as e:
            print(f"[tunnel]  Download failed: {e}")
            return None
    return bin_path

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="College Management System Launcher")
    parser.add_argument("--tunnel", action="store_true", help="Enable Cloudflare internet tunnel")
    parser.add_argument("--no-backend", action="store_true", help="Skip backend (already running)")
    parser.add_argument("--no-frontend", action="store_true", help="Skip frontend (already running)")
    parser.add_argument("--no-whatsapp", action="store_true", help="Skip WhatsApp microservice")
    args = parser.parse_args()

    print("\n" + "="*55)
    print("  🎓  College Management System — Network Launcher")
    print("="*55)

    # Start servers
    if not args.no_frontend:
        run_frontend_server()
    if not args.no_backend:
        run_backend_server()
    if not args.no_whatsapp:
        run_whatsapp_service()

    # Wait for servers to start
    print("[setup]   Waiting for servers to start...")
    time.sleep(3)

    # Get LAN IP
    lan_ip = get_lan_ip()

    print("\n" + "="*55)
    print("  ✅  Servers are running!")
    print("="*55)

    # Print LAN QR codes
    frontend_lan_url = f"http://{lan_ip}:{FRONTEND_PORT}/login.html"
    backend_lan_url  = f"http://{lan_ip}:{BACKEND_PORT}/api/health"

    print_qr(frontend_lan_url, "📱 LAN — Open on any device on this Wi-Fi network")
    print(f"  💻  Or open in browser: {frontend_lan_url}")
    print(f"  🔌  API endpoint:        http://{lan_ip}:{BACKEND_PORT}/api")

    # Cloudflare tunnel (internet access)
    if args.tunnel:
        print("\n" + "-"*55)
        result = start_cloudflare_tunnel(FRONTEND_PORT)
        if result and result[0]:
            public_url, tunnel_proc = result
            internet_frontend_url = f"{public_url}/login.html"
            print_qr(internet_frontend_url, "🌐 INTERNET — Share this link with anyone anywhere")
            print(f"  🌐  Public link: {internet_frontend_url}")
            print(f"\n  ⚠️  NOTE: For internet access, the backend API also needs")
            print(f"      a tunnel. Run this in a second terminal:")
            print(f"      python start_server.py --tunnel --no-frontend --tunnel-port {BACKEND_PORT}")
        else:
            print("[tunnel]  Could not start tunnel. Run without --tunnel for LAN-only mode.")

    print("\n" + "="*55)
    print("  Press Ctrl+C to stop all servers")
    print("="*55 + "\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[shutdown] Stopping servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()
