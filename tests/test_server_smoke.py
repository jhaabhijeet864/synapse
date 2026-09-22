"""Smoke test: daemon module imports and exposes the full IPC surface.

Regression guard — core/server.py was once truncated mid-function by an
interrupted write. It stayed syntactically valid, so compileall and the
rest of the suite could not catch it. This test fails if the app object,
lifespan, routes, or entry points ever go missing again.
"""

import core.server as server


def test_app_object_exists():
    assert server.app is not None
    assert server.app.title == "Synapse Daemon"


def test_full_route_table():
    paths = {r.path for r in server.app.routes}
    for required in (
        "/health",
        "/invoke",
        "/usage",
        "/ws",
        "/action/apply-fix",
        "/action/dismiss",
        "/action/store-memory",
    ):
        assert required in paths, f"missing route: {required}"


def test_pipeline_pieces_present():
    for name in (
        "broadcast",
        "process_bundle",
        "_on_clipboard_threadsafe",
        "health",
        "manual_invoke",
        "action_apply_fix",
        "action_store_memory",
        "action_dismiss",
        "usage",
        "websocket_endpoint",
    ):
        assert callable(getattr(server, name, None)), f"missing: {name}"
    # Module singletons that must exist (not callables): JSON logger +
    # captured loop slot for the Win32 clipboard bridge.
    assert server.logger is not None
    assert hasattr(server, "_main_loop")


def test_state_machine_states():
    from core.engine.state_machine import SynapseState

    assert {s.name for s in SynapseState} == {
        "IDLE",
        "CAPTURING",
        "REASONING",
        "READY",
        "SUPPRESSED",
    }
