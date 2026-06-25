# Contributing to Solar AI Advisor

Thank you for considering contributing to Solar AI Advisor! This guide explains how to get involved.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Checklist](#pull-request-checklist)

---

## Code of Conduct

Be respectful and constructive. Discrimination or harassment of any kind is not tolerated.

---

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/solar_ai_advisor.git
   cd solar_ai_advisor
   ```
3. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac / Linux
   source venv/bin/activate

   pip install -r requirements.txt
   ```
4. **Set up environment variables**:
   ```bash
   cp .env.example .env   # or: copy .env.example .env  (Windows)
   # Edit .env and add your GEMINI_API_KEY
   ```
5. **Build the FAISS index** (only needed once, or when documents change):
   ```bash
   python build_rag.py
   ```
6. **Run the app**:
   ```bash
   streamlit run app.py
   ```

---

## How to Contribute

### 🐛 Reporting Bugs

- Open a [GitHub Issue](../../issues/new?template=bug_report.md).
- Include: Python version, OS, steps to reproduce, expected behaviour, actual behaviour.

### 💡 Suggesting Features

- Open a [GitHub Issue](../../issues/new?template=feature_request.md) labelled `enhancement`.
- Describe the use-case and why it would benefit users.

### 🔧 Submitting Code

- Fix a bug, implement a feature, or improve documentation.
- Follow the Development Workflow below.

---

## Development Workflow

```
main  ←  your feature branch
```

1. Create a branch from `main`:
   ```bash
   git checkout -b feature/short-description
   ```
2. Make your changes.
3. Run tests:
   ```bash
   python test_calculator.py
   python test_time_series.py
   ```
4. Commit (see [Commit Messages](#commit-messages)).
5. Push and open a Pull Request against `main`.

---

## Coding Standards

- Follow **PEP 8** for Python code.
- Use descriptive variable names — avoid single letters except for loop counters.
- Add a docstring to every public function.
- Keep functions small and single-purpose.
- Do **not** hardcode API keys or secrets in source files.

---

## Commit Messages

Use the Conventional Commits format:

```
type(scope): short description

Optional longer description here.
```

| Type       | When to use                         |
|------------|-------------------------------------|
| `feat`     | New feature                         |
| `fix`      | Bug fix                             |
| `docs`     | Documentation only                  |
| `style`    | Formatting, no logic change         |
| `refactor` | Code restructuring, no feature change |
| `test`     | Adding or updating tests            |
| `chore`    | Build process, tooling              |

**Examples:**
```
feat(chatbot): add Hindi language support
fix(calculator): handle zero-area rooftop gracefully
docs(readme): correct Streamlit run command
```

---

## Pull Request Checklist

Before opening a PR, confirm:

- [ ] Tests pass (`python test_calculator.py` and `python test_time_series.py`)
- [ ] Code follows PEP 8
- [ ] Docstrings added to new functions
- [ ] No API keys or secrets committed
- [ ] `requirements.txt` updated if new packages were added
- [ ] `README.md` updated if behaviour changed
- [ ] PR description clearly explains what changed and why

---

Thank you for helping make Solar AI Advisor better! ☀️
