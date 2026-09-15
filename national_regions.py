# 3호 전국 지역 DB - 기존 gen.py와 독립
import json
from pathlib import Path
REGIONS = json.loads((Path(__file__).with_name('national_regions.json')).read_text(encoding='utf-8'))
