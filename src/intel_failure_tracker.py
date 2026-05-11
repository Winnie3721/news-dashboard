"""記錄 intel 生成連續失敗次數,判斷是否要觸發警報。"""
from pathlib import Path


class FailureTracker:
    def __init__(self, path: Path):
        self.path = Path(path)

    def count(self) -> int:
        if not self.path.exists():
            return 0
        try:
            return int(self.path.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            return 0

    def record_failure(self) -> None:
        n = self.count() + 1
        self.path.write_text(str(n), encoding="utf-8")

    def reset(self) -> None:
        self.path.write_text("0", encoding="utf-8")

    def should_alert(self, threshold: int = 3) -> bool:
        return self.count() >= threshold
