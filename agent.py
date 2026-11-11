import os
import json
import  operator
from typing import Literal
from typing_extensions import TypedDict, Annotated
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from tools import group_and_agg, filter_and_agg, get_summary
from database import init_db, save_task

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_URL"),
)
MODEL = os.environ.get("OPENAI_MODEL", "gpt-6.1-sol")
tool_map = {
    "group_and_agg": group_and_agg,
    "filter_and_agg": filter_and_agg,
    "get_summary": get_summary,
}

tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "group_and_agg",
            "description": "分组聚合，按某列分组再按某列使用对应聚合函数聚合",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_col": {"type": "string", "description": "按哪列分组"},
                    "value_col": {"type": "string", "description": "按哪列聚合"},
                    "agg_func": {"type": "string", "description": "聚合函数名称"},
                    "top_n": {"type": "integer", "description": "取前多少项"}
                },
                "required": ["group_col", "value_col", "agg_func"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filter_and_agg",
            "description": "按某要素筛选后聚合",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_col": {"type": "string", "description": "筛选哪列"},
                    "filter_val": {"type": "string", "description": "筛选值"},
                    "value_col": {"type": "string", "description": "对哪列统计"},
                    "agg_func": {"type": "string", "description": "聚合函数名称"},
                },
                "required": ["filter_col", "filter_val", "value_col", "agg_func"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary",
            "description": "总览表格，对总行数、各字段的基本统计",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    evidence: Annotated[list, operator.add]
    step: int
    retry: int

def llm_call(state: AgentState):
    response = client.chat.completions.create(
        model=MODEL,
        messages=state["messages"],
        tools=tool_definitions,
    )
    message = response.choices[0].message

    return {
        "messages": [
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ] if message.tool_calls else None,
            },
        ],
        "step": state["step"] + 1
    }

def tool_node(state: AgentState):
    last = state["messages"][-1]
    results = []
    has_error = False
    evidence_list = []
    for tool_call in last["tool_calls"]:
        args = json.loads(tool_call["function"]["arguments"])
        outputs = tool_map[tool_call["function"]["name"]](**args)
        if "error" in outputs:
            has_error = True
        results.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": str(outputs),
        })
        evidence_list.append({
            "tool_name": tool_call["function"]["name"],
            "parameters": args,
            "results": outputs,
        })
    return {
        "messages": results,
        "retry": state["retry"] + 1 if has_error else state["retry"],
        "evidence": evidence_list
    }

def should_continue(state: AgentState) -> Literal["tool_node", "__end__"]:
    if state["step"] >= 6:
        return "__end__"
    if state["retry"] >= 2:
        return "__end__"
    last = state["messages"][-1]
    if last.get("tool_calls"):
        return "tool_node"
    return "__end__"

builder = StateGraph(AgentState)
builder.add_node("llm_call", llm_call)
builder.add_node("tool_node", tool_node)

builder.add_edge(START, "llm_call")
builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
builder.add_edge("tool_node", "llm_call")

agent = builder.compile()

SYSTEM_PROMPT = (
    "你是一个数据分析助手。数据集共 5000 行，列名如下（调用工具时必须使用这些英文列名，不能用中文）：\n"
    "order_id, order_date, customer_id, product_category, region, "
    "quantity, unit_price, discount, payment_method, delivery_days, "
    "customer_rating, revenue"
)

def generate_report(question: str, answer: str, evidence: list) -> str:
    evidence_text = json.dumps(evidence, ensure_ascii=False, indent=2)
    prompt = (
        f"用户问题：{question}\n\n"
        f"Agent 最终回答：{answer}\n\n"
        f"工具调用记录：\n{evidence_text}\n\n"
        "请严格按以下格式生成分析报告，不要增减章节：\n\n"
        "## 分析报告\n"
        "**问题：** <用户原始问题>\n\n"
        "**结论：** <一句话核心结论>\n\n"
        "**数据依据：**\n"
        "- 工具：<tool_name>，参数：<parameters>，关键结果：<数字>\n"
        "（每次工具调用一条）"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

def chat(history: list, user_input: str) -> tuple[str, list, str]:
    history.append({"role": "user", "content": user_input})
    result = agent.invoke({
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
        "step": 0,
        "retry": 0,
        "evidence": []
    })
    reply = result["messages"][-1]["content"]
    history.append({"role": "assistant", "content": reply})
    report = generate_report(user_input, reply, result["evidence"])

    save_task(user_input, reply, report, result["evidence"])
    return reply, history, report

if __name__ == "__main__":
    init_db()
    history = []
    while True:
        user_input = input("你的问题：")
        if user_input == "退出":
            break
        reply, history, report = chat(history, user_input)
        print(f"助手：{reply}\n")
        print(f"--- 分析报告 ---\n{report}\n")