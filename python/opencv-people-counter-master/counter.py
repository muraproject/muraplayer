import numpy as np
import cv2
import imutils
import os
from collections import deque

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

def process_frame(frame, avg, min_area=5000):
    # Resize the frame, convert it to grayscale, and blur it
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # If the average frame is None, initialize it
    if avg is None:
        avg = gray.copy().astype("float")
        return frame, gray, avg, []

    # Accumulate the weighted average between the current frame and previous frames
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    # Threshold the delta image, dilate the thresholded image to fill in holes
    thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Find contours on thresholded image
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    # Initialize the list of detected x-coordinates
    detected_x = []

    # Loop over the contours
    for c in cnts:
        # If the contour is too small, ignore it
        if cv2.contourArea(c) < min_area:
            continue

        # Compute the bounding box for the contour and draw it on the frame
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        detected_x.append(x)

    return frame, gray, avg, detected_x

def main():
    # Print current working directory and list files
    print(f"Current working directory: {os.getcwd()}")
    print("Files in the current directory:")
    for file in os.listdir():
        print(f"- {file}")

    video_file = "edit.mp4"
    if not os.path.exists(video_file):
        print(f"Error: The file '{video_file}' does not exist in the current directory.")
        return

    # Initialize video capture
    video = cv2.VideoCapture(video_file)
    if not video.isOpened():
        print(f"Error: Couldn't open video file '{video_file}'. Please check the file path and permissions.")
        return

    print(f"Video properties: Width: {video.get(cv2.CAP_PROP_FRAME_WIDTH)}, "
          f"Height: {video.get(cv2.CAP_PROP_FRAME_HEIGHT)}, "
          f"FPS: {video.get(cv2.CAP_PROP_FPS)}")

    # Initialize variables
    avg = None
    xvalues = deque(maxlen=10)  # Store only the last 10 x-values
    motion = deque(maxlen=20)   # Store only the last 20 motion directions
    count_in = 0
    count_out = 0
    frame_count = 0

    while True:
        ret, frame = video.read()
        if not ret:
            print("End of video stream.")
            break

        frame_count += 1
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames")

        # Process the frame
        frame, gray, avg, detected_x = process_frame(frame, avg)

        # If we detected any objects, analyze their motion
        if detected_x:
            xvalues.extend(detected_x)
            if len(xvalues) > 2:
                # Determine the direction of motion
                difference = xvalues[-1] - xvalues[-2]
                motion.append(1 if difference > 0 else 0)

        # If no objects were detected in this frame, check if we need to count a movement
        elif len(motion) > 5:
            val, times = find_majority(motion)
            if val == 1 and times >= 15:
                count_in += 1
                print(f"Movement detected: In. Total In: {count_in}")
            else:
                count_out += 1
                print(f"Movement detected: Out. Total Out: {count_out}")
            motion.clear()

        # Draw reference lines and counts on the frame
        cv2.line(frame, (260, 0), (260, 480), (0, 255, 0), 2)
        cv2.line(frame, (420, 0), (420, 480), (0, 255, 0), 2)    
        cv2.putText(frame, f"In: {count_in}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, f"Out: {count_out}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Show the frames
        cv2.imshow("Frame", frame)
        cv2.imshow("Gray", gray)
        cv2.imshow("Frame Delta", cv2.absdiff(gray, cv2.convertScaleAbs(avg)))

        # Check for 'q' key press to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("User terminated the program.")
            break

    # Clean up
    video.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()