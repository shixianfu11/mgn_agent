from tools.material_tools import calculate_density
from tools.rdf import calculate_rdf
from tools.cn import calculate_cn


TOOL_REGISTRY = {
    "density": calculate_density,
    "rdf": calculate_rdf,
    "coordination_number": calculate_cn
}