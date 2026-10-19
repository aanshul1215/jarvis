from datetime import timedelta

from jarvis.contracts import AssetClass, utc_now
from jarvis.information import InformationDocument, ingest
from jarvis.storage import LocalStorage


def test_local_information_is_idempotent_and_has_no_trade_authority(tmp_path):
    now = utc_now() - timedelta(minutes=1)
    document = InformationDocument("BTC/USD", AssetClass.CRYPTO, "TEST_SOURCE", "https://example.invalid/story",
                                   now, now, "EVENT", "BTC/USD volume growth was reported. A loss was also reported.")
    with LocalStorage(tmp_path / "desk") as store:
        first = ingest(store, document)
        second = ingest(store, document)
        assert first == second
        assert first["trade_authority"] == "NONE"
        assert first["validation"] == "UNVALIDATED"
        assert len([e for e in store.read_events() if e["event"]["event_type"] == "INFO_FEATURE"]) == 1
