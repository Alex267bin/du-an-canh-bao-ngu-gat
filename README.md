# Hệ thống cảnh báo ngủ gật cho tài xế

Hệ thống này phát hiện tài xế ngủ gật bằng EAR và PERCLOS, sử dụng OpenCV và dlib.

## Cách chạy

```bash
python3 src/main.py --camera 0 --log-file /path/to/drowsiness_log.csv --snapshot-dir /path/to/snapshots
```

## Yêu cầu dữ liệu

File mô hình `shape_predictor_68_face_landmarks.dat` hiện được quản lý bằng Git LFS.

### Tải file mô hình

1. Truy cập: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
2. Giải nén file:

```bash
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
```

3. Di chuyển file đã giải nén vào thư mục `src/`:

```bash
mv shape_predictor_68_face_landmarks.dat src/
```

## Git LFS

Đã cấu hình `git-lfs` cho file `src/shape_predictor_68_face_landmarks.dat`.
