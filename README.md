# ROB2 Evaluator

基于多专家混合代理的RCT研究偏倚风险评估工具 (ROB2)。

## 架构设计

### 简单

```mermaid
graph TD
    A[输入文档] --> B[入口专家]
    B --> C[相关内容筛选]
    C --> D[分析类型专家]
    C --> E[Domain专家]
  
    subgraph "Domain专家评估"
        E --> F1[随机化专家]
        E --> F2[实施偏倚专家]
        E --> F3[缺失数据专家]
        E --> F4[测量专家]
        E --> F5[选择性报告专家]
    end
  
    F1 --> G[汇总专家]
    F2 --> G
    F3 --> G
    F4 --> G
    F5 --> G
    D --> G
  
    G --> H[评估结果]
```

### 系统架构详图

```mermaid
graph TD
    %% 主要执行流程
    A[PDF文档] --> B[PDFDocumentProcessor]
    B --> C[ROB2ContentProcessor]
    C --> D[EvaluationService]
    D --> E[ReportService]
    E --> F[评估报告]

    %% 文档处理和服务
    subgraph "文档处理系统"
        B --> PDFService[PDF服务]
        PDFService --> text[文本提取]
    end

    %% 评估服务详细流程
    subgraph "评估服务系统"
        D --> Entry[入口代理]
        D --> Analysis[分析类型代理]
      
        Entry --> Content[相关内容]
        Content --> DomainAgents[领域代理群]
      
        subgraph "专家评估系统"
            DomainAgents --> Random[随机化专家]
            DomainAgents --> Deviation[实施偏倚专家]
            DomainAgents --> Missing[缺失数据专家]
            DomainAgents --> Measure[测量专家]
            DomainAgents --> Selection[选择性报告专家]
        end
      
        Random & Deviation & Missing & Measure & Selection --> Agg[结果汇总器]
    end

    %% 报告生成系统
    subgraph "报告生成系统"
        E --> JSON[JSON报告]
        E --> HTML[HTML报告]
        E --> CSV[CSV报告]
        E --> Word[Word报告]
    end

    %% 配置管理系统
    subgraph "配置管理"
        Config[配置系统]
        Config --> ModelConfig[模型配置]
        Config --> ReportConfig[报告配置]
    end

    %% 工具支持系统
    subgraph "工具支持"
        Utils[工具系统]
        Utils --> Cache[缓存机制]
        Utils --> LLM[LLM调用]
        Utils --> Progress[进度显示]
        Utils --> OllamaManager[Ollama管理]
    end

    %% AI模型支持
    subgraph "AI模型支持"
        Models[模型系统]
        Models --> Claude[Anthropic]
        Models --> GPT[OpenAI]
        Models --> DeepSeek[DeepSeek]
        Models --> Ollama[本地模型]
    end

    %% 关联关系
    Config -.-> D
    Utils -.-> D
    Models -.-> D
    Cache -.-> B
    Cache -.-> C
```

### 模块说明

1. **文档处理系统**

   - PDFDocumentProcessor：PDF文档处理
   - ROB2ContentProcessor：内容提取与处理
   - PDFService：文本提取服务
2. **评估服务系统**

   - 入口代理：文献相关性筛选
   - 分析类型代理：评估路径判断
   - 专家评估系统：五大领域评估
   - 结果汇总器：综合分析
3. **报告生成系统**

   - 支持多种格式输出
   - 可视化报告生成
   - 结构化数据输出
4. **配置管理**

   - 模型配置：AI模型参数设置
   - 报告配置：输出格式定制
5. **工具支持**

   - 缓存机制：优化性能
   - LLM调用：模型接口封装
   - 进度显示：实时状态追踪
   - Ollama管理：本地模型部署
6. **AI模型支持**

   - 支持多种主流模型
   - 本地部署能力
   - 灵活的模型选择

````

````
