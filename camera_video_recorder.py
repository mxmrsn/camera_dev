import cv2
from datetime import datetime
import time
from tkinter.filedialog import asksaveasfilename
import subprocess

# --- SETTINGS ---
CAM_INDEX = '/dev/video0'
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30
LOG_INTERVAL_SEC = 5

def main():
    start_time = datetime.now()
    timestamp_str = start_time.strftime("%Y%m%d_%H%M%S")
    
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    print(f"Camera resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

    filename = asksaveasfilename(title="Save video as", defaultextension=".mp4",
                                 initialfile=f"recording_{timestamp_str}.mp4",
                                 filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 1.0/LOG_INTERVAL_SEC, (FRAME_WIDTH, FRAME_HEIGHT))
    print(f"Recording started. Saving to: {filename}")
    
    last_capture_time = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error reading from camera")
            break

        now = time.time()
        if now - last_capture_time >= LOG_INTERVAL_SEC:
            now_str = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            cv2.putText(frame, now_str, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            out.write(frame)
            last_capture_time = now
            print(f"Captured frame at {datetime.now().strftime('%H:%M:%S')}")

        cv2.imshow("Camera Preview", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Recording stopped by user")
            break

    # --- CLEANUP ---
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def find_econ_135cug() -> str:
    output = subprocess.check_output("v4l2-ctl --list-devices", shell=True).decode()
    print('output:', output)
    for i, s in enumerate(output):
        SEECAM_idx = s.find("See3CAM_CU135")
        if SEECAM_idx != -1:
            print("Found See3CAM_CU135 at index", i+2)
            return str(output[i+2])

if __name__ == "__main__":
    main()