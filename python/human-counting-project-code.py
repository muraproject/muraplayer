import cv2
import numpy as np

# Inisialisasi detektor HOG
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# Inisialisasi video capture
video_path = 'video.mp4'  # Ganti dengan path video Anda
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Tidak dapat membuka video di {video_path}")
    exit()

# Inisialisasi variabel
count_in = 0
count_out = 0
tracked_objects = {}
frame_count = 0

# Membuat window untuk menampilkan video
cv2.namedWindow('People Counter', cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Tidak dapat membaca frame. Mengakhiri...")
        break
    
    frame_count += 1
    
    # Resize frame untuk mempercepat pemrosesan
    frame = cv2.resize(frame, (640, 480))
    
    # Deteksi orang menggunakan HOG
    boxes, weights = hog.detectMultiScale(frame, winStride=(8,8))
    
    # Gambar garis diagonal
    h, w = frame.shape[:2]
    cv2.line(frame, (0, h), (w, 0), (0, 255, 0), 2)
    
    current_objects = {}
    for i, (x, y, w, h) in enumerate(boxes):
        center = (x + w // 2, y + h // 2)
        current_objects[i] = center
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.circle(frame, center, 4, (0, 255, 255), -1)
    
    # Pelacakan dan penghitungan
    for obj_id, center in current_objects.items():
        if obj_id in tracked_objects:
            prev_center = tracked_objects[obj_id]
            prev_pos = prev_center[1] / frame.shape[0] + prev_center[0] / frame.shape[1] - 1
            curr_pos = center[1] / frame.shape[0] + center[0] / frame.shape[1] - 1
            
            if abs(curr_pos) < 0.1 and abs(prev_pos) < 0.1:
                if curr_pos > prev_pos:
                    count_in += 1
                    cv2.circle(frame, center, 10, (0, 255, 0), -1)
                    print(f"Person entered at frame {frame_count}")
                elif curr_pos < prev_pos:
                    count_out += 1
                    cv2.circle(frame, center, 10, (0, 0, 255), -1)
                    print(f"Person exited at frame {frame_count}")
        
        tracked_objects[obj_id] = center
    
    # Tampilkan informasi
    cv2.putText(frame, f"In: {count_in} Out: {count_out}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    cv2.imshow('People Counter', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Pemrosesan video selesai.")
print(f"Total frame yang diproses: {frame_count}")
print(f"Total orang masuk: {count_in}")
print(f"Total orang keluar: {count_out}")