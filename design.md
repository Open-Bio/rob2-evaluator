# ROB2评估系统说明书

## 1. 项目概述

ROB2评估系统是一个基于Python的随机对照试验(RCT)文献质量评估工具。该系统采用ROB2框架标准，通过AI智能代理对医学研究文献进行自动化偏差风险评估，生成专业的评估报告。

### 1.1 核心功能

- 分析随机对照试验(RCT)的PDF文献
- 评估研究中的偏差风险
- 生成多格式评估报告
- 支持中英文文献处理

### 1.2 技术特点

- 模块化设计架构
- 多AI模型支持(Anthropic、OpenAI、DeepSeek等)
- 智能缓存机制
- 实时进度跟踪
- 多格式报告输出

## 2. 系统架构设计

### 2.1 整体架构层次

```
ROB2Executor (主执行器)
├── PDFDocumentProcessor (文档处理器)
├── ROB2ContentProcessor (内容处理器)
└── EvaluationService (评估服务)
    ├── EntryAgent (入口代理)
    ├── AnalysisTypeAgent (分析类型代理)
    ├── DomainAgents (领域代理群)
    │   ├── DomainRandomizationAgent (随机化过程)
    │   ├── DomainDeviationAgent (意向偏差)
    │   ├── DomainMissingDataAgent (缺失数据)
    │   ├── DomainMeasurementAgent (结果测量)
    │   └── DomainSelectionAgent (结果选择)
    └── Aggregator (结果汇总器)
```

### 2.2 核心执行流程 (`main.py: ROB2Executor`)

```
ROB2Executor.execute()
├── PDFDocumentProcessor.process_document() [processors/rob2_processor.py]
├── ROB2ContentProcessor.process_content() [processors/rob2_processor.py]
├── EvaluationService.evaluate() [services/evaluation_service.py]
└── ReportService.generate_report() [services/report_service.py]
```

## 3. 模块详细架构

### 3.1 Agent智能代理体系 (`agents/`)

```
DomainAgent [domain_agent.py] (基础代理类)
├── EntryAgent [entry_agent.py] (入口筛选)
├── AnalysisTypeAgent [analysis_type_agent.py] (分析类型判断)
├── DomainRandomizationAgent [domain_randomization.py] (随机化评估)
├── DomainDeviationAgent [domain_deviation.py] (意向偏差评估)
├── DomainMissingDataAgent [domain_missing_data.py] (缺失数据评估)
├── DomainMeasurementAgent [domain_measurement.py] (结果测量评估)
├── DomainSelectionAgent [domain_selection.py] (结果选择评估)
├── QualityCheckerAgent [quality_checker_agent.py] (质量审查代理)
├── SingleDomainReviewer [single_domain_reviewer.py] (单域专项审查器)
└── Aggregator [aggregator.py] (结果汇总)
```

**设计特点:**

- 每个代理负责特定的评估维度
- 采用专家系统设计思想
- 支持多维度协作评估
- 结果具有可解释性
- **双重质控机制**: 评估后进行专业审查
- **专项审查器**: 针对每个Domain的精确质控

### 3.2 工厂模式实现 (`factories/`)

```
DomainAgentFactory [domain_agent_factory.py]
└── create_agents() : 创建评估代理实例

ReporterFactory [reporter_factory.py]
└── create_reporter() : 创建报告生成器

DomainReviewerFactory [single_domain_reviewer.py]
└── create_reviewers() : 创建审查代理实例
```

**设计优势:**

- 统一的对象创建接口
- 支持动态代理配置
- 便于系统扩展
- **质量审查集成**: 自动创建对应的审查代理

### 3.3 服务层架构 (`services/`)

```
EvaluationService [evaluation_service.py]
├── evaluate() : 评估流程控制
├── _process_domain() : 单域评估处理  
└── 多线程并发处理 : ThreadPoolExecutor支持

PDFService [pdf_service.py]
└── extract_text() : PDF文本提取

ReportService [report_service.py]
└── generate_report() : 报告生成
```

### 3.4 数据结构定义 (`schema/rob2_schema.py`)

```
ROB2Schema
├── DomainKey : 评估域枚举
├── SignalJudgement : 信号判断结构
├── DomainJudgement : 域判断结构
└── DOMAIN_SCHEMAS : 评估域定义
```

**核心评估域:**

- Domain 1: 随机化过程
- Domain 2: 意向偏差(分配/依从性)
- Domain 3: 缺失数据
- Domain 4: 结果测量
- Domain 5: 结果选择

### 3.5 报告生成系统 (`reports/`)

```
BaseReporter [base.py]
├── JSONReporter [json_reporter.py]
├── HTMLReporter [html_reporter.py]
├── CSVReporter [csv_reporter.py]
└── WordReporter [word_reporter.py]
```

**支持格式:**

- HTML: 可视化报告
- JSON: 结构化数据
- CSV: 数据表格
- Word: 正式文档

### 3.6 配置管理 (`config/`)

```
ModelConfig [model_config.py]
├── get_model_name() : 获取模型名称
└── get_model_provider() : 获取模型提供者

ReportConfig [report_config.py]
└── get_report_settings() : 获取报告配置

ReviewConfig [review_config.py]
├── get_standards() : 获取审查标准
├── load_custom_standards() : 加载自定义标准
└── save_to_file() : 保存配置文件
```

### 3.7 工具支持 (`utils/`)

