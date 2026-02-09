import csv
import os
from datetime import datetime
from typing import List, Dict


def safe_name(name: str, max_len: int = 18) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        return "Player"
    cleaned = cleaned.replace(",", " ").replace("\n", " ").replace("\r", " ")
    return cleaned[:max_len]


def ensure_csv_header(path: str, header: List[str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(header)


def append_solo_score(path: str, name: str, score: int, speed: int, level: int, lines: int) -> None:
    ensure_csv_header(path, ["timestamp", "name", "score", "speed", "level", "lines"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow([timestamp, safe_name(name), int(score), int(speed), int(level), int(lines)])


def append_match_results(path: str, results: List[Dict]) -> None:
    ensure_csv_header(path, ["timestamp", "name", "score", "is_cpu"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        for result in results:
            writer.writerow(
                [
                    timestamp,
                    safe_name(result.get("name", "Player")),
                    int(result.get("score", 0)),
                    bool(result.get("is_cpu", False)),
                ]
            )


def get_top_scores(path: str, top_n: int = 5) -> List[Dict]:
    if not os.path.exists(path):
        return []

    best_by_name: Dict[str, int] = {}

    with open(path, "r", newline="", encoding="utf-8") as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            player_name = safe_name(row.get("name", "Player"))
            try:
                score_value = int(row.get("score", 0))
            except ValueError:
                score_value = 0

            if player_name not in best_by_name or score_value > best_by_name[player_name]:
                best_by_name[player_name] = score_value

    sorted_rows = sorted(best_by_name.items(), key=lambda item: item[1], reverse=True)[:top_n]
    return [{"rank": rank, "name": name, "score": score} for rank, (name, score) in enumerate(sorted_rows, start=1)]