# 🔮 Deja Protocol

**Shared operational memory for on-chain agents.**

*Your agent already lived this — through others.*

---

## The Problem

On-chain AI agents repeat the same mistakes other agents already made. Every failed transaction costs real gas. Every timeout wastes real time. And every workaround discovered by one agent stays locked in a silo — invisible to every other agent facing the same problem.

LLMs like Claude or GPT have general knowledge about how blockchains work, but they **don't know what's happening right now** on a specific chain. They don't know that a particular RPC started timing out 2 hours ago, or that a specific contract reverts under certain conditions that aren't in any documentation.

## The Solution

Deja is a **shared knowledge layer** that lets agents learn from each other's operational experience — automatically, in real time, without exposing strategies.

```
Agent Alpha tries a swap → fails → Deja captures why
Agent Beta tries the same swap → Deja warns BEFORE executing → Beta succeeds first try
```

### What Deja captures (automatically):
- 🔴 **Transaction failures** — what went wrong and why
- ⚡ **Gas deviations** — when real gas ≠ estimated gas
- 🔄 **Retry patterns** — when agents had to retry operations
- 🌐 **RPC issues** — timeouts, throttling, stale data
- 🔮 **Simulation mismatches** — when simulation ≠ real execution
- 🏗️ **Infrastructure issues** — indexer delays, oracle problems

### What Deja does NOT capture:
- ❌ Agent strategies or business logic
- ❌ Private keys or sensitive data
- ❌ Decision-making processes

## Why not just use an LLM?

| | LLM (Claude, GPT) | Deja Protocol |
|---|---|---|
| **Knowledge type** | General, from training data | Operational, from live execution |
| **Freshness** | Months old (training cutoff) | Real-time (seconds old) |
| **Source** | Public docs, forums, code | Actual agent execution results |
| **Specificity** | "How swaps generally work" | "This contract on this chain right now" |
| **Pre-transaction data** | ❌ No access | ✅ Simulation failures, retries |
| **Cross-system issues** | ❌ No visibility | ✅ RPC, indexer, oracle problems |

Deja doesn't replace LLMs — it gives them the **operational context they're missing**.

## Architecture

```
┌─────────────────────────────────────────────┐
│              DEJA PROTOCOL                   │
│                                              │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐ │
│  │  SDK    │──▶│  API     │──▶│ Knowledge│ │
│  │(wrapper)│◀──│ (FastAPI)│◀──│   DB     │ │
│  └─────────┘   └──────────┘   └──────────┘ │
│       │                                      │
│  Wraps agent        Receives &               │
│  operations         serves knowledge         │
└─────────────────────────────────────────────┘
        │
   ┌────┴────┐
   │  Agent  │  ← Developer integrates SDK (3 lines)
   └─────────┘
```

### Components:
1. **SDK** — Lightweight wrapper. Agent developers integrate it in 3 lines. Automatically reports observations and consults knowledge before executing.
2. **API** — Central service that receives observations and serves knowledge queries.
3. **Knowledge DB** — Structured storage of operational observations with relevance scoring.

## Quick Start

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/deja-protocol.git
cd deja-protocol
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic
```

### Run the Demo

```bash
python3 demo.py
```

This runs a simulation showing Agent Alpha failing and Agent Beta learning from Alpha's experience.

### Start the API

```bash
python3 main.py
# API docs available at http://localhost:8000/docs
```

### Integrate with your Agent (3 lines)

```python
from sdk import DejaSDK

deja = DejaSDK(agent_id="my-agent", chain="taiko")
result = deja.execute(
    operation_fn=your_swap_function,
    operation_description="Swap 100 USDC to ETH",
    contract_address="0x..."
)
```

That's it. The SDK automatically:
1. **Consults** Deja before executing → "Has anyone tried this?"
2. **Executes** your original operation
3. **Reports** the result → so others can learn

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/report` | Agent reports an observation |
| `POST` | `/query` | Agent queries knowledge before executing |
| `POST` | `/confirm/{id}` | Agent confirms an observation is accurate |
| `GET` | `/stats` | Network statistics |
| `GET` | `/docs` | Interactive API documentation |

## Roadmap

- [x] **v0.1** — Core SDK + API + Demo (current)
- [ ] **v1.0** — Multi-chain support, reputation system, developer dashboard
- [ ] **v2.0** — Tiered access (free basic / premium detailed), observation quality scoring
- [ ] **v3.0** — MCP integration for agent tool discovery, tokenized knowledge contributions

## The Vision

Every agent that connects makes the network smarter.
Every error shared is an error others won't repeat.

**This is Deja Protocol.**

---

*Built for the Taiko Hackathon 2026*
