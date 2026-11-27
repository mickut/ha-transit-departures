from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import custom_components.transit_departures.config_flow as config_flow
from custom_components.transit_departures.api import StopSearchResult, TransitApiError
from custom_components.transit_departures.config_flow import (
    CONF_NUMBER_OF_DEPARTURES,
    CONF_STOP_ID,
    CONF_STOP_LOOKUP_QUERY,
    TransitStopSubentryFlowHandler,
    _decode_stop_selection,
    _encode_stop_selection,
    _normalize_single_stop_id,
)


def test_encode_decode_stop_selection_round_trip() -> None:
    encoded = _encode_stop_selection("HSL:1040273", "Helsinki Main")

    assert _decode_stop_selection(encoded) == ("HSL:1040273", "Helsinki Main")


def test_decode_stop_selection_rejects_invalid_payload() -> None:
    assert _decode_stop_selection("not-json") is None
    assert _decode_stop_selection('{"foo":"bar"}') is None


def test_normalize_single_stop_id_strips_prefix_and_suffix() -> None:
    assert _normalize_single_stop_id(" GTFS:HSL:1040273#H1243 ") == "HSL:1040273"
    assert _normalize_single_stop_id(" ") == ""


@pytest.mark.asyncio
async def test_subentry_user_step_lookup_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    handler.hass = object()

    def fake_show_form(*, step_id, data_schema, errors):
        return {"type": "form", "step_id": step_id, "errors": errors}

    class FailingApi:
        async def async_search_stops(self, query: str):
            raise TransitApiError("failure")

    monkeypatch.setattr(handler, "async_show_form", fake_show_form)
    monkeypatch.setattr(config_flow, "async_get_clientsession", lambda hass: object())
    monkeypatch.setattr(config_flow, "TransitApiClient", lambda session: FailingApi())

    result = await handler.async_step_user(
        {
            CONF_STOP_LOOKUP_QUERY: "helsinki",
            CONF_STOP_ID: "",
        }
    )

    assert result["type"] == "form"
    assert result["errors"][CONF_STOP_LOOKUP_QUERY] == "lookup_failed"


