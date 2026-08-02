# tests/test_boundary_detector.py

import numpy as np
from PIL import Image
from core.boundary_detector import (
    FullFrameBoundary, ManualBoundary,
    detect_content_box, detect_margins, create_detector
)


def test_full_frame_boundary():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    det = FullFrameBoundary()
    left, right = det.detect(img)
    assert left == 0
    assert right == 200


def test_manual_boundary():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    det = ManualBoundary(left=10, right=150)
    left, right = det.detect(img)
    assert left == 10
    assert right == 150


def test_manual_boundary_default_right():
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    det = ManualBoundary(left=10, right=0)
    left, right = det.detect(img)
    assert left == 10
    assert right == 200


def test_detect_content_box_simple():
    # 白背景 + 黒矩形
    img = Image.new("RGB", (100, 100), "white")
    for x in range(20, 80):
        for y in range(30, 70):
            img.putpixel((x, y), (0, 0, 0))

    box = detect_content_box(img)
    assert box == (20, 30, 80, 70)


def test_detect_margins():
    img = Image.new("RGB", (100, 100), "white")
    for x in range(10, 90):
        for y in range(20, 80):
            img.putpixel((x, y), (0, 0, 0))

    margins = detect_margins(img)
    assert margins == (10, 10, 20, 20)


def test_create_detector():
    det = create_detector("manual", manual_left=5, manual_right=50)
    assert isinstance(det, ManualBoundary)
    det2 = create_detector("full")
    assert isinstance(det2, FullFrameBoundary)
