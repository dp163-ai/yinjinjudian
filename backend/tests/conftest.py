"""pytest 公共配置：确保 app 包可被导入。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
