"""Run pytest using ordinary workspace temp folders on restricted Windows hosts."""
from pathlib import Path
from uuid import uuid4
import pytest


class WorkspaceTemp:
    @pytest.fixture
    def tmp_path(self):
        path = Path('.qa') / uuid4().hex
        path.mkdir(parents=True)
        return path.resolve()


if __name__ == '__main__':
    raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider'], plugins=[WorkspaceTemp()]))
