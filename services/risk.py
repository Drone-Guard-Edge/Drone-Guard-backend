from models import RiskLevel, Detection

# ── 위험도 임계값 ─────────────────────────────────────────────────

THRESHOLDS: dict[RiskLevel, float] = {
    "HIGH":   0.85,
    "MEDIUM": 0.60,
    "LOW":    0.30,
}

RISK_PRIORITY: list[RiskLevel] = ["HIGH", "MEDIUM", "LOW", "NONE"]


# ── 단건 confidence → 위험도 ─────────────────────────────────────

def get_risk_level(confidence: float) -> RiskLevel:
    """confidence 수치 하나를 위험도 레벨로 변환"""
    if confidence >= THRESHOLDS["HIGH"]:
        return "HIGH"
    if confidence >= THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    if confidence >= THRESHOLDS["LOW"]:
        return "LOW"
    return "NONE"


# ── 복수 탐지 중 최고 위험도 ─────────────────────────────────────

def get_max_risk(detections: list[Detection]) -> RiskLevel:
    """탐지 목록에서 가장 높은 위험도 반환"""
    if not detections:
        return "NONE"
    levels = [get_risk_level(d.confidence) for d in detections]
    for level in RISK_PRIORITY:
        if level in levels:
            return level
    return "NONE"


def compare_risk(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    """두 위험도 중 더 높은 것 반환"""
    if RISK_PRIORITY.index(a) <= RISK_PRIORITY.index(b):
        return a
    return b


# ── 스냅샷용 통계 ─────────────────────────────────────────────────

def calc_avg_confidence(confidences: list[float]) -> float:
    """평균 confidence, 소수점 4자리 반올림"""
    if not confidences:
        return 0.0
    return round(sum(confidences) / len(confidences), 4)