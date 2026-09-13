import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def run_command(cmd: list[str], description: str = "command", env: dict = None, cwd: str = None):
    """
    Executes a system command with error handling and logging.
    """
    logger.info(f"Executing {description}...")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env or os.environ.copy(), cwd=cwd)
    if result.returncode != 0:
        error_msg = f"Error in {description} (code {result.returncode}): {result.stderr}"
        logger.error(error_msg)
        raise Exception(error_msg)
    return result
