# data-agent：电商数据分析 Agent

用自然语言查询电商销售数据，Agent 自动调用数据工具、生成带溯源依据的分析报告，结果持久化存储并通过 REST API 对外提供。

## 目录结构

```
data_agent/
├── agent.py        # LangGraph Agent：状态定义、节点、图编排
├── tools.py        # 数据工具层：group_and_agg、filter_and_agg、get_summary、compare_groups、detect_anomaly
├── database.py     # SQLite 持久化：建表、写入、查询
├── main.py         # FastAPI 服务：/ask 和 /tasks 接口
├── data/
│   ├── E-Commerce Sales Analytics.csv   # 数据集
│   └── eval_cases.json                  # 评测题目与标准答案
└── scripts/
    └── eval.py     # 评测脚本：批量跑接口，比对关键词
```

## 核心设计

**受控工具执行**：模型只能调用白名单工具（`group_and_agg`、`filter_and_agg`、`get_summary`、`compare_groups`、`detect_anomaly`），参数经 tool_definitions 约束，不生成或执行任意代码。

**Evidence 溯源**：每次工具调用记录工具名、参数、返回值，报告中的数字均可追溯到具体的工具调用。

**自动重试**：工具返回 error 时，模型携带错误信息重新调用，最多重试 2 次；LLM 调用步数上限为 6 步，防止死循环。

**多轮对话**：`chat()` 函数维护对话历史，追问时模型能记住上下文。

## 当前不足

- 评测规模小，仅 10 道题，覆盖场景有限
- 报告生成依赖模型描述数量，偶有计数偏差
- 无身份验证，接口完全开放

## 环境准备

Python 3.10+

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

pip install pandas langgraph langchain langchain-openai openai fastapi uvicorn
```

配置环境变量：

```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=your_base_url
OPENAI_MODEL=your_model       # 可选，默认 gpt-4o
```

## 启动与使用

**启动 API 服务：**

```bash
uvicorn main:app --port 8001
```

**提问（POST /ask）：**

```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "各品类的总收入分别是多少？"}'
```

返回：

```json
{
  "reply": "各品类总收入如下...",
  "report": "## 分析报告\n**问题：** ..."
}
```

**查询历史（GET /tasks）：**

```bash
curl http://localhost:8001/tasks
```

**交互模式：**

```bash
python agent.py
```

**运行评测（需先启动服务）：**

```bash
python scripts/eval.py
```

## 数据集

[E-Commerce Sales Analytics](https://www.kaggle.com/) — 5000 行 × 12 列，CC BY-SA 4.0。  
字段：`order_id`、`order_date`、`customer_id`、`product_category`、`region`、`quantity`、`unit_price`、`discount`、`payment_method`、`delivery_days`、`customer_rating`、`revenue`。
