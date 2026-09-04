import json
import sys
from pathlib import Path


def children(node):
    """Return dictionary children, ignoring null CST entries."""
    if not isinstance(node, dict):
        return []

    return [
        child
        for child in node.get("children", [])
        if isinstance(child, dict)
    ]


def walk(node):
    """Depth-first traversal of the Verible CST."""
    if not isinstance(node, dict):
        return

    yield node

    for child in children(node):
        yield from walk(child)


def find_tag(node, tag):
    """Find the first descendant with the requested tag."""
    for item in walk(node):
        if item.get("tag") == tag:
            return item
    return None


def find_all_tags(node, tag):
    """Find all descendants with the requested tag."""
    return [
        item for item in walk(node)
        if item.get("tag") == tag
    ]


def identifier(node):
    """Get the first SymbolIdentifier directly/indirectly in a node."""
    item = find_tag(node, "SymbolIdentifier")
    return item.get("text") if item else None


def number(node):
    """Get a numeric literal from a CST expression."""
    item = find_tag(node, "TK_DecNumber")
    if item:
        return item.get("text")

    return None


def expression(node):
    """
    Convert a small Verible expression subtree into a structured
    representation.

    This intentionally does not parse the original RTL.
    """

    if node is None:
        return None

    # Simple identifier/reference.
    ident = find_tag(node, "SymbolIdentifier")
    if ident:
        return {
            "kind": "identifier",
            "value": ident.get("text")
        }

    # Decimal number.
    dec = find_tag(node, "TK_DecNumber")
    if dec:
        return {
            "kind": "number",
            "value": dec.get("text")
        }

    # Binary expression, e.g. WIDTH - 1.
    if node.get("tag") == "kBinaryExpression":
        kids = children(node)

        if len(kids) >= 3:
            op = next(
                (
                    child.get("tag")
                    for child in kids
                    if child.get("tag") in {"+", "-", "*", "/", "%"}
                ),
                None,
            )

            if op:
                operands = [
                    child
                    for child in kids
                    if child.get("tag") != op
                ]

                if len(operands) >= 2:
                    return {
                        "kind": "binary",
                        "operator": op,
                        "left": expression(operands[0]),
                        "right": expression(operands[-1]),
                    }

    # Look through expression wrappers.
    kids = children(node)

    for child in kids:
        result = expression(child)

        if result is not None:
            return result

    return None


def extract_range(dimension):
    """
    Extract a packed range such as [WIDTH-1:0] directly from
    the CST structure.
    """

    range_node = dimension

    expressions = []

    for child in children(range_node):
        if child.get("tag") == "kExpression":
            value = expression(child)

            if value is not None:
                expressions.append(value)

    if len(expressions) >= 2:
        return {
            "left": expressions[0],
            "right": expressions[1],
        }

    return None


def extract_width(data_type):
    """Extract packed dimensions from a kDataType node."""

    packed = find_tag(data_type, "kPackedDimensions")

    if not packed:
        return None

    ranges = find_all_tags(packed, "kDimensionRange")

    if not ranges:
        return None

    # Support multiple packed dimensions.
    result = []

    for item in ranges:
        value = extract_range(item)

        if value:
            result.append(value)

    if not result:
        return None

    return result[0] if len(result) == 1 else result


def find_module(tree):
    return find_tag(tree, "kModuleDeclaration")


def extract_parameters(module):
    parameters = []

    for declaration in find_all_tags(module, "kParamDeclaration"):

        name = identifier(declaration)

        if not name:
            continue

        default = None

        trailing = find_tag(
            declaration,
            "kTrailingAssign"
        )

        if trailing:
            expressions = find_all_tags(
                trailing,
                "kExpression"
            )

            if expressions:
                default = expression(expressions[-1])

        parameters.append(
            {
                "name": name,
                "default": default,
            }
        )

    return parameters


def extract_ports(module):
    ports = []

    for declaration in find_all_tags(
        module,
        "kPortDeclaration"
    ):

        direction = None

        for child in children(declaration):
            tag = child.get("tag")

            if tag in {"input", "output", "inout"}:
                direction = tag
                break

        if direction is None:
            continue

        # kUnqualifiedId contains the actual port identifier.
        name = None

        for child in children(declaration):
            if child.get("tag") == "kUnqualifiedId":
                name = identifier(child)
                break

        if not name:
            continue

        port = {
            "name": name,
            "direction": direction,
        }

        # Width/type information comes from kDataType.
        data_type = None

        for child in children(declaration):
            if child.get("tag") == "kDataType":
                data_type = child
                break

        if data_type:
            width = extract_width(data_type)

            if width:
                port["width"] = width

            primitive = find_tag(
                data_type,
                "kDataTypePrimitive"
            )

            if primitive:
                # Extract the actual primitive type token.
                for item in walk(primitive):
                    if item.get("tag") in {
                        "logic",
                        "bit",
                        "wire",
                        "reg",
                        "integer",
                        "int",
                    }:
                        port["type"] = item["tag"]
                        break

        ports.append(port)

    return ports


def extract(cst):
    tree = cst["tree"]

    module = find_module(tree)

    if module is None:
        raise ValueError("No module declaration found")

    module_name = identifier(module)

    return {
        "module": module_name,
        "parameters": extract_parameters(module),
        "ports": extract_ports(module),
    }


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python extract_concise.py "
            "<cst.json> <output.json>"
        )
        sys.exit(1)

    cst_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    data = json.loads(cst_path.read_text())

    if len(data) != 1:
        raise ValueError(
            "Expected exactly one Verible source entry"
        )

    cst = next(iter(data.values()))

    if cst is None:
        raise ValueError(
            "Verible returned no parse tree"
        )

    result = extract(cst)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(result, indent=2) + "\n"
    )

    print(
        f"Wrote concise RTL information to {output_path}"
    )


if __name__ == "__main__":
    main()