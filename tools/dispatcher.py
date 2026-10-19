from schemas import AnalysisRequest
from tools.registry import TOOL_REGISTRY


def dispatch_request(request: AnalysisRequest) -> dict:
    """按请求顺序执行工具，将预期失败记录为结果，继续后续任务。"""
    results = {}

    for task in request.tasks:
        # 注册、参数检查和计算都属于当前任务，统一放在这一轮 try 中。
        try:
            if task not in TOOL_REGISTRY:
                raise NotImplementedError(
                    f"任务 '{task}' 尚未接入可执行 Tool"
                )

            tool_function = TOOL_REGISTRY[task]

            if task == "density":
                if request.num_atoms is None:
                    raise ValueError("density 任务缺少 num_atoms")
                if request.volume_angstrom3 is None:
                    raise ValueError("density 任务缺少 volume_angstrom3")
                if request.num_atoms <= 0:
                    raise ValueError("density 的 num_atoms 必须大于 0")
                if request.volume_angstrom3 <= 0:
                    raise ValueError("density 的 volume_angstrom3 必须大于 0")

                value = tool_function(
                    num_atoms=request.num_atoms,
                    volume_angstrom3=request.volume_angstrom3,
                )
                data = {"density_g_cm3": value}

            elif task in ("rdf", "coordination_number"):
                if not request.file_path:
                    raise ValueError(f"{task} 任务缺少 file_path")
                data = tool_function(file_path=request.file_path)

            else:
                # 已注册不代表 Dispatcher 已知道如何传递该工具的参数。
                raise NotImplementedError(
                    f"任务 '{task}' 已注册，但尚未实现参数调度"
                )

        except (ValueError, FileNotFoundError, NotImplementedError) as exc:
            results[task] = {
                "tool_name": task,
                "success": False,
                "data": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
        else:
            results[task] = {
                "tool_name": task,
                "success": True,
                "data": data,
                "error": None,
            }

    # 全部任务处理完再返回；TypeError 等未预期错误仍向外传播。
    return results
