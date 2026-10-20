# repo-multiverse

Before changing anything here, read "Core ideas" in README.md (繁體中文: README.zh-Hant.md, 「核心思想」). Every change must keep them.

- This is a session-management tool, not a git tool. Don't add script features for what plain git commands already do; put those steps in a SKILL.md instead.
- Prefer removing to adding. Earlier versions grew a combine lock, pre-combine scope checks, conflict scans, branch-number resolving and a cleanup command; 0.3.0 removed them on purpose. Don't add them back unless real use needs them.
- If something already works, leave it alone. Change only what real use shows is wrong.
- Keep README.md and README.zh-Hant.md in step; English is the default.
- All skills share `skills/repo-multiverse/scripts/multiverse.py` (Python 3.9+, standard library only). State lives in `~/.claude/multiverse/<repo-key>/`, never inside a user's repo.
- No comments in the script, and keep each SKILL.md short.
