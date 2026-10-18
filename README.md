# IHB-01 · Finance Categorizer

Categorizes bank transactions with a fast ML classifier and an LLM fallback for low-confidence cases.

![Status](https://img.shields.io/badge/status-in%20progress-24466B)
![Python](https://img.shields.io/badge/python-3.13-24466B)
![License](https://img.shields.io/badge/license-MIT-24466B)

| Headline metric | Dataset | Model | Status |
| --- | --- | --- | --- |
| Evaluation pending | TBD | TBD | Feature 1.1 in progress |

> Part of the **IHB lab series**: six AI engineering projects by Irene (IHB-01 Finance Categorizer, IHB-02 Biotech RAG Assistant, IHB-03 Process Anomaly Detection, IHB-04 Operations SQL Agent, IHB-05 LoRA Extraction Model, IHB-06 Microscopy Cell Classifier).

## How it works

A bank CSV goes in, every row is validated, and each stored transaction gets a category from a fast ML model, with an LLM only for the cases the model is unsure about.

```mermaid
flowchart LR
    CSV[/"Bank CSV<br/>Fecha;Concepto;Importe"/] --> UP["POST /transactions/upload<br/>Feature 1.1 (planned)"]
    UP --> ROW["✓ TransactionRow<br/>validates each row"]
    ROW -->|valid| DB[("SQLite<br/>dedupe hash UNIQUE<br/>(planned)")]
    ROW -->|invalid| ERR["Error list<br/>row + reason (planned)"]
    DB --> LAB["Labeling CLI<br/>200 rows · 1.2 (planned)"]
    LAB --> ML["TF-IDF + LogReg<br/>1.3 (planned)"]
    ML -->|confident| OUT["category + confidence<br/>(planned)"]
    ML -->|unsure| LLM["LLM fallback<br/>1.4 (planned)"]
    LLM --> OUT

    classDef step fill:#FBFAF6,stroke:#24466B,color:#1B2A2F
    classDef good fill:#FBFAF6,stroke:#1F7A5A,stroke-width:2px,color:#1B2A2F
    classDef planned fill:#FBFAF6,stroke:#5F6B6E,stroke-dasharray:4 3,color:#5F6B6E
    class CSV step
    class ROW good
    class UP,DB,ERR,LAB,ML,OUT,LLM planned
```

Solid green border = built and tested. Dashed = planned. Diagram conventions live in [docs/STYLE.md](docs/STYLE.md).

## Engineering decisions
Every technical choice, with the options I rejected and why: [docs/DECISIONS.md](docs/DECISIONS.md).

## Learning log
What I built each session and what I learned: [docs/LEARNING_LOG.md](docs/LEARNING_LOG.md).

## License
[MIT](LICENSE)
