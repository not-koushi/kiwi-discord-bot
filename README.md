# Kiwi 🥝
Modular Moderation & Utility Discord Bot (Pycord)

Kiwi is a Discord bot engineered with a strong emphasis on **modular design, auditability, and maintainability**. The project demonstrates real-world bot architecture using modern Discord slash commands, persistent moderation logging, and server-scoped configuration.

This repository is intended as a **technical portfolio project**, not as a public bot distribution.

---

## What This Project Demonstrates

- Clean, cog-based architecture using Pycord
- Production-style moderation workflows with attribution
- Persistent, server-isolated data storage (SQLite)
- Event-driven design aligned with Discord audit logs
- Defensive handling of edge cases (e.g., ban vs leave events)

---

## Key Features

### Moderation & Compliance
- Warning system with logged reasons
- Per-server warning history
- Automatic banning after a configurable warning threshold
- Timeout, kick, and ban tracking with moderator attribution
- Intelligent suppression of duplicate leave events on bans

### Logging & Persistence
- Structured moderation logs per server
- SQLite-backed persistence layer
- Automatic creation and management of required data directories
- Embed-based logging for clarity and traceability

### Utilities
- General server utility commands
- Role management helpers
- Slash-command-first interface

---

## Code Structure

bot/
  kiwi_bot.py
  config.py
  cogs/
    general.py
    modlogs.py
    roles.py
    utility.py
    warns.py


Data and log directories are created dynamically at runtime.

---

## Architectural Highlights

- **Cog Isolation**  
  Each functional domain is encapsulated, reducing coupling and improving extensibility.

- **Persistent State Management**  
  Moderation data is stored using SQLite with per-guild isolation where applicable.

- **Modern Discord API Usage**  
  All interactions are implemented via slash commands and event listeners.

---

## Design Principles

- Maintainability over shortcuts  
- Explicit logic over abstraction  
- Auditability over silent automation  
- Scalable structure suitable for long-term extension

---

## Scope & Intent

- No public deployment
- No setup or installation guide
- No secrets or credentials included
- Built strictly as a **code quality and system design showcase**

---

## Author

Developed by **Koushik Panchadarla**.

Focused on clean system design, security-conscious development, and maintainable Discord bots.

---

Kiwi reflects an emphasis on reliability, clarity, and accountability in moderation systems.
