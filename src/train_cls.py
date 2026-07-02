from ultralytics import YOLO
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "dataset" / "images"

    print("Project root:", project_root)
    print("Data dir:", data_dir)
    print("Train folder exists:", (data_dir / "train").exists())
    print("Val folder exists:", (data_dir / "val").exists())
    print("Test folder exists:", (data_dir / "test").exists())

    model = YOLO("yolov8n-cls.pt")

    model.train(
        data=str(data_dir),
        epochs=20,
        imgsz=64,
        batch=32,
        name="eye_state_cls"
    )

if __name__ == "__main__":
    main()