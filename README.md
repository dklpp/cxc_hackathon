# cxc_hackathon

Banking system for customer data and debt tracking.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install dependencies

```bash
uv sync --no-install-project
```

**Note:** This project is a script-based application (not a Python package), so we use `--no-install-project` to skip building/installing the project itself.

This will:
- Create a virtual environment in `.venv/`
- Install all dependencies from `pyproject.toml`
- Generate `uv.lock` for reproducible builds

### Activate the virtual environment

```bash
source .venv/bin/activate
```

Or use `uv run` to run commands directly without activation:

```bash
uv run python DB/db_usage_example.py
```

### Add new dependencies

```bash
uv add package-name
```

### Update dependencies

```bash
uv sync --no-install-project --upgrade
```

## Database Setup

Initialize the database and load sample customers:

```bash
uv run python DB/db_usage_example.py
```

This will create the database tables and load 10 sample customers from `DB/customers/`.
# Automated Client Engagement Platform for Financial Services

## Executive Summary

An AI-powered platform that transforms traditional cold calling into data-driven, personalized client engagement for financial institutions. The system automatically analyzes client data to create behavioral profiles, optimal contact strategies, and personalized conversation approaches, then executes outreach through AI-powered voice calls.

## Problem Statement

Financial institutions, particularly banks, face significant challenges with traditional outreach methods:

- **Low Success Rates**: Cold calls achieve only 10–15% effectiveness
- **Time-Intensive Research**: Manual client research for personalized approaches requires substantial resources
- **Missed Opportunities**: Without data-driven insights, call centers contact clients at suboptimal times
- **Scalability Constraints**: Human agents cannot efficiently analyze and act on large volumes of client data

## Solution Overview

A four-stage automated platform that:

1. **Ingests client data** from existing databases (focusing on clients requiring engagement, such as those with outstanding obligations)
2. **Generates intelligent profiles** using AI agents to analyze behavioral patterns, financial situations, and engagement history
3. **Executes personalized outreach** via ElevenLabs AI voice technology with Gemini-powered conversational capabilities
4. **Provides actionable insights** through a comprehensive dashboard tracking all interactions and outcomes

## Core Use Cases

- **Automated Data Collection**: Seamlessly integrates with existing client databases
- **Behavioral Profiling**: Creates comprehensive client profiles including financial patterns, communication preferences, and engagement history
- **Optimal Timing Intelligence**: Identifies the best contact windows (e.g., Friday evenings post-payday, following direct deposits)
- **Strategy Personalization**: Generates 3 top-ranked conversation strategies tailored to each client's profile
- **AI-Powered Conversations**: Deploys natural, empathetic voice interactions through ElevenLabs and Gemini integration

## Key Innovation

The platform achieved a **30% improvement in model efficiency** by implementing a distributed AI architecture—deploying smaller, specialized models for dedicated tasks rather than relying on a single large model for all operations.

## Expected Outcomes

- Increase engagement success rates beyond the industry standard 10–15%
- Reduce research and preparation time per client interaction
- Scale personalized outreach without proportional increases in human resources
- Improve customer satisfaction through relevant, well-timed communications
- Provide call center teams with actionable intelligence and ready-to-execute strategies

## Setup

1. Copy `.env.example` to `.env` and configure your API keys
2. Install dependencies: `pip install flask websockets openai twilio python-dotenv`
