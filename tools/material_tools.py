AVOGADRO = 6.02214076e23
TE_ATOMIC_MASS = 127.60  # g/mol


def calculate_density(num_atoms: int, volume_angstrom3: float) -> float:
    """
    根据 Te 原子数和晶胞体积计算密度。

    Parameters
    ----------
    num_atoms : int
        Te 原子数量。

    volume_angstrom3 : float
        晶胞体积，单位 Å^3。

    Returns
    -------
    float
        密度，单位 g/cm^3。
    """

    mass_g = num_atoms * TE_ATOMIC_MASS / AVOGADRO

    volume_cm3 = volume_angstrom3 * 1e-24

    density = mass_g / volume_cm3

    return density

def analyze_rdf(first_peak_position: float,first_peak_height: float | None = None) -> dict:
    """
    根据 RDF 第一峰信息进行简单结构分析。

    Parameters
    ----------
    first_peak_position : float
        RDF 第一峰位置，单位 Å。

    first_peak_height : float | None
        RDF 第一峰高度，可选。

    Returns
    -------
    dict
        RDF 第一峰分析结果。
    """

    result = {
        "first_peak_position_angstrom": first_peak_position,
        "interpretation": (
            f"RDF 第一峰位于 {first_peak_position:.3f} Å，"
            "通常对应体系中最近邻原子之间的典型距离，"
            "反映第一配位壳层的局域结构。"
        )
    }

    if first_peak_height is not None:
        result["first_peak_height"] = first_peak_height
        result["peak_height_interpretation"] = (
            "峰高反映该距离附近原子对出现的相对概率，"
            "但不能仅凭峰高直接得到配位数。"
        )

    return result