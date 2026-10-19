from pathlib import Path

from ase import Atoms
from ase.io import read


def validate_structure(atoms: Atoms, file_path: str) -> None:
    """检查单个结构是否合法。"""

    if len(atoms) == 0:
        raise ValueError(
            f"结构文件中没有原子: {file_path}"
        )

    if atoms.cell.volume <= 0:
        raise ValueError(
            "结构缺少有效晶胞，无法进行周期结构分析。"
        )

    if not atoms.pbc.all():
        raise ValueError(
            "结构未定义三维周期边界条件。"
        )


def load_structures(file_path: str) -> list[Atoms]:
    """读取文件中的全部结构帧。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"结构文件不存在: {file_path}"
        )

    frames = read(path, index=":")

    if len(frames) == 0:
        raise ValueError(
            f"结构文件中没有结构帧: {file_path}"
        )

    for i, atoms in enumerate(frames):
        try:
            validate_structure(atoms, file_path)

        except ValueError as e:
            raise ValueError(
                f"第 {i} 帧结构无效: {e}"
            ) from e

    return frames

def load_structure(file_path: str) -> Atoms:
    """读取单帧结构。"""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"结构文件不存在: {file_path}"
        )

    frames = read(path, index=":")

    if len(frames) != 1:
        raise ValueError(
            f"期望单帧结构，但文件包含 {len(frames)} 帧: {file_path}"
        )

    return frames[0]