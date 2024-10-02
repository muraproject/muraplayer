import cv2
import numpy as np

# Inisialisasi video capture
video_path = 'video.mp4'  # Ganti dengan path video Anda
cap = cv2.VideoCapture(video_path)

# Periksa apakah video berhasil dibuka
if not cap.isOpened():
    print(f"Error: Tidak dapat membuka video di {video_path}")
    exit()

# Dapatkan informasi frame rate video
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Frame rate video: {fps}")

# Inisialisasi background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2()

# Inisialisasi variabel untuk menghitung
count_in = 0
count_out = 0

# Fungsi untuk menggambar garis diagonal (kiri bawah ke kanan atas)
def draw_line(frame):
    h, w = frame.shape[:2]
    cv2.line(frame, (0, h), (w, 0), (0, 255, 0), 2)
    return frame

# Inisialisasi list untuk melacak objek
tracked_objects = []

# Fungsi untuk mendeteksi pergerakan
def detect_movement(frame, fgmask):
    global count_in, count_out, tracked_objects
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    h, w = frame.shape[:2]
    new_tracked_objects = []
    
    for contour in contours:
        if cv2.contourArea(contour) > 2000:  # Filter berdasarkan ukuran
            x, y, w, h = cv2.boundingRect(contour)
            center = (x + w//2, y + h//2)
            
            # Cek apakah objek ini sudah dilacak
            tracked = False
            for obj in tracked_objects:
                dist = np.sqrt((center[0] - obj['center'][0])**2 + (center[1] - obj['center'][1])**2)
                if dist < 50:  # Jika objek cukup dekat dengan yang dilacak sebelumnya
                    tracked = True
                    if not obj['counted']:
                        if abs(center[1] / frame.shape[0] + center[0] / frame.shape[1] - 1) < 0.1:
                            if center[1] / frame.shape[0] > center[0] / frame.shape[1]:
                                count_in += 1
                            else:
                                count_out += 1
                            obj['counted'] = True
                    new_tracked_objects.append({'center': center, 'counted': obj['counted']})
                    break
            
            if not tracked:
                new_tracked_objects.append({'center': center, 'counted': False})
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    tracked_objects = new_tracked_objects
    return frame

# Membuat window untuk menampilkan video
cv2.namedWindow('People Counter', cv2.WINDOW_NORMAL)

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Tidak dapat membaca frame. Mengakhiri...")
        break
    
    frame_count += 1
    
    # Terapkan background subtraction
    fgmask = fgbg.apply(frame)
    
    # Pra-pemrosesan mask
    kernel = np.ones((5,5), np.uint8)
    fgmask = cv2.erode(fgmask, kernel, iterations=1)
    fgmask = cv2.dilate(fgmask, kernel, iterations=1)
    
    # Deteksi pergerakan
    frame = detect_movement(frame, fgmask)
    
    # Gambar garis diagonal
    frame = draw_line(frame)
    
    # Tampilkan hitungan
    cv2.putText(frame, f"In: {count_in} Out: {count_out}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Tampilkan frame
    cv2.imshow('People Counter', frame)
    
    # Cetak informasi setiap 30 frame
    if frame_count % 30 == 0:
        print(f"Frame ke-{frame_count} diproses. In: {count_in}, Out: {count_out}")
    
    # Tekan 'q' untuk keluar
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Pemrosesan video selesai.")
print(f"Total frame yang diproses: {frame_count}")
print(f"Total orang masuk: {count_in}")
print(f"Total orang keluar: {count_out}")