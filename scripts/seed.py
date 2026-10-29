"""灌入演示数据（从项目根目录运行）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.data.seed import seed  # noqa: E402

if __name__ == "__main__":
    seed()
