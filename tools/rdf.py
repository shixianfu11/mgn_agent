import numpy as np
from ase.io import read
from ase import Atoms
from ase.neighborlist import neighbor_list


def calculate_single_rdf(
    atoms: Atoms,
    r_max: float = 8.0,
    bins: int = 200
) -> dict:

    # 1. 计算 r_max 范围内所有周期原子对距离
    distances = neighbor_list(
        "d",
        atoms,
        r_max
    )

    # 2. 把距离统计到不同的 r 区间
    hist, bin_edges = np.histogram(
        distances,
        bins=bins,
        range=(0.0, r_max)
    )

    # 3. 每个原子的平均邻居数
    hist = hist / len(atoms)

    # 4. 系统平均原子数密度 N / V
    rho_mean = len(atoms) / atoms.cell.volume

    # 5. 每个球壳的体积
    shell_volume = (
        4.0
        * np.pi
        / 3.0
        * (
            bin_edges[1:] ** 3
            - bin_edges[:-1] ** 3
        )
    )

    # 6. 每个球壳内实际的平均原子密度
    rho_r = hist / shell_volume

    # 7. RDF: g(r)
    g_r = rho_r / rho_mean

    # 8. 每个 bin 的中心位置
    r = 0.5 * (
        bin_edges[:-1]
        + bin_edges[1:]
    )

    return {
        "r": r,
        "g_r": g_r
    }

def calculate_rdf(
    file_path: str,
    r_max: float = 8.0,
    bins: int = 200,
) -> dict:

    # 1. 读取所有结构帧
    frames = read(file_path, index=":")

    if len(frames) == 0:
        raise ValueError("No structures found")

    # 2. 存储每一帧的 RDF
    all_g_r = []

    for atoms in frames:

        result = calculate_single_rdf(
            atoms,
            r_max=r_max,
            bins=bins,
        )

        all_g_r.append(result["g_r"])

    # 3. 对各帧 RDF 求平均
    mean_g_r = np.mean(all_g_r, axis=0)

    return {
        # 文件级工具返回标准 JSON 数据，底层计算仍使用 NumPy 数组。
        "r": result["r"].tolist(),
        "g_r": mean_g_r.tolist(),
        "num_frames": len(frames),
    }
