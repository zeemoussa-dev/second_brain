"""Template entity -- defines what a vault Note's shape is (note naming
rule, per-section write access, frontmatter defaults). TemplateManager
(2026-08-28) is the sole gateway onto this data -- folded in and retired
`data_access/templates/registry.py`. See template.py for the Template/
TemplateSection dataclass shape, template_manager.py for TemplateManager
itself, and its own module docstring for the real, deliberate distinction
from `app/vault/vault_manager.py`'s own, unrelated `load_template()`.
"""
