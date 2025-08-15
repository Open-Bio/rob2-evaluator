# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROB2 Evaluator is a multi-agent AI system for Risk of Bias (ROB2) assessment of randomized controlled trials (RCTs). The system processes PDF research papers and generates comprehensive bias risk evaluation reports using multiple specialized AI agents.

## Development Commands

### Environment Setup

```bash
# Install dependencies using Poetry
poetry install

# Install development dependencies
poetry install --group dev
```

### Running the Application

```bash
# Main entry point (using Poetry)
poetry run rob2-eval

# Direct Python execution 
python rob2_evaluator/main.py
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/unit/test_domain_agent.py

# Run tests with verbose output
poetry run pytest -v
```

### Code Quality

```bash
# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .

# Lint with flake8
poetry run flake8
```

## Architecture Overview

### Core Execution Flow

```
ROB2Executor → PDFDocumentProcessor → ROB2ContentProcessor → EvaluationService → ReportService
```

### Agent System

The system uses a multi-agent architecture with specialized evaluators:

1. **EntryAgent** (`agents/entry_agent.py`) - Filters relevant content from documents
2. **AnalysisTypeAgent** (`agents/analysis_type_agent.py`) - Determines evaluation pathway (assignment/adherence)
3. **Domain Agents** - Five specialized agents for ROB2 domains:
   - `DomainRandomizationAgent` (Domain 1: Randomization process)
   - `DomainDeviationAgent` (Domain 2: Deviations from intended interventions)
   - `DomainMissingDataAgent` (Domain 3: Missing outcome data)
   - `DomainMeasurementAgent` (Domain 4: Measurement of the outcome)
   - `DomainSelectionAgent` (Domain 5: Selection of the reported result)
4. **Aggregator** (`agents/aggregator.py`) - Synthesizes results from all domain agents

### Key Design Patterns

- **Factory Pattern**: `DomainAgentFactory` creates agents based on analysis type
- **Strategy Pattern**: Different evaluation strategies for assignment vs adherence analysis
- **Template Method**: Unified processing pipeline across all agents
- **Decorator Pattern**: Caching functionality via `@cache_result()`

### Data Flow

1. PDF processing extracts text content with page indexing
2. Content filtering identifies ROB2-relevant sections
3. Concurrent domain evaluation using ThreadPoolExecutor
4. Result aggregation and risk assessment synthesis
5. Multi-format report generation (HTML, JSON, CSV, Word)

## Important Modules

### Core Services (`services/`)

- `evaluation_service.py` - Orchestrates the evaluation pipeline with multithreading
- `pdf_service.py` - Handles PDF text extraction
- `report_service.py` - Manages report generation across formats

### Configuration (`config/`)

- `model_config.py` - AI model selection and provider configuration
- `report_config.py` - Output format and template settings

### Schema (`schema/rob2_schema.py`)

- Pydantic models for ROB2 evaluation structure
- `GenericDomainJudgement`, `SignalJudgement`, `DomainJudgement`
- Evidence tracking with page references

### Utilities (`utils/`)

- `cache.py` - File-based caching with `@cache_result()` decorator
- `llm.py` - LLM interface abstraction for multiple providers
- `ollama.py` - Local model management
- `progress.py` - Real-time evaluation progress tracking

## AI Model Support

The system supports multiple LLM providers:

- **Anthropic Claude** (via langchain-anthropic)
- **OpenAI GPT** (via langchain-openai)
- **DeepSeek** (via langchain-deepseek)
- **Groq** (via langchain-groq)
- **Google Gemini** (via langchain-google-genai)
- **Local models** (via Ollama)

Model configuration is centralized in `config/model_config.py`.

## Testing Strategy

- **Unit tests** for each agent in `tests/unit/`
- **Fixtures** with sample content in `tests/fixtures/`
- **Integration testing** via main execution pipeline
- Test coverage includes signal evaluation, evidence extraction, and result aggregation

## Performance Features

- **Concurrent evaluation**: Domain agents run in parallel using ThreadPoolExecutor
- **Intelligent caching**: Results cached by content hash to avoid reprocessing
- **Progress tracking**: Real-time status updates during evaluation
- **Memory optimization**: Lazy loading of processors and agents

## File Structure Notes

- `main.py` contains `ROB2Executor` (main orchestrator) and `ROB2Reporter` (report generation)
- Agent implementations inherit from base `DomainAgent` class
- Report templates use Jinja2 in `templates/`
- Data samples in `data/english/` and `data/中文文献/` for testing
