from app.core.config import PRIORITY_ORDER


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(value, maximum))


def format_percentage(value: float, decimals: int = 1) -> str:
    value = clamp(value)
    if float(value).is_integer():
        return f"{int(value)}%"
    return f"{value:.{decimals}f}%"


def format_ratio(
    numerator: float,
    denominator: float,
    decimals: int = 1,
    fallback: str = "0%",
) -> str:
    if denominator <= 0:
        return fallback
    return format_percentage(safe_divide(numerator, denominator) * 100, decimals)


def range_attainment(actual: int, minimum: int, maximum: int) -> float:
    if actual <= 0:
        return 0.0
    if minimum <= actual <= maximum:
        return 100.0
    if actual < minimum:
        return clamp(safe_divide(actual, minimum) * 100)
    return clamp(safe_divide(maximum, actual) * 100)


def status_from_score(score: float) -> str:
    if score >= 90:
        return "Good"
    if score >= 80:
        return "At Benchmark"
    if score >= 50:
        return "Needs Improvement"
    return "Critical Gap"


def priority_from_score(score: float, hard_fail: bool = False) -> str:
    if hard_fail or score < 40:
        return "High"
    if score < 80:
        return "Medium"
    return "Low"


def minimum_attainment(actual: float, minimum: float) -> float:
    if minimum <= 0:
        return clamp(actual)
    if actual >= minimum:
        return 100.0
    return clamp(safe_divide(actual, minimum) * 100)


def maximum_attainment(actual: float, maximum: float) -> float:
    if maximum <= 0:
        return 100.0 if actual <= 0 else 0.0
    if actual <= maximum:
        return 100.0
    return clamp(100 - ((actual - maximum) / maximum) * 100)


def weighted_score(score_map: dict[str, float], weights: dict[str, int]) -> float:
    total_weight = sum(weights.values())
    if not total_weight:
        return 0.0

    weighted_total = sum(score_map.get(key, 0.0) * weight for key, weight in weights.items())
    return round(weighted_total / total_weight, 1)


def sort_by_priority(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda item: PRIORITY_ORDER.get(item.get("priority"), 99))
