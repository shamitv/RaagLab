"""Run Phase 04 unit, real-service and API-served browser checks in isolation."""
import os
from pathlib import Path
import runpy

os.environ["MUSEFORGE_TEST_PROJECT_PREFIX"] = "museforge-phase4-test-"
os.environ["PHASE4_BROWSER"] = "1"
runpy.run_path(str(Path(__file__).with_name("verify-phase2.py")), run_name="__main__")
