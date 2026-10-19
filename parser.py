from openai import OpenAI
from dotenv import load_dotenv
from schemas import AnalysisRequest

import json
import os


load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def parse_user_query(user_query: str) -> AnalysisRequest:
    system_prompt = """
你是材料分析请求解析器。

你的任务是把用户的自然语言请求转换成 JSON。

输出字段必须为：

{
    "file_path": string | null,
    "tasks": list[string],
    "temperature": number | null,
    "num_structures": integer | null,
    "num_atoms": integer | null,
    "volume_angstrom3": number | null
}

支持的任务名称包括：
- rdf
- coordination_number
- adf
- quality_check
- density

规则：
1. 只提取用户明确提供的信息。
2. 缺失字段使用 null。
3. temperature 只保留数值，例如 300 K -> 300。
4. volume_angstrom3 只保留数值，例如 2000 Å³ -> 2000。
5. 不要输出解释文字，只输出 JSON。
6. 如果用户要求了不支持的任务，不要擅自替换成其他任务，保留其任务名称，让后续程序验证。
"""
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_query
            }
        ],
        response_format={
            "type": "json_object"
        }
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    request = AnalysisRequest(**data)

    return request