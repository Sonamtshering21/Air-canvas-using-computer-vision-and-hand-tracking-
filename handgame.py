import cv2
import numpy as np
import mediapipe as mp
import time

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Webcam
cap = cv2.VideoCapture(0)

# Canvas
canvas = np.zeros((480, 640, 3), np.uint8)

# Colors
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 255)]  # Red, Green, Blue, Eraser
color_names = ['Red', 'Green', 'Blue', 'Eraser']
current_color = colors[0]
color_index = 0

# Brush and Eraser Thickness
brush_thickness = 8
eraser_thickness = 50

# Previous points
xp, yp = 0, 0

# Finger Tip IDs
tip_ids = [4, 8, 12, 16, 20]

# Font
font = cv2.FONT_HERSHEY_SIMPLEX

# Timer for save confirmation
save_time = 0
show_save_msg = False

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            lm_list = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = frame.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))

            fingers = []

            if lm_list:
                # Thumb
                if lm_list[tip_ids[0]][1] > lm_list[tip_ids[0] - 1][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)

                # Other 4 Fingers
                for id in range(1, 5):
                    if lm_list[tip_ids[id]][2] < lm_list[tip_ids[id] - 2][2]:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                total_fingers = fingers.count(1)

                # Only Index Finger Up -> Drawing Mode
                if fingers[1] == 1 and fingers[2] == 0:
                    cx, cy = lm_list[8][1], lm_list[8][2]

                    if xp == 0 and yp == 0:
                        xp, yp = cx, cy

                    if current_color == (255, 255, 255):
                        # Erase by drawing black (not white!)
                        cv2.line(canvas, (xp, yp), (cx, cy), (0, 0, 0), eraser_thickness)
                    else:
                        cv2.line(canvas, (xp, yp), (cx, cy), current_color, brush_thickness)

                    xp, yp = cx, cy

                # Both Index and Middle Fingers Up -> Selection Mode
                if fingers[1] == 1 and fingers[2] == 1:
                    xp, yp = 0, 0
                    cx, cy = lm_list[8][1], lm_list[8][2]

                    # Top Menu Area
                    if 10 < cy < 70:
                        if 40 < cx < 120:
                            color_index = 0
                            current_color = colors[color_index]
                        elif 140 < cx < 220:
                            color_index = 1
                            current_color = colors[color_index]
                        elif 240 < cx < 320:
                            color_index = 2
                            current_color = colors[color_index]
                        elif 340 < cx < 420:
                            color_index = 3
                            current_color = colors[color_index]

                # Three Fingers Up -> Increase Brush Size
                if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
                    brush_thickness += 1
                    if brush_thickness > 50:
                        brush_thickness = 50
                    time.sleep(0.2)

                # Four Fingers Up -> Decrease Brush Size
                if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
                    brush_thickness -= 1
                    if brush_thickness < 5:
                        brush_thickness = 5
                    time.sleep(0.2)

    # Merge canvas and frame
    gray_canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, inv_canvas = cv2.threshold(gray_canvas, 50, 255, cv2.THRESH_BINARY_INV)
    inv_canvas = cv2.cvtColor(inv_canvas, cv2.COLOR_GRAY2BGR)
    frame = cv2.bitwise_and(frame, inv_canvas)
    frame = cv2.bitwise_or(frame, canvas)

    # Draw color menu
    cv2.rectangle(frame, (40, 10), (120, 70), (0, 0, 255), -1)
    cv2.rectangle(frame, (140, 10), (220, 70), (0, 255, 0), -1)
    cv2.rectangle(frame, (240, 10), (320, 70), (255, 0, 0), -1)
    cv2.rectangle(frame, (340, 10), (420, 70), (255, 255, 255), -1)

    # Show current color name
    cv2.putText(frame, color_names[color_index], (450, 50), font, 1, (0, 0, 0), 2)

    # Show brush size
    cv2.putText(frame, f'Brush: {brush_thickness}', (10, 470), font, 1, (0, 0, 255), 2)

    # Show save confirmation
    if show_save_msg:
        if time.time() - save_time < 2:  # show for 2 seconds
            cv2.putText(frame, 'Saved!', (250, 240), font, 2, (0, 255, 0), 3)
        else:
            show_save_msg = False

    # Display
    cv2.imshow('Air Canvas Pro', frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    if key == ord('c'):
        canvas = np.zeros((480, 640, 3), np.uint8)
    if key == ord('s'):
        filename = f'air_canvas_{int(time.time())}.png'
        cv2.imwrite(filename, frame)
        save_time = time.time()
        show_save_msg = True

cap.release()
cv2.destroyAllWindows()
