from pydantic import BaseModel
from typing import Literal

class AnalysisRequest (BaseModel):
    file_path: str | None = None
    tasks : list[
        Literal["rdf", 
                "adf",
                "coordination_number",
                 "quality_check",
                  "density" ]
    ]


    temperature: float | None = None
    num_structures: int | None = None

    num_atoms: int | None = None
    volume_angstrom3: float | None = None