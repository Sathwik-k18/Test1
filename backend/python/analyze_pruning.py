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


def detect_branch_lines(image: np.ndarray) -> List[BranchCandidate]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 140)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=35,
        minLineLength=25,
        maxLineGap=12,
    )

    branches = []
    if lines is None:
        return branches

    idx = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < 20:
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
    density_radius = max(35, int(min(h, w) * 0.09))
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
            if dist < 28 and angle_delta > 30:
                overlaps += 1

        score = 0.0
        reasons = []

        # Rule 1: Overcrowded area
        if local_neighbors >= 5:
            score += 0.4
            reasons.append("Overcrowded area")

        # Rule 2: Blocking sunlight (branch grows inward toward center)
        cx, cy = w / 2.0, h / 2.0
        vec_to_center = np.array([cx - mx, cy - my])
        vec_branch = np.array([branch.x2 - branch.x1, branch.y2 - branch.y1])
        dot = float(np.dot(vec_to_center, vec_branch))
        if dot > 0 and abs(branch.angle_deg) < 70:
            score += 0.3
            reasons.append("Blocking sunlight")

        # Rule 3: Weak branch (very short)
        if branch.length < 40:
            score += 0.35
            reasons.append("Weak branch")

        # Rule 4: Crossing / overlap
        if overlaps >= 2:
            score += 0.35
            reasons.append("Overlapping branch")

        if score >= 0.5:
            radius = int(max(10, min(35, branch.length * 0.18)))
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
        label = f"{s.reason} ({s.confidence})"
        cv2.putText(
            annotated,
            label,
            (s.center_x + 5, max(15, s.center_y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )
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
        },
        "suggestions": [asdict(s) for s in suggestions],
    }

    print(json.dumps(response))


if __name__ == "__main__":
    main()
