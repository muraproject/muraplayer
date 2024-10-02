import cv2
import numpy as np
from collections import deque

# Inisialisasi video capture
video_path = 'video.mp4'  # Ganti dengan path video Anda
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Tidak dapat membuka video di {video_path}")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Frame rate video: {fps}")

fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)

count_in = 0
count_out = 0

def draw_line(frame):
    h, w = frame.shape[:2]
    cv2.line(frame, (0, h), (w, 0), (0, 255, 0), 2)
    return frame

class TrackedObject:
    def __init__(self, center):
        self.positions = deque(maxlen=20)
        self.positions.append(center)
        self.counted = False

    def update(self, center):
        self.positions.append(center)

    def get_direction(self):
        if len(self.positions) < 2:
            return None
        first = self.positions[0]
        last = self.positions[-1]
        if last[1] / 480 + last[0] / 640 > first[1] / 480 + first[0] / 640:
            return "in"
        else:
            return "out"

tracked_objects = []

def detect_movement(frame, fgmask):
    global count_in, count_out, tracked_objects
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    h, w = frame.shape[:2]
    current_objects = []
    
    for contour in contours:
        if cv2.contourArea(contour) > 1500:  # Increased minimum area
            x, y, w, h = cv2.boundingRect(contour)
            center = (x + w//2, y + h//2)
            current_objects.append(center)
            
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.circle(frame, center, 5, (0, 255, 255), -1)
    
    if not tracked_objects:
        for center in current_objects:
            tracked_objects.append(TrackedObject(center))
    else:
        new_tracked_objects = []
        for center in current_objects:
            closest_obj = min(tracked_objects, key=lambda obj: np.linalg.norm(np.array(obj.positions[-1]) - np.array(center)))
            if np.linalg.norm(np.array(closest_obj.positions[-1]) - np.array(center)) < 50:
                closest_obj.update(center)
                new_tracked_objects.append(closest_obj)
            else:
                new_tracked_objects.append(TrackedObject(center))
        
        for obj in new_tracked_objects:
            if not obj.counted and len(obj.positions) > 10:
                direction = obj.get_direction()
                if direction == "in":
                    relative_pos = obj.positions[-1][1]/h + obj.positions[-1][0]/w - 1
                    if -0.1 < relative_pos < 0.1:
                        count_in += 1
                        obj.counted = True
                        cv2.circle(frame, obj.positions[-1], 10, (0, 255, 0), -1)
                        print(f"Person entered at frame {frame_count}")
                elif direction == "out":
                    relative_pos = obj.positions[-1][1]/h + obj.positions[-1][0]/w - 1
                    if -0.1 < relative_pos < 0.1:
                        count_out += 1
                        obj.counted = True
                        cv2.circle(frame, obj.positions[-1], 10, (0, 0, 255), -1)
                        print(f"Person exited at frame {frame_count}")
        
        tracked_objects = new_tracked_objects

    return frame

cv2.namedWindow('People Counter', cv2.WINDOW_NORMAL)

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Tidak dapat membaca frame. Mengakhiri...")
        break
    
    frame_count += 1
    
    fgmask = fgbg.apply(frame)
    
    kernel = np.ones((3,3), np.uint8)
    fgmask = cv2.erode(fgmask, kernel, iterations=1)
    fgmask = cv2.dilate(fgmask, kernel, iterations=2)
    
    frame = detect_movement(frame, fgmask)
    frame = draw_line(frame)
    
    cv2.putText(frame, f"In: {count_in} Out: {count_out}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    cv2.imshow('People Counter', frame)
    cv2.imshow('Foreground Mask', fgmask)
    
    if frame_count % 30 == 0:
        print(f"Frame ke-{frame_count} diproses. In: {count_in}, Out: {count_out}")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Pemrosesan video selesai.")
print(f"Total frame yang diproses: {frame_count}")
print(f"Total orang masuk: {count_in}")
print(f"Total orang keluar: {count_out}")