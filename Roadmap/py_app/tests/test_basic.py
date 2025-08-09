from core.utils import load_roadmap

def test_load_roadmap_ok():
    rm = load_roadmap("data/roadmap.json")
    assert len(rm.nodes) == 2
    assert len(rm.edges) == 1
    assert rm.nodes[0].id == "python_basics"

