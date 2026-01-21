# Zero to AI Agent - Jupyter Notebooks

**Interactive Jupyter Notebook version of the book's code examples**

This repository contains Jupyter notebook versions of all code from *Zero to AI Agent*. Each chapter has two notebooks:
- **Main notebook**: Content, examples, and exercises with empty practice cells
- **Solutions notebook**: Complete solutions to all exercises

---

## Repository Structure

```
zero-to-ai-agent-notebook/
├── part_1_python/                    # Part I: Python Foundations
│   ├── requirements.txt
│   ├── chapter_01_setup.ipynb
│   ├── chapter_01_setup_solutions.ipynb
│   ├── chapter_02_variables.ipynb
│   ├── chapter_02_variables_solutions.ipynb
│   ├── ... (chapters 03-06)
│
├── part_2_ai_basics/                 # Part II: AI and LLM Fundamentals
│   ├── requirements.txt
│   ├── chapter_07_intro_ai_llm.ipynb
│   ├── ... (chapters 08-09)
│
├── part_3_agents/                    # Part III: Building AI Agents
│   ├── requirements.txt
│   ├── chapter_10_what_are_agents.ipynb
│   ├── ... (chapters 11-13)
│
├── part_4_langgraph/                 # Part IV: Advanced Agent Development
│   ├── requirements.txt
│   ├── chapter_14_langgraph_intro.ipynb
│   ├── ... (chapters 15-17)
│
├── part_5_production/                # Part V: Production-Ready Agents
│   ├── requirements.txt
│   ├── chapter_18_testing.ipynb
│   ├── ... (chapters 19-20)
│
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.13+**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ksankaran/zero-to-ai-agent-notebook.git
   cd zero-to-ai-agent-notebook
   ```

2. **Navigate to the part you're working on**
   ```bash
   cd part_1_python
   ```

3. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   # or: .venv\Scripts\activate  # Windows
   ```

   > **Note:** Using `.venv` (with a dot) keeps the folder hidden in Jupyter's file explorer.

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start Jupyter**
   ```bash
   jupyter notebook
   ```

---

## Using the Notebooks

### Main Notebooks (`chapter_XX_name.ipynb`)

Each main notebook contains:
1. **Setup cell** - Run first to install dependencies
2. **Content sections** - Code examples with explanations
3. **Exercise sections** - Practice problems with empty cells for your solutions

### Solutions Notebooks (`chapter_XX_name_solutions.ipynb`)

Contains complete solutions to all exercises. **Try solving exercises yourself first!**

---

## API Keys

Parts 2-5 require API keys. Create a `.env` file in each part's directory:

```bash
# .env
OPENAI_API_KEY=your-openai-key-here
LANGSMITH_API_KEY=your-langsmith-key-here  # Optional, for tracing
```

The setup cell in each notebook will load these automatically.

---

## Quick Reference

| Part | Chapters | Topics |
|------|----------|--------|
| Part 1 | 01-06 | Python basics (no API keys needed) |
| Part 2 | 07-09 | AI/LLM fundamentals, first API calls |
| Part 3 | 10-13 | Building agents with LangChain |
| Part 4 | 14-17 | Advanced agents with LangGraph |
| Part 5 | 18-20 | Testing, deployment, capstone |

---

## Troubleshooting

### Kernel not found
Make sure you activated the virtual environment before starting Jupyter:
```bash
source .venv/bin/activate  # Mac/Linux
```

### Package installation fails
Try upgrading pip first:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### API errors
Verify your `.env` file exists and contains valid API keys.

---

## Contributing

Found an error? Open an issue or submit a PR!

---

## License

Educational companion to *Zero to AI Agent*.

**Happy Learning!**
