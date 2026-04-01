import cv2
import pytesseract
from tkinter.filedialog import askopenfilename

def main():
    values = []

    filename = askopenfilename(title="Select a video file", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
    cap = cv2.VideoCapture(filename)

    if not cap.isOpened():
        print("Error opening video file")
        return
    
    # read first frame to define roi
    ret, frame = cap.read()
    if not ret:
        print("Error reading video file")
        return
    print("Select DIGITS roi")
    roi_digits = cv2.selectROI("Digits ROI", frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Digits ROI")

    xd, yd, wd, hd = roi_digits

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        roi_frame = frame[yd:yd+hd, xd:xd+wd]
        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow("ROI", gray)
        value = parse_image(roi_frame)
        if value is not None:
            values.append(value)
            print(f"Frame {frame_count}: {value}")

        if cv2.waitKey(3000) & 0xFF == ord('q'):
            break

        frame_count += 1
    cap.release()
    cv2.destroyAllWindows()

    print("Extracted values:")
    for val in values:
        print(val)

def parse_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    config = r'--psm 7 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(gray, config=config)

    try:
        value = float(text)
        return value
    except ValueError:
        print(f"Could not parse value from text: '{text}'")
        return None

if __name__ == "__main__":
    main()