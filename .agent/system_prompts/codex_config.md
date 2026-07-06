# 💻 Codex CLI System Instructions

When starting a chat session using **Codex CLI**, load the system instructions directly:

```bash
codex chat --system-file Dhiraj-AI-Product-Analyst.md
```

**Persistent Shell Instructions:**
Configure your Codex configuration (`~/.codex/config.toml`) to load this prompt persistently whenever working in the product-analytics project:

```toml
[chat]
default_system_prompt_file = "Dhiraj-AI-Product-Analyst/Dhiraj-AI-Product-Analyst.md"
```
