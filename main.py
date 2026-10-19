import json
import os
from pprint import pprint
from typing import Callable

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from schemas import AnalysisRequest
from tools.dispatcher import dispatch_request


REPORT_SYSTEM_PROMPT = (
    "你是材料结构分析助手。"
    "请严格根据提供的 Tool Results 回答用户问题。"
    "只使用 success=true 项的 data 作为计算结果。"
    "对于 success=false 的任务，请说明失败原因，不得补写其计算结果。"
    "部分任务失败时，分别说明已完成的分析和未完成的分析。"
    "density_g_cm3 的单位为 g/cm³。"
    "不要编造 Tool Results 中不存在的定量信息。"
)


def main(
    *,
    client=None,
    parse_query: Callable[[str], AnalysisRequest] | None = None,
) -> None:
    """CLI 入口；测试可注入假解析器和假报告客户端，无需真实 API。"""
    if client is None:
        load_dotenv()
        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )

    if parse_query is None:
        # 导入 main 不初始化 parser 中的客户端，便于独立测试 CLI。
        from parser import parse_user_query

        parse_query = parse_user_query

    system_messages = [{"role": "system", "content": "你是材料结构分析助手"}]
    messages = system_messages.copy()

    print(
        "mgn_agent 已启动，输入 /history 查看对话历史，"
        "输入 /clear 清空对话历史，输入 /exit 退出。"
    )

    while True:
        user_input = input("\nUser: ").strip()

        if user_input.lower() == "/exit":
            break
        if user_input == "/history":
            pprint(messages)
            continue
        if user_input == "/clear":
            messages = system_messages.copy()
            print("对话历史已清空。")
            continue

        # 1. 自然语言 -> AnalysisRequest
        try:
            parsed_request = parse_query(user_input)
        except ValidationError as exc:
            print("\n请求解析失败:")
            print(exc)
            continue

        print("\n解析后的 AnalysisRequest:")
        print(parsed_request.model_dump())

        # 2. 执行工具；预期的单工具失败已经由 Dispatcher 转成结果。
        tool_results = dispatch_request(parsed_request)
        print("\nTool Results:")
        pprint(tool_results)

        success_count = sum(item["success"] for item in tool_results.values())
        failure_count = len(tool_results) - success_count

        # 3. 无成功计算结果时，本地说明原因，不进入报告 API。
        if success_count == 0:
            if not tool_results:
                print("未执行任何工具，请至少指定一个任务。")
            else:
                print("全部工具执行失败，本次不调用报告 API。")
                for task, item in tool_results.items():
                    print(f"- {task}: {item['error']}")
            continue

        if failure_count:
            print(f"部分成功：{success_count} 个成功，{failure_count} 个失败。")
        else:
            print(f"全部成功：{success_count} 个工具已完成。")

        # 4. 有成功结果时，将完整状态交给 LLM，明确区分成功与失败。
        report_response = client.chat.completions.create(
            model="deepseek-flash",
            messages=[
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"用户原始请求：{user_input}\n"
                        "Tool Results："
                        + json.dumps(tool_results, ensure_ascii=False)
                    ),
                },
            ],
            extra_body={"thinking": {"type": "disabled"}},
        )
        final_message = report_response.choices[0].message.content

        messages.append({"role": "user", "content": user_input})
        messages.append({"role": "assistant", "content": final_message})
        print("\n最终回答:")
        print(final_message)


if __name__ == "__main__":
    main()
