from typing import Dict, List, Optional
from sqlmodel import select
from db.database import get_domain_tree_session
from db.models import Domain
import json


def build_tree(domains: List[Domain], parent_id: Optional[str] = None) -> List[Dict]:
    """Recursively build tree structure from domain list."""
    tree = []
    # Get all children for current parent
    children = [d for d in domains if d.parent == parent_id]
    # Sort children by sort field if available, then by name
    children.sort(
        key=lambda x: (x.sort if x.sort is not None else float("inf"), x.name)
    )

    for child in children:
        node = {"id": child.id, "name": child.name}
        # Recursively get children
        child_nodes = build_tree(domains, child.id)
        if child_nodes:
            node["children"] = child_nodes
        tree.append(node)

    return tree


def export_domain_tree():
    """Export domain table as tree structure JSON."""
    with get_domain_tree_session() as session:
        # Get all domains ordered by level to ensure proper tree building
        statement = select(Domain).order_by(Domain.level)
        domains = session.exec(statement).all()

        # Build tree starting from root nodes (parent is None)
        tree = build_tree(domains)

        # Write to JSON file
        with open("domain_tree.json", "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    export_domain_tree()
