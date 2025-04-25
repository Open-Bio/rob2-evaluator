<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Instructions for Copilot

这是一个模块化的Python项目，用于评估随机对照试验（ROB2框架）中偏差的风险。该项目包括多个专家代理，每个专家负责特定领域，以及一个汇总结果来总结结果。

## 一、核心数据结构 (Core Data Structure - schema/rob2_schema.py)

- **文件 (File):** `rob2_evaluator/schema/rob2_schema.py`
- **主要类/结构 (Key Classes/Structures):**
  - `Domain`
  - `Judgement`
  - `Signal`
  - `ROB2Assessment`
    *(示例，具体以源码为准 / Examples, refer to source code for specifics)*
- **作用 (Purpose):**
  - 定义 ROB2 (Risk of Bias 2) 评估所需的所有核心数据结构。
  - 确保所有代理（Agents）的输入和输出严格遵循这些预定义的结构，保证整个系统数据流的一致性和规范性。

## 二、主要代理体系 (Main Agent System - rob2_evaluator/agents/)

### 1. 入口代理 (EntryAgent)

- **文件 (File):** `rob2_evaluator/agents/entry_agent.py`
- **主要类 (Main Class):** `EntryAgent`
- **作用 (Purpose):**
  - 接收原始输入数据（例如：临床试验描述文本、研究文献内容等）。
  - 执行初步的数据预处理和格式校验。
  - 根据内容将任务分发给相应的领域代理（Domain Agents）。
- **关键方法 (Key Methods):** `process_input`, `dispatch_to_domains` *(如有 / if any)*

### 2. 各领域代理 (Domain Agents)

- **文件模式 (File Pattern):** `rob2_evaluator/agents/domain_*.py`
- **主要类/函数 (Example Classes/Functions):**
  - `DomainRandomizationAgent` (`domain_randomization.py`) - 随机化过程域
  - `DomainMissingDataAgent` (`domain_missing_data.py`) - 缺失结果数据域
  - `DomainDeviationAgent` (`domain_deviation.py`) - 干预偏离域
  - `DomainMeasurementAgent` (`domain_measurement.py`) - 结果测量域
  - `DomainSelectionAgent` (`domain_selection.py`) - 结果选择性报告域
- **作用 (Purpose):**
  - 每个 Domain Agent 专注于 ROB2 评估框架中的一个特定领域（Domain）。
  - 负责对其负责的领域进行深入分析、风险偏倚判断（Judgement）和信号词提取（Signal）。
  - 输出符合 `rob2_schema.py` 定义的结构化评估结果（例如 `DomainJudgement` 实例）。
- **关键方法 (Key Methods):** `evaluate`, `analyze`, `get_judgement` *(如有 / if any)*

### 3. 分析类型代理 (AnalysisTypeAgent)

- **文件 (File):** `rob2_evaluator/agents/analysis_type_agent.py`
- **主要类 (Main Class):** `AnalysisTypeAgent`
- **作用 (Purpose):**
  - 识别和处理研究中使用的主要分析类型（例如：意向性分析 (Intention-to-Treat), 符合方案分析 (Per-Protocol), 亚组分析 (Subgroup Analysis) 等）。
  - 为各领域代理（Domain Agents）的评估提供必要的上下文信息（例如，不同的分析类型可能影响某些领域的偏倚风险判断）。
- **关键方法 (Key Methods):** `detect_analysis_type`

### 4. 聚合代理 (Aggregator)

- **文件 (File):** `rob2_evaluator/agents/aggregator.py`
- **主要类 (Main Class):** `Aggregator`
- **作用 (Purpose):**
  - 收集并汇总来自所有领域代理（Domain Agents）的评估结果。
  - 根据各领域的判断，生成对整个研究的总体 ROB2 偏倚风险评估结论。
  - 可能负责将最终的评估结果格式化并输出为报告。
- **关键方法 (Key Methods):** `aggregate_results`, `generate_report`

## 三、辅助模块 (Auxiliary Modules)

- **`llm/models.py`:**
  - 定义与大语言模型（LLM）交互的接口和数据结构。
  - 封装 LLM 调用逻辑，支持利用 AI 进行智能分析和判断。
- **`utils/`:**
  - **`json_io.py`:** 提供 JSON 数据的读取和写入功能。
  - **`llm.py` / `ollama.py`:** 可能包含更底层的 LLM API 调用或特定模型（如 Ollama）的辅助函数。
  - **`progress.py`:** 提供命令行进度条显示等用户界面相关的工具。
  - *(其他通用工具函数)*

## 四、主流程 (Main Flow - main.py)

- **文件 (File):** `rob2_evaluator/main.py`
- **主要函数 (Main Functions):** `main`, `run_evaluation` *(如有 / if any)*
- **作用 (Purpose):**
  - 作为整个项目的执行入口点。
  - 编排和组织各个代理（Agents）的调用顺序和协作流程。
- **典型执行步骤 (Typical Execution Steps):**
    1. **加载输入数据 (Load Input Data):** 读取需要评估的试验描述或文献。
    2. **调用 `EntryAgent`:** 进行输入预处理和任务分发。
    3. **并行/串行调用各 `Domain Agents`:** 各代理独立或按需处理其负责的评估领域。
    4. **(可选) 调用 `AnalysisTypeAgent`:** 获取分析类型信息供 Domain Agents 使用。
    5. **调用 `Aggregator`:** 汇总所有 Domain 的评估结果，生成最终结论。
    6. **输出结果 (Output Results):** 输出结构化的 ROB2 评估报告或数据。

## 五、数据流与交互 (Data Flow & Interaction)

1. **输入 (Input):** 原始试验描述 / 文献内容 (Raw Trial Description / Literature Content)
2. **`EntryAgent`:** 预处理、校验、分发 (Preprocesses, Validates, Dispatches)
3. **`Domain Agents`:** 接收分发的数据，结合可能的 `AnalysisTypeAgent` 信息，进行各自领域的分析，输出结构化的领域评估结果 (Analyze respective domains, output structured domain assessments, potentially using info from `AnalysisTypeAgent`)
4. **`Aggregator`:** 收集所有 `Domain Agents` 的输出 (Collects outputs from all `Domain Agents`)
5. **输出 (Output):** 遵循 `rob2_schema.py` 结构的最终 ROB2 评估报告/数据 (Final ROB2 assessment report/data adhering to `rob2_schema.py`)

**核心原则 (Core Principle):** 所有组件间的数据交换严格遵循 `rob2_schema.py` 中定义的结构，确保系统内部通信的准确性和一致性。
