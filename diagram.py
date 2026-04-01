import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

# Visual config per node type
NODE_STYLE = {
    "cloud":        {"color": "#87CEEB", "marker": "s", "size": 1200},
    "firewall":     {"color": "#FF6B6B", "marker": "D", "size": 1000},
    "router":       {"color": "#4ECDC4", "marker": "o", "size": 1000},
    "switch":       {"color": "#45B7D1", "marker": "s", "size": 800},
    "server":       {"color": "#96CEB4", "marker": "^", "size": 900},
    "access_point": {"color": "#FFEAA7", "marker": "v", "size": 700},
    "pc":           {"color": "#DDA0DD", "marker": "o", "size": 500},
    "printer":      {"color": "#D3D3D3", "marker": "s", "size": 500},
}

LINK_STYLE = {
    "fiber":    {"color": "#FF6B6B", "style": "solid",  "width": 2.5},
    "ethernet": {"color": "#333333", "style": "solid",  "width": 1.5},
    "wireless": {"color": "#999999", "style": "dashed", "width": 1.0},
}

LAYER_Y = {"core": 3, "distribution": 2, "access": 1, "endpoint": 0}


def _compute_positions(nodes: list) -> dict:
    """Assign x,y positions using hierarchical layer layout."""
    layers = {}
    for node in nodes:
        layer = node.get("layer", "access")
        layers.setdefault(layer, []).append(node["id"])

    positions = {}
    for layer, node_ids in layers.items():
        y = LAYER_Y.get(layer, 0)
        count = len(node_ids)
        for i, nid in enumerate(node_ids):
            x = (i - (count - 1) / 2) * 2.5
            positions[nid] = (x, y)
    return positions


def generate_diagram(topology: dict) -> str:
    """Generate network topology diagram. Returns base64-encoded PNG string."""
    nodes = topology.get("nodes", [])
    links = topology.get("links", [])

    G = nx.Graph()
    node_map = {n["id"]: n for n in nodes}

    for node in nodes:
        G.add_node(node["id"])

    # Only add links where both endpoints exist
    valid_links = [
        lk for lk in links
        if lk.get("source") in node_map and lk.get("target") in node_map
    ]
    for lk in valid_links:
        G.add_edge(lk["source"], lk["target"], **lk)

    pos = _compute_positions(nodes)
    # Ensure all graph nodes have a position
    for nid in G.nodes():
        if nid not in pos:
            pos[nid] = (0, 0)

    # Dynamic figure size based on node count
    width = max(10, len(nodes) * 1.5)
    fig, ax = plt.subplots(figsize=(width, 8))
    ax.set_facecolor("#F8F9FA")
    fig.patch.set_facecolor("#F8F9FA")

    # Draw nodes per type
    type_groups = {}
    for node in nodes:
        t = node.get("type", "pc")
        type_groups.setdefault(t, []).append(node["id"])

    for ntype, nids in type_groups.items():
        style = NODE_STYLE.get(ntype, NODE_STYLE["pc"])
        nx.draw_networkx_nodes(
            G, pos,
            nodelist=nids,
            node_color=style["color"],
            node_shape=style["marker"],
            node_size=style["size"],
            ax=ax,
        )

    # Draw edges per link type
    link_groups = {}
    for lk in valid_links:
        lt = lk.get("link_type", "ethernet")
        link_groups.setdefault(lt, []).append((lk["source"], lk["target"]))

    for ltype, edge_list in link_groups.items():
        style = LINK_STYLE.get(ltype, LINK_STYLE["ethernet"])
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edge_list,
            edge_color=style["color"],
            style=style["style"],
            width=style["width"],
            ax=ax,
        )

    # Labels
    labels = {n["id"]: n.get("label", n["id"]) for n in nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, ax=ax)

    # Edge bandwidth labels
    edge_labels = {
        (lk["source"], lk["target"]): lk.get("bandwidth", "")
        for lk in valid_links if lk.get("bandwidth")
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7, ax=ax)

    # Legend
    legend_handles = [
        mpatches.Patch(color=style["color"], label=ntype.replace("_", " ").title())
        for ntype, style in NODE_STYLE.items()
        if ntype in type_groups
    ]
    ax.legend(handles=legend_handles, loc="upper right", fontsize=8)
    ax.set_title(topology.get("topology_name", "Network Topology"), fontsize=14, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


if __name__ == "__main__":
    sample = {
        "topology_name": "Office Network (Test)",
        "topology_type": "star",
        "nodes": [
            {"id": "cloud-1",    "label": "ISP/Internet",   "type": "cloud",        "layer": "core"},
            {"id": "fw-1",       "label": "Firewall",       "type": "firewall",     "layer": "core"},
            {"id": "router-1",   "label": "Core Router",    "type": "router",       "layer": "core"},
            {"id": "sw-core",    "label": "Core Switch",    "type": "switch",       "layer": "distribution"},
            {"id": "sw-f1",      "label": "Floor 1 Switch", "type": "switch",       "layer": "access"},
            {"id": "sw-f2",      "label": "Floor 2 Switch", "type": "switch",       "layer": "access"},
            {"id": "ap-f1",      "label": "AP Floor 1",     "type": "access_point", "layer": "access"},
            {"id": "ap-f2",      "label": "AP Floor 2",     "type": "access_point", "layer": "access"},
            {"id": "srv-1",      "label": "File Server",    "type": "server",       "layer": "distribution"},
        ],
        "links": [
            {"source": "cloud-1",  "target": "fw-1",     "link_type": "fiber",    "bandwidth": "1Gbps",  "label": "WAN"},
            {"source": "fw-1",     "target": "router-1", "link_type": "ethernet", "bandwidth": "1Gbps",  "label": ""},
            {"source": "router-1", "target": "sw-core",  "link_type": "fiber",    "bandwidth": "10Gbps", "label": "Trunk"},
            {"source": "sw-core",  "target": "sw-f1",    "link_type": "ethernet", "bandwidth": "1Gbps",  "label": ""},
            {"source": "sw-core",  "target": "sw-f2",    "link_type": "ethernet", "bandwidth": "1Gbps",  "label": ""},
            {"source": "sw-core",  "target": "srv-1",    "link_type": "ethernet", "bandwidth": "1Gbps",  "label": ""},
            {"source": "sw-f1",    "target": "ap-f1",    "link_type": "ethernet", "bandwidth": "100Mbps","label": "PoE"},
            {"source": "sw-f2",    "target": "ap-f2",    "link_type": "ethernet", "bandwidth": "100Mbps","label": "PoE"},
        ],
    }
    b64 = generate_diagram(sample)
    with open("test_diagram.png", "wb") as f:
        f.write(base64.b64decode(b64))
    print("Saved test_diagram.png")