@pytest.mark.asyncio
async def test_subentry_user_step_no_search_results(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    handler.hass = object()

    def fake_show_form(*, step_id, data_schema, errors):
        return {"type": "form", "step_id": step_id, "errors": errors}

    class EmptyApi:
        async def async_search_stops(self, query: str):
            return []

    monkeypatch.setattr(handler, "async_show_form", fake_show_form)
    monkeypatch.setattr(config_flow, "async_get_clientsession", lambda hass: object())
    monkeypatch.setattr(config_flow, "TransitApiClient", lambda session: EmptyApi())

    result = await handler.async_step_user(
        {
            CONF_STOP_LOOKUP_QUERY: "helsinki",
            CONF_STOP_ID: "",
        }
    )

    assert result["type"] == "form"
    assert result["errors"][CONF_STOP_LOOKUP_QUERY] == "no_search_results"


@pytest.mark.asyncio
async def test_subentry_user_step_search_success_transitions_to_select(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    handler.hass = object()

    class SuccessApi:
        async def async_search_stops(self, query: str):
            return [StopSearchResult(stop_id="HSL:1040273", label="Helsinki Main")]

    next_step_result = {"type": "form", "step_id": "select_stop"}
    monkeypatch.setattr(config_flow, "async_get_clientsession", lambda hass: object())
    monkeypatch.setattr(config_flow, "TransitApiClient", lambda session: SuccessApi())
    monkeypatch.setattr(handler, "async_step_select_stop", AsyncMock(return_value=next_step_result))

    result = await handler.async_step_user(
        {
            CONF_STOP_LOOKUP_QUERY: "helsinki",
            CONF_STOP_ID: "",
        }
    )

    assert result == next_step_result
    assert handler._search_results == [{"stop_id": "HSL:1040273", "title": "Helsinki Main"}]


@pytest.mark.asyncio
async def test_create_stop_subentry_aborts_if_already_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    monkeypatch.setattr(
        handler,
        "_get_entry",
        lambda: SimpleNamespace(subentries={"sub-1": SimpleNamespace(unique_id="HSL:1040273")}),
    )
    monkeypatch.setattr(handler, "async_abort", lambda *, reason: {"type": "abort", "reason": reason})

    result = await handler._async_create_stop_subentry("HSL:1040273", "Helsinki Main")

    assert result == {"type": "abort", "reason": "already_configured"}


@pytest.mark.asyncio
async def test_create_stop_subentry_stores_custom_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    monkeypatch.setattr(handler, "_get_entry", lambda: SimpleNamespace(subentries={}))
    monkeypatch.setattr(
        handler,
        "async_create_entry",
        lambda *, title, unique_id, data: {
            "type": "create_entry",
            "title": title,
            "unique_id": unique_id,
            "data": data,
        },
    )

    result = await handler._async_create_stop_subentry(
        "HSL:1040273",
        "Helsinki Main",
        stop_suffix="Gate A",
        disable_stop_suffix=False,
    )

    assert result["data"] == {
        "stop_id": "HSL:1040273",
        "disable_stop_suffix": False,
        "stop_suffix": "Gate A",
    }


@pytest.mark.asyncio
async def test_create_stop_subentry_stores_disable_stop_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    monkeypatch.setattr(handler, "_get_entry", lambda: SimpleNamespace(subentries={}))
    monkeypatch.setattr(
        handler,
        "async_create_entry",
        lambda *, title, unique_id, data: {
            "type": "create_entry",
            "title": title,
            "unique_id": unique_id,
            "data": data,
        },
    )

    result = await handler._async_create_stop_subentry(
        "HSL:1040273",
        "Helsinki Main",
        stop_suffix="Gate A",
        disable_stop_suffix=True,
    )

    assert result["data"] == {"stop_id": "HSL:1040273", "disable_stop_suffix": True}


@pytest.mark.asyncio
async def test_subentry_reconfigure_updates_departure_count(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    monkeypatch.setattr(
        handler, "_get_entry", lambda: SimpleNamespace(data={CONF_NUMBER_OF_DEPARTURES: 4})
    )
    monkeypatch.setattr(
        handler, "_get_reconfigure_subentry", lambda: SimpleNamespace(data={CONF_STOP_ID: "HSL:1"})
    )
    captured: dict = {}

    def fake_update_and_abort(entry, subentry, *, data_updates):
        captured.update(data_updates)
        return {"type": "abort", "reason": "reconfigure_successful"}

    monkeypatch.setattr(handler, "async_update_and_abort", fake_update_and_abort)

    result = await handler.async_step_reconfigure({CONF_NUMBER_OF_DEPARTURES: 6.0})

    assert result["reason"] == "reconfigure_successful"
    assert captured == {CONF_NUMBER_OF_DEPARTURES: 6}
    assert isinstance(captured[CONF_NUMBER_OF_DEPARTURES], int)


@pytest.mark.asyncio
async def test_subentry_reconfigure_defaults_to_shared_count(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = TransitStopSubentryFlowHandler()
    monkeypatch.setattr(
        handler, "_get_entry", lambda: SimpleNamespace(data={CONF_NUMBER_OF_DEPARTURES: 5})
    )
    monkeypatch.setattr(handler, "_get_reconfigure_subentry", lambda: SimpleNamespace(data={}))
    captured: dict = {}

    def fake_show_form(*, step_id, data_schema, errors=None):
        captured["schema"] = data_schema
        return {"type": "form", "step_id": step_id}

    monkeypatch.setattr(handler, "async_show_form", fake_show_form)

    result = await handler.async_step_reconfigure(None)

    assert result["type"] == "form"
    schema_key = next(iter(captured["schema"].schema))
    assert schema_key.default() == 5


@pytest.mark.asyncio
async def test_main_flow_reconfigure_updates_shared_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    flow = config_flow.TransitDeparturesConfigFlow()
    entry = SimpleNamespace(
        data={
            CONF_NUMBER_OF_DEPARTURES: 4,
            config_flow.CONF_CUTOFF_MINUTES: 0,
            config_flow.CONF_UPDATE_INTERVAL_MINUTES: 15,
        }
    )
    monkeypatch.setattr(flow, "_get_reconfigure_entry", lambda: entry)
    captured: dict = {}

    def fake_update_reload_and_abort(entry_, *, data_updates):
        captured.update(data_updates)
        return {"type": "abort", "reason": "reconfigure_successful"}

    monkeypatch.setattr(flow, "async_update_reload_and_abort", fake_update_reload_and_abort)

    result = await flow.async_step_reconfigure(
        {
            CONF_NUMBER_OF_DEPARTURES: 6,
            config_flow.CONF_CUTOFF_MINUTES: 5,
            config_flow.CONF_UPDATE_INTERVAL_MINUTES: 10,
        }
    )

    assert result["reason"] == "reconfigure_successful"
    assert captured == {
        CONF_NUMBER_OF_DEPARTURES: 6,
        config_flow.CONF_CUTOFF_MINUTES: 5,
        config_flow.CONF_UPDATE_INTERVAL_MINUTES: 10,
    }
