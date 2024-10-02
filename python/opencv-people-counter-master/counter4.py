import numpy as np
import cv2
import imutils
import os
from collections import deque
import time

def find_majority(k):
    myMap = {}
    maximum = ('', 0)  # (occurring element, occurrences)
    for n in k:
        if n in myMap:
            myMap[n] += 1
        else:
            myMap[n] = 1

        # Keep track of maximum on the go
        if myMap[n] > maximum[1]:
            maximum = (n, myMap[n])

    return maximum

class ObjectTracker:
    def __init__(self, max_disappeared=10, max_distance=50):
        self.nextObjectID = 0
        self.objects = {}
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        del self.objects[objectID]
        del self.disappeared[objectID]

    def update(self, rects):
        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.max_disappeared:
                    self.deregister(objectID)
            return self.objects

        inputCentroids = np.zeros((len(rects), 2), dtype="int")
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)

        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i])
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = np.linalg.norm(np.array(objectCentroids)[:, np.newaxis] - inputCentroids, axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row, col) in zip(rows, cols):
                if row in usedRows or col in usedCols:
                    continue
                if D[row, col] > self.max_distance:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]
                self.disappeared[objectID] = 0

                usedRows.add(row)
                usedCols.add(col)

            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            if D.shape[0] >= D.shape[1]:
                for row in unusedRows:
                    objectID = objectIDs[row]
                    self.disappeared[objectID] += 1
                    if self.disappeared[objectID] > self.max_disappeared:
                        self.deregister(objectID)
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col])

        return self.objects

def process_frame(frame, avg, tracker, min_area=5000):
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if avg is None:
        avg = gray.copy().astype("float")
        return frame, gray, avg, {}

    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    rects = []
    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        rects.append((x, y, x + w, y + h))

    objects = tracker.update(rects)

    for (objectID, centroid) in objects.items():
        text = f"ID {objectID}"
        cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

    return frame, gray, avg, objects

def main():
    print(f"Current working directory: {os.getcwd()}")
    print("Files in the current directory:")
    for file in os.listdir():
        print(f"- {file}")

    video_file = "edit.mp4"
    if not os.path.exists(video_file):
        print(f"Error: The file '{video_file}' does not exist in the current directory.")
        return

    video = cv2.VideoCapture(video_file)
    if not video.isOpened():
        print(f"Error: Couldn't open video file '{video_file}'. Please check the file path and permissions.")
        return

    orig_fps = video.get(cv2.CAP_PROP_FPS)
    print(f"Video properties: Width: {video.get(cv2.CAP_PROP_FRAME_WIDTH)}, "
          f"Height: {video.get(cv2.CAP_PROP_FRAME_HEIGHT)}, "
          f"Original FPS: {orig_fps}")

    playback_fps = 30  # As requested

    avg = None
    object_positions = {}
    count_in = 0
    count_out = 0
    frame_count = 0

    tracker = ObjectTracker(max_disappeared=10, max_distance=50)

    # Define the counting line
    counting_line = 340  # Adjust this value based on your video

    while True:
        start_time = time.time()

        ret, frame = video.read()
        if not ret:
            print("End of video stream.")
            break

        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames")

        frame, gray, avg, objects = process_frame(frame, avg, tracker)

        for object_id, new_position in objects.items():
            if object_id in object_positions:
                old_position = object_positions[object_id]
                if old_position[0] < counting_line <= new_position[0]:
                    count_in += 1
                    print(f"Object {object_id} moved in. Total In: {count_in}")
                elif old_position[0] >= counting_line > new_position[0]:
                    count_out += 1
                    print(f"Object {object_id} moved out. Total Out: {count_out}")
            object_positions[object_id] = new_position

        cv2.line(frame, (counting_line, 0), (counting_line, 480), (0, 255, 0), 2)
        cv2.putText(frame, f"In: {count_in}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, f"Out: {count_out}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imshow("Frame", frame)
        cv2.imshow("Gray", gray)
        cv2.imshow("Frame Delta", cv2.absdiff(gray, cv2.convertScaleAbs(avg)))

        elapsed_time = time.time() - start_time
        wait_time = max(1, int((1 / playback_fps - elapsed_time) * 1000))

        key = cv2.waitKey(wait_time) & 0xFF
        if key == ord('q'):
            print("User terminated the program.")
            break

    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()