# Healio Multi-Agent Pipeline
# Phase 2: Core AI Agents
# Phase 4: Vision Agent for Image Analysis
# Lazy-load agents to avoid import errors during startup

def __getattr__(name):
    """Lazy-load agent functions on demand"""
    if name == "run_agent1":
        from .agent1_intake import run_agent1
        return run_agent1
    elif name == "run_agent1_async":
        from .agent1_intake import run_agent1_async
        return run_agent1_async
    elif name == "run_agent2":
        from .agent2_reasoning import run_agent2
        return run_agent2
    elif name == "run_agent2_async":
        from .agent2_reasoning import run_agent2_async
        return run_agent2_async
    elif name == "run_agent3":
        from .agent3_handoff import run_agent3
        return run_agent3
    elif name == "run_agent3_async":
        from .agent3_handoff import run_agent3_async
        return run_agent3_async
    elif name == "format_for_firebase":
        from .agent3_handoff import format_for_firebase
        return format_for_firebase
    elif name == "format_for_surveillance":
        from .agent3_handoff import format_for_surveillance
        return format_for_surveillance
    elif name == "analyze_clinical_image":
        from .vision_agent import analyze_clinical_image
        return analyze_clinical_image
    elif name == "analyze_multiple_images":
        from .vision_agent import analyze_multiple_images
        return analyze_multiple_images
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "run_agent1", "run_agent1_async",
    "run_agent2", "run_agent2_async",
    "run_agent3", "run_agent3_async",
    "format_for_firebase", "format_for_surveillance",
    "analyze_clinical_image", "analyze_multiple_images"
]

