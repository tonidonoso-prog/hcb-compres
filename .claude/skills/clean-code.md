---
name: clean-code
description: "Embodies Clean Code principles by Robert C. Martin. Use to review or refactor code for readability, maintainability, and quality."
risk: safe
source: community
date_added: "2026-02-27"
---

# Clean Code Skill

> "Code is clean if it can be read, and enhanced by a developer other than its original author." — Grady Booch

## When to Use
- Writing new code — ensure quality from the start
- Reviewing pull requests — principle-based feedback
- Refactoring legacy code — identify and remove code smells

## 1. Meaningful Names
- Use intention-revealing names: `elapsed_time_days` not `d`
- Avoid disinformation: don't use `account_list` if it's a dict
- Class names: nouns (`Customer`, `MaterialCatalog`)
- Method names: verbs (`load_catalog`, `export_excel`, `search_refs`)

## 2. Functions
- **Do One Thing**: one function = one responsibility
- **Small**: shorter than you think
- **Descriptive names**: `buscar_por_referencia` better than `search`
- **Few arguments**: 0-2 ideal, 3+ needs justification
- **No side effects**: don't secretly change state

## 3. Comments
- Don't comment bad code — rewrite it
- Prefer self-documenting code over comments
- Good comments: clarify regex intent, external API quirks, TODOs

## 4. Formatting
- Related code close together (vertical density)
- Variables declared near usage
- High-level logic at top, details below

## 5. Error Handling
- Use exceptions, not return codes
- Don't return None — forces callers to check every time
- Handle errors at the appropriate level

## 6. Functions Checklist
- [ ] Function < 20 lines?
- [ ] Does exactly one thing?
- [ ] Names are searchable and intention-revealing?
- [ ] No unnecessary comments (code is self-explanatory)?
- [ ] ≤ 2 arguments?
- [ ] No hidden side effects?

## Code Smells to Watch
- **Rigidity**: hard to change
- **Fragility**: breaks in many places when changed
- **Needless complexity**: abstractions for single-use cases
- **Duplication**: same logic in multiple places
