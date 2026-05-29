from src.api.currency_client import CurrencyClient


class MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_calculate_erg_value_uses_supported_conversion_modes():
    client = CurrencyClient()
    rates = {"SigUSD": 2.0, "GORT": 4.0, "RSN": 8.0, "BENE": 5.0, "gGOLD": 10.0}

    assert client.calculate_erg_value("12", "ERG", rates) == 12.0
    assert client.calculate_erg_value("10", "SigUSD", rates) == 5.0
    assert client.calculate_erg_value("8", "GORT", rates) == 2.0
    assert client.calculate_erg_value("16", "RSN", rates) == 2.0
    assert client.calculate_erg_value("15", "BENE", rates) == 3.0
    assert client.calculate_erg_value("3", "g GOLD", rates) == 30.0


def test_calculate_erg_value_returns_zero_for_unknown_or_non_amounts():
    client = CurrencyClient()

    assert client.calculate_erg_value("Not specified", "ERG", {}) == 0.0
    assert client.calculate_erg_value("Ongoing", "ERG", {}) == 0.0
    assert client.calculate_erg_value("10", "UNKNOWN", {}) == 0.0
    assert client.calculate_erg_value("abc", "ERG", {}) == 0.0


def test_fetch_spectrum_rates_prefers_highest_volume_sigusd_market(monkeypatch):
    client = CurrencyClient()

    markets = [
        {"baseSymbol": "ERG", "quoteSymbol": "SigUSD", "lastPrice": "3", "baseVolume": {"value": "10"}},
        {"baseSymbol": "ERG", "quoteSymbol": "SigUSD", "lastPrice": "2", "baseVolume": {"value": "20"}},
        {"baseSymbol": "ERG", "quoteSymbol": "GORT", "lastPrice": "4"},
        {"baseSymbol": "ERG", "quoteSymbol": "RSN", "lastPrice": "5"},
        {"baseSymbol": "ERG", "quoteSymbol": "OTHER", "lastPrice": "100"},
    ]

    def fake_get(url, timeout):
        assert url == client.SPECTRUM_API_URL
        assert timeout == client.timeout
        return MockResponse(200, markets)

    monkeypatch.setattr(client.session, "get", fake_get)

    client._fetch_spectrum_rates()

    assert client.rates["SigUSD"] == 2.0
    assert client.rates["GORT"] == 4.0
    assert client.rates["RSN"] == 5.0


def test_fetch_gold_price_reads_oracle_register(monkeypatch):
    client = CurrencyClient()
    oracle_payload = {
        "items": [
            {
                "additionalRegisters": {
                    "R4": {"renderedValue": "100000000000000"}
                }
            }
        ]
    }

    def fake_get(url, timeout):
        assert client.XAU_ERG_ORACLE_NFT in url
        assert timeout == 60
        return MockResponse(200, oracle_payload)

    monkeypatch.setattr(client.session, "get", fake_get)

    client._fetch_gold_price()

    assert client.rates["gGOLD"] == 100.0
