"""Development command-line entry point for the packaged local renderer."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.local_renderer import generate


if __name__ == "__main__":
    paths = generate(Path(sys.argv[1]).resolve())
    print(json.dumps({"files": [str(path) for path in paths], "generated_at": datetime.now(timezone.utc).isoformat()}))
