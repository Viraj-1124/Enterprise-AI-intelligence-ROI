"""Run AgentEval suites locally: python scripts/agent_eval.py run <suite>"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agent_eval.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
