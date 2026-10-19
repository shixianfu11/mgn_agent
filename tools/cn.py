from pathlib import Path
import numpy as np
from ase.io import read
from ase.geometry import get_distances


def distance_matrix(
    scaled_positions: np.ndarray,
    lattice: np.ndarray,
) -> np.ndarray:
    """
    Calculate pairwise distances using ASE's MIC.
    Supports non-orthogonal periodic cells.
    """

    # Fractional -> Cartesian coordinates
    cart_positions = scaled_positions @ lattice

    # Minimum image convention
    _, distances = get_distances(
        cart_positions,
        cell=lattice,
        pbc=[True, True, True],
    )

    return distances


def calculate_cn_for_frame(
    distances: np.ndarray,
    cutoff: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate coordination number for every atom in one frame.

    Parameters
    ----------
    distances : np.ndarray
        Pairwise distance matrix.

    cutoff : float
        Distance cutoff in Angstrom.

    Returns
    -------
    cn_per_atom : np.ndarray
        Coordination number of every atom.

    neighbor_matrix : np.ndarray
        Boolean neighbor matrix.
    """

    # Two atoms are regarded as neighbors when r <= cutoff
    neighbor_matrix = distances <= cutoff

    # An atom cannot be its own neighbor, diagonal = False
    np.fill_diagonal(neighbor_matrix, False)

    # Count neighbors of every atom,line sum (N,)
    cn_per_atom = np.sum(
        neighbor_matrix,
        axis=1,
    )

    return cn_per_atom, neighbor_matrix


def calculate_cn(
    file_path: str,
    cutoff: float = 3.2,
    max_cn: int = 15,
) -> dict:
    """
    Calculate coordination-number statistics from a structure file.

    Parameters
    ----------
    file_path : str
        Path to an ASE-readable structure file.

    cutoff : float
        Coordination cutoff in Angstrom.

    max_cn : int
        Maximum CN included in the distribution.

    Returns
    -------
    dict
        JSON-serializable coordination-number result.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Structure file not found: {file_path}"
        )

    if cutoff <= 0:
        raise ValueError(
            "cutoff must be greater than 0."
        )

    if max_cn < 1:
        raise ValueError(
            "max_cn must be at least 1."
        )

    # Read all frames
    atoms_list = read(
        file_path,
        index=":",
    )

    if len(atoms_list) == 0:
        raise ValueError(
            f"No structure frames found in {file_path}"
        )

    total_counts = np.zeros(
        max_cn + 1,
        dtype=float,
    )

    all_cn = []

    for atoms in atoms_list:

        lattice = atoms.get_cell().array

        scaled_positions = atoms.get_scaled_positions()

        distances = distance_matrix(
            scaled_positions,
            lattice,
        )

        cn_per_atom, _ = calculate_cn_for_frame(
            distances,
            cutoff,
        )

        if np.max(cn_per_atom) > max_cn:
            raise ValueError(
                f"Observed CN {np.max(cn_per_atom)} "
                f"is larger than max_cn={max_cn}."
            )

        counts = np.bincount(
            cn_per_atom,
            minlength=max_cn + 1,
        )

        total_counts += counts

        all_cn.extend(
            cn_per_atom.tolist()
        )

    all_cn = np.asarray(all_cn)

    # CN = 0, 1, 2, ...
    total = np.sum(total_counts)

    percentages = (
        total_counts / total * 100
    )

    distribution = {
        str(cn): float(percentages[cn])
        for cn in range(max_cn + 1)
        if total_counts[cn] > 0
    }

    result = {
        "metric": "coordination_number",
        "file_path": str(path),
        "num_frames": len(atoms_list),
        "num_atoms": len(atoms_list[0]),
        "cutoff": float(cutoff),
        "max_cn": int(max_cn),
        "mean_cn": float(np.mean(all_cn)),
        "distribution": distribution,
    }

    return result