import argparse
import cv2
import dlib
import datetime
import numpy as np
import os
from fatigue_logic import DrowsinessMonitor
from alert import play_alarm, stop_alarm, set_audio_enabled
from logger import log_event, send_system_notification


def save_drowsy_snapshot(frame, output_dir, avg_ear, perclos):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"drowsy_{timestamp}_EAR{avg_ear:.2f}_PERCLOS{int(perclos * 100)}.jpg"
    path = os.path.join(output_dir, filename)
    cv2.imwrite(path, frame)
    return path


def draw_hud_dashboard(frame, ear_val, perclos, is_drowsy, no_face=False):
    overlay = frame.copy()
    x1, y1, x2, y2 = 30, 100, 380, 400
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (40, 40, 40), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 200, 200), 2)

    status_text = "NGỦ GẬT" if is_drowsy else "BÌNH THƯỜNG"
    status_color = (0, 0, 255) if is_drowsy else (0, 255, 0)
    face_text = "Không thấy" if no_face else "Đã thấy"
    cv2.putText(frame, f"Trạng thái: {status_text}", (x1 + 10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    cv2.line(frame, (x1, y1 + 45), (x2, y1 + 45), (200, 200, 200), 1)

    metrics = [
        ("EAR:", f"{ear_val:.2f}"),
        ("Ngưỡng EAR:", f"{0.21:.2f}"),
        ("PERCLOS:", f"{perclos * 100:.0f}%"),
        ("Phát hiện mặt:", face_text),
        ("Tình trạng:", status_text),
    ]

    row_y = y1 + 80
    for label, val in metrics:
        cv2.putText(frame, label, (x1 + 15, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1)
        color = status_color if label == "Drowsiness:" else (255, 255, 255)
        cv2.putText(frame, val, (x1 + 180, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        cv2.line(frame, (x1 + 10, row_y + 16), (x2 - 10, row_y + 16), (70, 70, 70), 1)
        row_y += 45


def parse_arguments():
    parser = argparse.ArgumentParser(description="Driver drowsiness detection using EAR and dlib landmarks.")
    parser.add_argument("--camera", type=int, default=0, help="Camera index to use.")
    parser.add_argument("--predictor", type=str, default=None, help="Path to shape_predictor_68_face_landmarks.dat")
    parser.add_argument("--disable-audio", action="store_true", help="Disable alarm sound.")
    parser.add_argument("--ear-threshold", type=float, default=0.21, help="EAR threshold for closed eyes.")
    parser.add_argument("--sleep-seconds", type=float, default=2.0, help="Seconds of continuous eye closure before alarm.")
    parser.add_argument("--perclos-window", type=int, default=30, help="Number of frames used to compute PERCLOS.")
    parser.add_argument("--perclos-threshold", type=float, default=0.6, help="PERCLOS threshold to trigger alarm.")
    parser.add_argument("--log-file", type=str, default=None, help="Path to save drowsiness event log.")
    parser.add_argument("--snapshot-dir", type=str, default=None, help="Directory to save drowsy snapshots.")
    return parser.parse_args()


def main():
    args = parse_arguments()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    predictor_path = args.predictor or os.path.join(BASE_DIR, "shape_predictor_68_face_landmarks.dat")

    if not os.path.isfile(predictor_path):
        print(f"Lỗi: Không tìm thấy file predictor tại {predictor_path}")
        return

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    set_audio_enabled(not args.disable_audio)

    monitor = DrowsinessMonitor(
        threshold_seconds=args.sleep_seconds,
        ear_threshold=args.ear_threshold,
        perclos_window=args.perclos_window,
        perclos_threshold=args.perclos_threshold,
    )

    log_file = args.log_file or os.path.join(BASE_DIR, "drowsiness_log.csv")
    snapshot_dir = args.snapshot_dir or os.path.join(BASE_DIR, "snapshots")
    previous_state = None

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Lỗi: Không thể mở camera {args.camera}")
        return

    print("Hệ thống Drowsiness EAR đang chạy...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc frame từ camera. Kết thúc.")
            break

        h, w, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)

        avg_ear = 0.35
        perclos = monitor.perclos
        is_drowsy = False

        no_face = len(rects) == 0
        if no_face:
            monitor.register_no_face()
            perclos = monitor.perclos
        else:
            rect = rects[0]
            shape = predictor(gray, rect)
            shape_np = np.array([[p.x, p.y] for p in shape.parts()])

            left_eye = shape_np[36:42]
            right_eye = shape_np[42:48]

            left_ear = monitor.calculate_ear(left_eye)
            right_ear = monitor.calculate_ear(right_eye)
            is_drowsy, avg_ear, perclos = monitor.update(left_ear, right_ear)

            box_color = (0, 0, 255) if is_drowsy else (0, 255, 0)
            cv2.rectangle(frame, (rect.left(), rect.top()), (rect.right(), rect.bottom()), box_color, 2)

            for (x, y) in np.concatenate((left_eye, right_eye), axis=0):
                cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)

        current_state = "NO_FACE" if no_face else "DROWSY" if is_drowsy else "NORMAL"
        if current_state != previous_state:
            message = "Không phát hiện khuôn mặt" if no_face else (
                f"Ngủ gật: EAR {avg_ear:.2f}, PERCLOS {perclos * 100:.0f}%" if is_drowsy else "Lái xe bình thường"
            )
            if current_state == "DROWSY":
                snapshot_path = save_drowsy_snapshot(frame, snapshot_dir, avg_ear, perclos)
                message += f" (Ảnh lưu: {os.path.basename(snapshot_path)})"
            log_event(log_file, current_state, avg_ear, perclos, not no_face, message)
            if current_state in ("NO_FACE", "DROWSY"):
                send_system_notification("Cảnh báo lái xe", message)
            previous_state = current_state

        draw_hud_dashboard(frame, avg_ear, perclos, is_drowsy, no_face)

        if no_face:
            top_bar = frame.copy()
            cv2.rectangle(top_bar, (0, 0), (w, 55), (0, 165, 255), -1)
            cv2.addWeighted(top_bar, 0.3, frame, 0.7, 0, frame)
            cv2.putText(frame, "CẢNH BÁO: Không tìm thấy khuôn mặt", (30, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            stop_alarm()
        elif is_drowsy:
            top_bar = frame.copy()
            cv2.rectangle(top_bar, (0, 0), (w, 55), (0, 0, 255), -1)
            cv2.addWeighted(top_bar, 0.3, frame, 0.7, 0, frame)
            cv2.putText(frame, f"CẢNH BÁO NGỦ GẬT! EAR {avg_ear:.2f} | PERCLOS {perclos * 100:.0f}%", (30, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            play_alarm()
        else:
            top_bar = frame.copy()
            cv2.rectangle(top_bar, (0, 0), (w, 55), (0, 255, 0), -1)
            cv2.addWeighted(top_bar, 0.15, frame, 0.85, 0, frame)
            cv2.putText(frame, f"TRẠNG THÁI: TỈNH (EAR: {avg_ear:.2f})", (30, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            stop_alarm()

        cv2.imshow("Driver Drowsiness EAR HUD System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
