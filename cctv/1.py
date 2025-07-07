import time
import sys
import os
import threading
import logging
import socket
from flask import Flask, Response, render_template
import cv2
import numpy as np

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Konfigurasi RTSP
rtsp_urls = {
    "cam1": "rtsp://admin:Admin123@41.216.191.132:554/Streaming/Channels/102",
    "cam2": "rtsp://admin:Admin123@41.216.191.132:554/Streaming/Channels/101"  # Add second camera
}

# Konfigurasi HTTP server
http_port = 5003
frame_rate = 20  # FPS untuk HTTP stream

# Variabel global untuk sharing data
current_frames = {
    "cam1": None,
    "cam2": None
}
frame_locks = {
    "cam1": threading.Lock(),
    "cam2": threading.Lock()
}
connection_status = {
    "cam1": False,
    "cam2": False
}
server_running = True

def get_local_ip():
    """Fungsi untuk mendapatkan alamat IP lokal"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.warning(f"Tidak dapat mendapatkan IP lokal: {str(e)}")
        return "127.0.0.1"

def capture_thread_function(cam_id):
    """Thread untuk menangkap frame dari RTSP stream menggunakan OpenCV"""
    global current_frames, connection_status
    
    rtsp_url = rtsp_urls[cam_id]
    cap = None
    
    # Variabel untuk timing
    last_capture_time = 0
    capture_interval = 1.0 / frame_rate  # Interval capture sesuai frame rate
    reconnect_delay = 5  # Delay untuk reconnect dalam detik
    
    logger.info(f"Memulai capture {cam_id} dari {rtsp_url}")
    
    while server_running:
        try:
            # Inisialisasi atau reinisialisasi capture
            if cap is None or not cap.isOpened():
                logger.info(f"{cam_id}: Mencoba koneksi ke {rtsp_url}")
                connection_status[cam_id] = False
                
                # Buat VideoCapture object
                cap = cv2.VideoCapture(rtsp_url)
                
                # Set buffer size untuk mengurangi latency
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Set timeout
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
                
                # Coba buka stream
                if not cap.isOpened():
                    logger.error(f"{cam_id}: Tidak dapat membuka stream")
                    time.sleep(reconnect_delay)
                    continue
                
                logger.info(f"{cam_id}: Berhasil terhubung")
                connection_status[cam_id] = True
            
            current_time = time.time()
            
            # Ambil frame pada interval yang ditentukan
            if current_time - last_capture_time >= capture_interval:
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    # Tambahkan overlay status
                    add_status_overlay(frame, cam_id, rtsp_url)
                    
                    # Update frame global dengan thread lock
                    with frame_locks[cam_id]:
                        current_frames[cam_id] = frame.copy()
                    
                    connection_status[cam_id] = True
                    last_capture_time = current_time
                else:
                    logger.warning(f"{cam_id}: Tidak dapat membaca frame")
                    connection_status[cam_id] = False
                    
                    # Reset capture object
                    if cap is not None:
                        cap.release()
                        cap = None
                    time.sleep(1)
            else:
                # Jika belum waktunya capture frame baru, tidur sebentar
                sleep_time = capture_interval - (current_time - last_capture_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except Exception as e:
            logger.error(f"Error dalam capture thread {cam_id}: {str(e)}")
            connection_status[cam_id] = False
            
            # Reset capture object
            if cap is not None:
                cap.release()
                cap = None
            
            time.sleep(reconnect_delay)
    
    # Cleanup
    if cap is not None:
        cap.release()
    logger.info(f"Capture thread {cam_id} berhenti")

def add_status_overlay(frame, cam_id, rtsp_url):
    """Menambahkan overlay status ke frame"""
    if frame is None:
        return
    
    height, width = frame.shape[:2]
    
    # Background semi-transparan
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, height-60), (width, height), (0, 0, 0), -1)
    alpha = 0.7
    cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)
    
    # Tambahkan informasi status
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    status_text = f"{cam_id.upper()} | {current_time}"
    cv2.putText(frame, status_text, (10, height-35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Tambahkan info resolusi
    resolution_text = f"Resolution: {width}x{height}"
    cv2.putText(frame, resolution_text, (10, height-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

def create_status_frame(message, cam_id):
    """Membuat frame status ketika tidak ada koneksi"""
    frame = np.zeros((480, 640, 3), np.uint8)
    
    # Tambahkan waktu saat ini
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, current_time, (20, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Tampilkan pesan
    cv2.putText(frame, message, (20, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Tampilkan info kamera
    cv2.putText(frame, f"Camera: {cam_id.upper()}", (20, 350), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    # Tampilkan info URL (dipotong jika terlalu panjang)
    url = rtsp_urls.get(cam_id, "Unknown")
    if len(url) > 50:
        url = url[:47] + "..."
    cv2.putText(frame, f"URL: {url}", (20, 380), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return frame

def generate_frames(cam_id):
    """Generator untuk streaming HTTP"""
    global current_frames, connection_status
    
    while server_running:
        # Jika tidak ada frame atau tidak terhubung, kirim frame status
        if current_frames[cam_id] is None or not connection_status[cam_id]:
            status_frame = create_status_frame(f"Connecting to {cam_id}...", cam_id)
            
            # Encode frame untuk streaming
            ret, buffer = cv2.imencode('.jpg', status_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Jeda lebih lama saat tidak ada koneksi
            time.sleep(0.5)
            continue
        
        # Ambil frame dengan thread lock
        with frame_locks[cam_id]:
            if current_frames[cam_id] is not None:
                frame_to_send = current_frames[cam_id].copy()
            else:
                continue
        
        # Encode frame untuk streaming
        ret, buffer = cv2.imencode('.jpg', frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Jeda sesuai frame rate
        time.sleep(1.0 / frame_rate)

def generate_combined_frames():
    """Generator untuk streaming gabungan dua kamera"""
    global current_frames, connection_status
    
    while server_running:
        # Buat frame gabungan
        combined_frame = None
        
        # Dapatkan frame dari kedua kamera
        frame1 = None
        frame2 = None
        
        # Ambil frame cam1 dengan thread lock
        with frame_locks["cam1"]:
            if current_frames["cam1"] is not None and connection_status["cam1"]:
                frame1 = current_frames["cam1"].copy()
            else:
                frame1 = create_status_frame("Connecting to Camera 1...", "cam1")
        
        # Ambil frame cam2 dengan thread lock
        with frame_locks["cam2"]:
            if current_frames["cam2"] is not None and connection_status["cam2"]:
                frame2 = current_frames["cam2"].copy()
            else:
                frame2 = create_status_frame("Connecting to Camera 2...", "cam2")
        
        # Resize kedua frame ke ukuran yang sama
        height = 360  # Tinggi setiap frame
        width = 640   # Lebar setiap frame
        
        frame1 = cv2.resize(frame1, (width, height))
        frame2 = cv2.resize(frame2, (width, height))
        
        # Gabungkan frame secara vertikal
        combined_frame = np.vstack((frame1, frame2))
        
        # Tambahkan garis pemisah
        cv2.line(combined_frame, (0, height), (width, height), (0, 255, 255), 3)
        
        # Tambahkan timestamp pada combined view
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(combined_frame, f"Combined View | {current_time}", 
                   (10, height * 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Encode frame untuk streaming
        ret, buffer = cv2.imencode('.jpg', combined_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Jeda sesuai frame rate
        time.sleep(1.0 / frame_rate)

# Inisialisasi Flask
app = Flask(__name__)

@app.route('/')
def index():
    """Halaman utama"""
    local_ip = get_local_ip()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dual RTSP Stream Viewer (OpenCV)</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; background-color: #f0f0f0; }}
            .stream-container {{ 
                margin: 20px auto; 
                background-color: #000; 
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                max-width: 640px;
            }}
            .stream-img {{
                max-width: 100%;
                height: auto;
                display: block;
            }}
            h1 {{ color: #333; }}
            h2 {{ color: #555; font-size: 1.2em; margin-top: 30px; }}
            .info {{ background-color: #333; color: #fff; padding: 10px; font-size: 14px; border-radius: 5px; margin: 10px 0; }}
            .status {{ margin: 10px 0; padding: 10px; color: white; border-radius: 5px; display: inline-block; min-width: 200px; }}
            .connected {{ background-color: #4CAF50; }}
            .disconnected {{ background-color: #f44336; }}
            .streams-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .button-container {{
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                margin: 0 10px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
            .tech-info {{
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                font-size: 14px;
            }}
        </style>
        <script>
            // Fungsi untuk memeriksa status koneksi
            function checkStatus() {{
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {{
                        const status1Elem = document.getElementById('status1');
                        const status2Elem = document.getElementById('status2');
                        
                        if (data.cam1) {{
                            status1Elem.innerText = 'Camera 1: Connected';
                            status1Elem.className = 'status connected';
                        }} else {{
                            status1Elem.innerText = 'Camera 1: Disconnected';
                            status1Elem.className = 'status disconnected';
                        }}
                        
                        if (data.cam2) {{
                            status2Elem.innerText = 'Camera 2: Connected';
                            status2Elem.className = 'status connected';
                        }} else {{
                            status2Elem.innerText = 'Camera 2: Disconnected';
                            status2Elem.className = 'status disconnected';
                        }}
                    }})
                    .catch(err => {{
                        console.error("Error checking status:", err);
                    }});
            }}
            
            // Periksa status setiap 3 detik
            setInterval(checkStatus, 3000);
            
            // Periksa status saat halaman dimuat
            window.onload = checkStatus;
        </script>
    </head>
    <body>
        <h1>🎥 Dual RTSP Stream Viewer</h1>
        <div class="tech-info">Using OpenCV for better compatibility and performance</div>
        
        <div>
            <span id="status1" class="status">Camera 1: Checking...</span>
            <span id="status2" class="status">Camera 2: Checking...</span>
        </div>
        
        <div class="button-container">
            <a href="/view/cam1" class="button">📹 View Camera 1</a>
            <a href="/view/cam2" class="button">📹 View Camera 2</a>
            <a href="/view/combined" class="button">📺 View Combined</a>
        </div>
        
        <h2>Combined View</h2>
        <div class="stream-container">
            <img src="/video_feed/combined" class="stream-img" alt="Combined Stream" />
        </div>
        
        <div class="streams-grid">
            <div>
                <h2>Camera 1</h2>
                <div class="stream-container">
                    <img src="/video_feed/cam1" class="stream-img" alt="Camera 1 Stream" />
                </div>
            </div>
            
            <div>
                <h2>Camera 2</h2>
                <div class="stream-container">
                    <img src="/video_feed/cam2" class="stream-img" alt="Camera 2 Stream" />
                </div>
            </div>
        </div>
        
        <div class="info">
            <p><strong>Server Info:</strong></p>
            <p>🌐 Port: {http_port} | Frame Rate: {frame_rate} FPS</p>
            <p>📷 Camera 1: {rtsp_urls['cam1']}</p>
            <p>📷 Camera 2: {rtsp_urls['cam2']}</p>
            <p>🔗 External Access: <a href="http://{local_ip}:{http_port}/" style="color: #7FDBFF;">http://{local_ip}:{http_port}/</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/view/<cam_id>')
def view_single(cam_id):
    """Halaman untuk melihat kamera tunggal"""
    if cam_id not in ["cam1", "cam2", "combined"]:
        return "Camera not found", 404
    
    title = "Camera 1" if cam_id == "cam1" else "Camera 2" if cam_id == "cam2" else "Combined View"
    feed_url = f"/video_feed/{cam_id}"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title} - RTSP Stream</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #000; }}
            .stream-container {{ 
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }}
            .stream-img {{
                width: 100%;
                height: 100%;
                object-fit: contain;
            }}
            .back-button {{
                position: fixed;
                top: 10px;
                left: 10px;
                padding: 10px 20px;
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                text-decoration: none;
                border-radius: 5px;
                z-index: 100;
                font-weight: bold;
            }}
            .back-button:hover {{
                background-color: rgba(0, 0, 0, 0.9);
            }}
            .fullscreen-btn {{
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 10px 20px;
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                border: none;
                border-radius: 5px;
                z-index: 100;
                cursor: pointer;
                font-weight: bold;
            }}
            .fullscreen-btn:hover {{
                background-color: rgba(0, 0, 0, 0.9);
            }}
        </style>
        <script>
            function toggleFullscreen() {{
                if (!document.fullscreenElement) {{
                    document.documentElement.requestFullscreen();
                }} else {{
                    document.exitFullscreen();
                }}
            }}
        </script>
    </head>
    <body>
        <a href="/" class="back-button">← Back</a>
        <button onclick="toggleFullscreen()" class="fullscreen-btn">⛶ Fullscreen</button>
        <div class="stream-container">
            <img src="{feed_url}" class="stream-img" alt="{title}" />
        </div>
    </body>
    </html>
    """

