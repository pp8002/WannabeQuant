def render_edges(edges, nodes):
    svg_parts = []
    for idx, edge in enumerate(edges):
        start_node = next(n for n in nodes if n["id"] == edge["from"])
        end_node = next(n for n in nodes if n["id"] == edge["to"])
        delay = idx * 0.2  # postupné vykreslení

        # Barva a třída podle stavu
        if edge.get("status") == "completed":
            css_class = "edge-line edge-completed"
        elif edge.get("status") == "active":
            css_class = "edge-line edge-active"
        else:
            css_class = "edge-line"

        # Výpočet délky cesty (pro správný stroke-dasharray)
        x1, y1 = start_node["position"]
        x2, y2 = end_node["position"]
        length = ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5

        svg_parts.append(f'''
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                  class="{css_class}"
                  stroke-dasharray="{length}"
                  stroke-dashoffset="{length}"
                  style="animation-delay: {delay}s;" />
        ''')

    return "\n".join(svg_parts)
