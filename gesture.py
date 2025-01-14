import cv2
import time
from pathlib import Path
from collections import Counter
import numpy as np
from joblib import load
from mediapipe.python.solutions import drawing_utils, hands
import pyautogui

pyautogui.FAILSAFE= True

print('GESTURE RECOGNITION')
print("Press 'q' to quit")
print("Press 'd' for debug")

debug = False
t = 0
txt_offset = (-60, 30)

# load the models
gesture_model = load('./model/gesture_model.pkl')

hand_model = hands.Hands(static_image_mode=True,
                         min_detection_confidence=0.7,
                         min_tracking_confidence=0.7, max_num_hands=4)

# initialize video capture
vc = cv2.VideoCapture(0, cv2.CAP_DSHOW)
resolution = (vc.get(3), vc.get(4))
gesture_list = []
gesture_id = -1
n = 0
save_dir = '../screenshots'
_save_dir = Path(save_dir)
if not _save_dir.exists():
    _save_dir.mkdir(exist_ok=True)

while vc.isOpened():
    ret, frame = vc.read()
    # get hands model prediction
    results = hand_model.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if results.multi_hand_landmarks:
        for handLandmarks in results.multi_hand_landmarks:
            if debug:
                # draw hand skeleton
                drawing_utils.draw_landmarks(frame, handLandmarks,
                                             hands.HAND_CONNECTIONS)

            # get predicted points
            x, y = [], []
            for lm in handLandmarks.landmark:
                x.append(lm.x)
                y.append(lm.y)

            txt_pos = np.add(np.multiply(resolution, (x[0], y[0])), txt_offset)

            # normalize points
            points = np.asarray([x, y])
            min = points.min(axis=1, keepdims=True)
            max = points.max(axis=1, keepdims=True)
            normalized = np.stack((points-min)/(max-min), axis=1).flatten()

            # get prediction and confidence
            pred = gesture_model.predict_proba([normalized])
            gesture = pred.argmax(axis=1)[0]
            confidence = pred.max()
            gesture_id += 1
            # add text
            cv2.putText(frame, "'{}',{:.1%}".format(gesture, confidence),
                        txt_pos.astype(int), cv2.FONT_HERSHEY_DUPLEX,  1,
                        (0, 255, 255), 1, cv2.LINE_AA)
            gesture_list.append(int(gesture))
            counters = Counter(gesture_list)

            if len(gesture_list) < 500:
                print(gesture_list)
                if counters[5] % 50 == 7:  # 手势五, 截图
                    # pyautogui.hotkey('win', 'shift', 's')
                    name = f'{save_dir}/screenshot-{n}.png'
                    im = pyautogui.screenshot(name)
                    n += 1
                elif gesture == 2:  # 手势二, 向上滚动
                    pyautogui.scroll(10)  # scroll up 10 "clicks"
                elif gesture == 1:  # 手势1, 向下滚动
                    pyautogui.scroll(-10)  # scroll up 10 "clicks"
                elif gesture == 5:
                    pyautogui.hotkey('win', 'shift', 's')
                elif gesture == 0:  # 手势0, copy
                    pyautogui.hotkey('ctrl', 'c')
                elif gesture == 9:  # 手势9cc, 粘  # 手势4, 向上滚动贴
                    pyautogui.hotkey('ctrl','v')
                elif counters[7] % 50 == 7:  # 手势7, 
                    m, n = pyautogui.size()
                    pyautogui.moveTo(x=m / 2, y=n / 2)
                    pyautogui.click()  # 点击屏幕并聚焦
                    distance = 200
                    while distance == 200:
                        pyautogui.drag(distance, 0, duration=0.5)  # 像右移动
                        distance -= 5
                        pyautogui.drag(0, distance, duration=0.5)  # 向下移动
                        pyautogui.drag(-distance, 0, duration=0.5)  # 向左移动
                        distance -= 5
                        pyautogui.drag(0, -distance, duration=0.5)  # 向上移
            else:
                gesture_list = []

    fps = 1/(time.time()-t)
    t = time.time()

    # debug text
    if debug:
        cv2.putText(frame,
                    "{}x{}; {}fps".format(*resolution, int(fps)),
                    (0, 15),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.6, (0, 0, 255), 1, cv2.LINE_AA)

    cv2.imshow('frame', frame)

    # get keyinput
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        vc.release()
    if key == ord('d'):
        debug = not debug

cv2.destroyAllWindows()
