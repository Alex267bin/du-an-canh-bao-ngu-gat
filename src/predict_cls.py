from ultralytics import YOLO

import os

# Lấy đường dẫn thư mục gốc của dự án (HeThongCanhBaoNguGat) dựa vào vị trí file này
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "best_cls.pt")

# Khởi tạo model một lần duy nhất khi import để tránh load đi load lại làm chậm real-time
model = YOLO(MODEL_PATH)

def predict_eye_status(frame):
    """
    Hàm nhận vào frame từ webcam, chạy qua model YOLOv8-cls 
    và trả về danh sách kết quả gồm label và độ tự tin (conf).
    """
    results = model(frame, verbose=False) # verbose=False để tắt log rác của YOLO khi chạy real-time
    
    eyes_data = []
    
    for r in results:
        # Lấy thông tin xác suất (probabilities) của model phân loại (classification)
        if r.probs is not None:
            pred_idx = r.probs.top1
            conf = r.probs.top1conf.item()
            
            # Lấy tên của class dựa vào index (Ví dụ: 'Closed_Eyes' hoặc 'Open_Eyes')
            label = r.names[pred_idx]
            
            eyes_data.append({
                'label': label,
                'conf': conf
            })
            
    return eyes_data

# Giữ lại hàm main cũ để bạn vẫn có thể test chạy riêng file này bằng ảnh độc lập nếu muốn
def main():
    image_path = "/Users/alex/HeThongCanhBaoNguGat/dataset/images/test/Closed_Eyes/s0001_00001_0_0_0_0_0_01.png"
    import cv2
    img = cv2.imread(image_path)
    if img is not None:
        res = predict_eye_status(img)
        print("Kết quả test ảnh tĩnh:", res)
    else:
        print("Không tìm thấy ảnh test tại đường dẫn đã cấu hình.")

if __name__ == "__main__":
    main()