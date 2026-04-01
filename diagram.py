import json


def topology_to_cytoscape_elements(topology: dict) -> str:
    """Convert topology dict to Cytoscape.js elements JSON for frontend use."""
    elements = []

    for node in topology.get("nodes", []):
        elements.append({
            "group": "nodes",
            "data": {
                "id": node["id"],
                "label": node.get("label", node["id"]),
                "type": node.get("type", "switch"),
                "layer": node.get("layer", "access"),
            }
        })

    for i, link in enumerate(topology.get("links", [])):
        elements.append({
            "group": "edges",
            "data": {
                "id": f"e{i}",
                "source": link["source"],
                "target": link["target"],
                "label": link.get("label", ""),
                "bandwidth": link.get("bandwidth", ""),
                "linkType": link.get("link_type", "ethernet"),
            }
        })

    return json.dumps(elements, ensure_ascii=False)