```
cache.py : 缓存装饰器
├── FileCache.get()
└── FileCache.set()

llm.py : LLM调用封装
└── call_llm()

progress.py : 进度显示
└── AgentProgress.update_status()

ollama.py : Ollama模型管理
├── ensure_ollama_and_model()
└── start_ollama_server()
```

### 3.8 处理器系统 (`processors/`)

```
BaseProcessor [base_processor.py]
└── process()

ROB2Processor [rob2_processor.py]
├── PDFDocumentProcessor.process_document()
└── ROB2ContentProcessor.process_content()
```

## 4. 系统工作流程

### 4.1 完整评估流程

```
ROB2Executor.execute()
1. PDFDocumentProcessor.process_document() 处理PDF
2. ROB2ContentProcessor.process_content() 提取内容
3. EvaluationService.evaluate() 评估流程
   - EntryAgent.filter_relevant() 相关性筛选
   - AnalysisTypeAgent.infer_analysis_type() 分析类型判断
   - DomainAgentFactory.create_agents() 创建评估代理
   - 并发执行DomainAgent.evaluate() (ThreadPoolExecutor)
   - DomainReviewerFactory.create_reviewers() 创建审查代理
   - 各SingleDomainReviewer.review_and_revise() 质量审查
   - Aggregator.evaluate() 汇总结果
4. ReportService.generate_report() 生成报告
```

### 4.2 评估策略

**多维度评估:**

- 每个域都有独立的评估标准
- 支持不同分析类型(assignment/adherence)
- 基于证据的风险判断

**智能筛选:**

- 入口代理过滤无关内容
- 分析类型代理判断评估路径
- 内容相关性评分

## 5. 设计原则与模式

### 5.1 设计原则

- **单一职责原则**: 每个类只负责一个功能
- **开闭原则**: 对扩展开放，对修改封闭
- **依赖倒置原则**: 依赖抽象，不依赖具体实现
- **接口隔离原则**: 使用多个专门的接口

### 5.2 应用的设计模式

- **工厂模式**: DomainAgentFactory, ReporterFactory
- **策略模式**: 不同的评估策略
- **模板方法**: 统一的处理流程框架
- **装饰器模式**: 缓存功能实现

### 5.3 架构特色

- **领域驱动设计**: 基于ROB2专业框架
- **分层架构**: 清晰的系统层次
- **模块化设计**: 高内聚低耦合
- **可扩展性**: 易于添加新功能

## 6. 质量保障

### 6.1 测试覆盖

- 单元测试: 每个模块都有对应测试
- 集成测试: 完整流程测试
- 功能测试: 各Agent功能验证

### 6.2 错误处理

- 完善的异常处理机制  
- 数据验证和清洗
- 结果一致性检查

### 6.3 性能优化

- 缓存机制避免重复处理
- 智能进度跟踪
- 资源使用优化

## 7. 技术栈

### 7.1 核心技术

- **语言**: Python 3.8+
- **AI框架**: 支持多种LLM模型
- **文档处理**: PDF解析库
- **报告生成**: 多格式输出

### 7.2 支持的AI模型

- Anthropic Claude
- OpenAI GPT系列
- DeepSeek
- Ollama本地模型

## 8. 使用特点

### 8.1 用户友好

- 简单的配置方式
- 清晰的进度显示
- 详细的评估报告
- 多种输出格式

### 8.2 专业性

- 基于ROB2标准框架
- 专业的评估维度
- 可解释的评估结果
- 支持中英文文献

## 9. 扩展性设计

### 9.1 模块扩展

- 易于添加新的评估代理
- 支持新的报告格式
- 灵活的配置机制

### 9.2 功能扩展

- 支持新的文档格式
- 集成更多AI模型
- 添加新的评估标准

## 10. v0.2.0版本新特性

### 10.1 质量审查系统

**核心改进：**
- 引入双重质控机制，每个Domain评估结果都经过专业审查
- `QualityCheckerAgent`：通用质量审查代理，支持多Domain审查
- `SingleDomainReviewer`：专项审查器，针对特定Domain的精确质控
- `ReviewConfig`：可配置的审查标准，支持自定义审查规则

**技术实现：**
- 基于ROB2框架的专业审查标准
- 自动检测评估结果中的逻辑不一致和质量问题
- 智能修正机制，自动提供高质量的修正建议
- 完整的审查过程追踪和记录

### 10.2 高性能并发处理

**性能优化：**
- 使用`ThreadPoolExecutor`实现Domain代理的并发执行
- 智能任务调度，保证结果顺序一致性
- 显著缩短大型文档的处理时间
- 支持批量文件的并行处理

**批量处理能力：**
- 支持多PDF文件同时处理
- 智能文件去重和缓存机制
- 统一的汇总报告生成
- 进度追踪和状态监控

### 10.3 增强的报告系统

**报告模板升级：**
- 新增汇总报告模板 (`report_template_summary.html.j2`)
- 支持多文件分析结果的统一展示
- 改进的可视化效果和交互体验
- 更好的风险评估数据展示

**报告格式扩展：**
- 优化的HTML报告，支持汇总视图
- 改进的JSON数据结构，便于程序化处理
- 增强的CSV格式，支持更复杂的数据分析
- 更专业的Word文档格式

### 10.4 架构改进

**模块化增强：**
- 更清晰的责任分离和接口定义
- 改进的依赖注入机制
- 更好的错误处理和异常管理
- 增强的可测试性和可维护性

**配置管理：**
- 新增`ReviewConfig`支持审查标准的配置化
- 更灵活的模型配置选项
- 支持运行时配置的动态加载
- 改进的环境变量和配置文件支持
