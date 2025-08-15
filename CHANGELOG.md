# 更新日志 (Changelog)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-08-15

### 新增功能 (Added)

#### 质量审查系统
- **双重质控机制**: 为每个Domain评估结果提供专业的二次审查
- **QualityCheckerAgent**: 新增通用质量审查代理，支持多Domain标准化审查
- **SingleDomainReviewer**: 新增专项审查器，针对特定Domain提供精确质控
- **DomainReviewerFactory**: 新增审查器工厂，自动创建对应的审查代理
- **ReviewConfig**: 新增可配置的审查标准管理，支持自定义审查规则
- **智能修正**: 自动检测评估结果中的逻辑不一致并提供修正建议
- **审查追踪**: 完整记录审查过程、修正原因和置信度评分

#### 高性能并发处理
- **多线程评估**: 使用ThreadPoolExecutor实现Domain代理的并发执行
- **批量处理**: 支持多个PDF文件的同时处理和批量评估
- **智能调度**: 保证并发处理结果的顺序一致性
- **进度监控**: 实时显示批量处理的进度和状态

#### 增强的报告系统
- **汇总报告模板**: 新增`report_template_summary.html.j2`支持多文件分析汇总
- **统一展示**: 支持多文件分析结果的统一可视化展示
- **改进的可视化**: 更好的风险评估数据展示和交互体验

### 改进优化 (Changed)

#### 架构优化
- **EvaluationService**: 重构评估服务，集成并发处理和质量审查功能
- **ROB2Executor**: 优化执行器，支持多文件处理和缓存优化
- **依赖注入**: 改进的依赖注入机制，提升模块间的解耦
- **错误处理**: 增强的异常处理和错误恢复机制

#### 性能提升
- **缓存机制**: 基于内容哈希的智能缓存，避免重复处理
- **内存优化**: 优化大文件处理的内存使用
- **处理速度**: 多线程并发显著提升处理速度

#### 配置管理
- **灵活配置**: 支持运行时配置的动态加载
- **环境变量**: 改进的环境变量和配置文件支持
- **标准化**: 更好的配置结构和管理方式

### 技术改进 (Technical)

#### 代码质量
- **模块化**: 更清晰的责任分离和接口定义
- **可测试性**: 增强的单元测试支持和覆盖率
- **可维护性**: 改进的代码结构和文档

#### 数据结构
- **审查信息**: 在评估结果中新增review_info字段，记录审查过程
- **批量结果**: 支持多文件结果的统一数据结构
- **元数据**: 增强的文件处理元数据和追踪信息

### 向后兼容性 (Compatibility)

- ✅ **API兼容**: 保持原有API接口的向后兼容
- ✅ **配置兼容**: 现有配置文件无需修改即可使用
- ✅ **数据兼容**: 原有评估结果格式保持兼容
- ✅ **别名支持**: `QualityCheckerAgent`作为`DomainReviewerAgent`的别名保持兼容

### 依赖更新 (Dependencies)

- 无破坏性依赖变更
- 所有现有依赖保持稳定版本

### 文档更新 (Documentation)

- **README.md**: 新增功能亮点和使用说明
- **design.md**: 更新架构设计，包含新组件说明
- **CLAUDE.md**: 更新项目指导说明
- **CHANGELOG.md**: 新增版本更新记录

### 迁移指南 (Migration Guide)

从v0.1.0升级到v0.2.0无需任何代码修改，所有现有功能保持完全兼容。

#### 推荐升级步骤:
1. 更新依赖: `poetry install` 或 `pip install -e .`
2. 验证功能: 运行现有评估任务确认正常工作
3. 体验新功能: 尝试批量处理和质量审查功能

#### 新功能使用:
- **质量审查**: 评估结果自动包含review_info字段
- **批量处理**: 直接传入多个PDF文件路径
- **并发处理**: 自动启用，无需额外配置

---

## [0.1.0] - 2025-08-01

### 初始版本 (Initial Release)

#### 核心功能
- ROB2框架的完整实现
- 五大Domain的专业评估
- 多AI模型支持
- 多格式报告生成
- 智能代理系统
- 缓存机制
- 进度追踪

#### 支持的功能
- PDF文档处理
- 内容提取和过滤
- 专家代理评估
- 结果汇总
- 报告生成（HTML、JSON、CSV、Word）
- 配置管理
- 测试覆盖

#### 支持的AI模型
- Anthropic Claude
- OpenAI GPT
- DeepSeek
- Google Gemini
- Groq
- Ollama本地模型