@app.route('/video_feed/<cam_id>')
def video_feed(cam_id):
    """Endpoint untuk streaming video"""
    if cam_id == "combined":
        return Response(generate_combined_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    elif cam_id in ["cam1", "cam2"]:
        return Response(generate_frames(cam_id),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Camera not found", 404

@app.route('/status')
def status():
    """Endpoint untuk cek status koneksi"""
    return {
        "cam1": connection_status["cam1"],
        "cam2": connection_status["cam2"],
        "timestamp": time.time(),
        "server_running": server_running
    }

def cleanup():
    """Fungsi untuk membersihkan sumber daya"""
    global server_running
    
    server_running = False
    logger.info("Menghentikan server...")
    logger.info("Cleanup selesai")

def run_server():
    """Menjalankan server Flask"""
    local_ip = get_local_ip()
    logger.info(f"Starting HTTP server di http://{local_ip}:{http_port}/")
    
    try:
        # Coba gunakan Waitress jika tersedia
        from waitress import serve
        serve(app, host='0.0.0.0', port=http_port, threads=6)
    except ImportError:
        # Fallback ke Flask development server
        logger.warning("Waitress tidak tersedia, menggunakan Flask dev server")
        app.run(host='0.0.0.0', port=http_port, threaded=True, debug=False)

if __name__ == "__main__":
    try:
        # Mulai thread capture untuk kedua kamera
        for cam_id in rtsp_urls.keys():
            capture_thread = threading.Thread(target=capture_thread_function, args=(cam_id,))
            capture_thread.daemon = True
            capture_thread.start()
            logger.info(f"Thread untuk {cam_id} dimulai")
        
        # Tunggu sebentar untuk inisialisasi
        time.sleep(2)
        
        # Jalankan server HTTP
        run_server()
        
    except KeyboardInterrupt:
        logger.info("Program dihentikan oleh pengguna")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        cleanup()