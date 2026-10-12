# Print the Alembic revision chain; flag multiple heads or dangling parents.
import os
import re
import sys

VERSIONS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "backend", "alembic", "versions"
)

chain: dict[str, str | None] = {}
for name in sorted(os.listdir(VERSIONS)):
    if not name.endswith(".py"):
        continue
    text = open(os.path.join(VERSIONS, name), encoding="utf-8").read()
    revision = re.search(r"revision\s*(?::\s*[^=]+)?=\s*[\"']([^\"']+)[\"']", text)
    if not revision:
        continue
    down = re.search(
        r"down_revision\s*(?::\s*[^=]+)?=\s*(?:[\"']([^\"']+)[\"']|None)", text
    )
    chain[revision.group(1)] = down.group(1) if down and down.group(1) else None

pointed_to = {parent for parent in chain.values() if parent}
heads = [rev for rev in chain if rev not in pointed_to]
dangling = [parent for parent in chain.values() if parent and parent not in chain]

print(f"revisions: {len(chain)}")
print(f"heads    : {heads}")
print(f"dangling : {dangling}")
sys.exit(1 if len(heads) > 1 or dangling else 0)
