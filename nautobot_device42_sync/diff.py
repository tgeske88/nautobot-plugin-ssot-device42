"""Custom Diff Class for custom handling of object CRUD operations."""
from collections import defaultdict
from diffsync.diff import Diff


class CustomOrderingDiff(Diff):
    """Alternate diff class to list children in alphabetical order, except devices to be ordered by CRUD action."""

    @classmethod
    def order_children_default(cls, children):
        """Simple diff to return all children in alphabetical order."""
        for child_name, _ in sorted(children.items()):
            yield children[child_name]

    @classmethod
    def order_children_device(cls, children):
        """Return a list of device sorted by CRUD action, starting with deletion, then create, and update, along with being in alphabetical order."""
        children_by_type = defaultdict(list)

        # Organize the children's name by action create, update or delete
        for child_name, child in children.items():
            action = child.action or "skip"
            children_by_type[action].append(child_name)

        # Create a global list, organized per action, with deletion first to prevent conflicts
        sorted_children = sorted(children_by_type["delete"])
        sorted_children += sorted(children_by_type["create"])
        sorted_children += sorted(children_by_type["update"])
        sorted_children += sorted(children_by_type["skip"])

        for name in sorted_children:
            yield children[name]
