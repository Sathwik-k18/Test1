#!/usr/bin/env python3
import cv2
import json
import math
import numpy as np
import sys
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class BranchCandidate:
    id: int
    x1: int
    y1: int
    x2: int
    y2: int
    length: float
    angle_deg: float


@dataclass
class Suggestion:
    branch_id: int
    center_x: int
    center_y: int
    radius: int
    reason: str
    confidence: float


def build_plant_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    green_mask = cv2.inRange(hsv, (25, 30, 20), (95, 255, 255))
    brown_mask = cv2.inRange(hsv, (5, 30, 20), (30, 255, 220))
    mask = cv2.bitwise_or(green_mask, brown_mask)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def detect_branch_lines(image: np.ndarray) -> List[BranchCandidate]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    plant_mask = build_plant_mask(image)
    filtered = cv2.bitwise_and(gray, gray, mask=plant_mask)
    blurred = cv2.GaussianBlur(filtered, (5, 5), 0)
    edges = cv2.Canny(blurred, 60, 150)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=45,
        minLineLength=35,
        maxLineGap=10,
    )

    branches = []
    if lines is None:
        return branches

    idx = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 30:
            continue

        mx = int((x1 + x2) / 2)
        my = int((y1 + y2) / 2)
        if plant_mask[my, mx] == 0:
            continue

        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        branches.append(
            BranchCandidate(
                id=idx,
                x1=int(x1),
                y1=int(y1),
                x2=int(x2),
                y2=int(y2),
                length=float(length),
                angle_deg=float(angle),
            )
        )
        idx += 1

    return branches


def midpoint(branch: BranchCandidate):
    return int((branch.x1 + branch.x2) / 2), int((branch.y1 + branch.y2) / 2)


def suggest_pruning(branches: List[BranchCandidate], image_shape) -> List[Suggestion]:
    if not branches:
        return []

    h, w = image_shape[:2]
    density_radius = max(35, int(min(h, w) * 0.08))
    suggestions: List[Suggestion] = []

    for i, branch in enumerate(branches):
        mx, my = midpoint(branch)
        local_neighbors = 0
        overlaps = 0

        for j, other in enumerate(branches):
            if i == j:
                continue

            omx, omy = midpoint(other)
            dist = math.hypot(mx - omx, my - omy)

            if dist < density_radius:
                local_neighbors += 1

            angle_delta = abs(branch.angle_deg - other.angle_deg)
            angle_delta = min(angle_delta, 180 - angle_delta)
            if dist < 20 and angle_delta > 35:
                overlaps += 1

        score = 0.0
        reasons = []

        if local_neighbors >= 4:
            score += 0.45
            reasons.append("Overcrowded area")

        cx, cy = w / 2.0, h / 2.0
        vec_to_center = np.array([cx - mx, cy - my])
        vec_branch = np.array([branch.x2 - branch.x1, branch.y2 - branch.y1])
        dot = float(np.dot(vec_to_center, vec_branch))
        if dot > 0 and abs(branch.angle_deg) < 65:
            score += 0.25
            reasons.append("Blocking sunlight")

        if branch.length < 48:
            score += 0.30
            reasons.append("Weak branch")

        if overlaps >= 2:
            score += 0.30
            reasons.append("Overlapping branch")

        if score >= 0.6:
            radius = int(max(10, min(28, branch.length * 0.16)))
            suggestions.append(
                Suggestion(
                    branch_id=branch.id,
                    center_x=mx,
                    center_y=my,
                    radius=radius,
                    reason=", ".join(reasons[:2]),
                    confidence=round(min(score, 0.95), 2),
                )
            )

    return suggestions


def annotate_image(image: np.ndarray, suggestions: List[Suggestion]):
    annotated = image.copy()
    for s in suggestions:
        cv2.circle(annotated, (s.center_x, s.center_y), s.radius, (0, 0, 255), 2)
    return annotated


def main():
    if len(sys.argv) < 3:
        raise ValueError("Usage: analyze_pruning.py <input_path> <output_path>")

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    image = cv2.imread(input_path)
    if image is None:
        raise ValueError("Could not read input image")

    branches = detect_branch_lines(image)
    suggestions = suggest_pruning(branches, image.shape)
    annotated = annotate_image(image, suggestions)

    cv2.imwrite(output_path, annotated)

    response = {
        "stats": {
            "detectedBranches": len(branches),
            "pruneCandidates": len(suggestions),
            "imageWidth": int(image.shape[1]),
            "imageHeight": int(image.shape[0]),
        },
        "suggestions": [asdict(s) for s in suggestions],
    }

    print(json.dumps(response))


if __name__ == "__main__":
    main()
