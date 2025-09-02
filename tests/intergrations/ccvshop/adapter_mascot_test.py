import pytest
from syncly.intergrations.ccvshop.adapters.adapter_mascot import MascotAdapter
from syncly.clients.mascot.client import InMemoryFTPClient
from syncly.config import EnvSettings, SynclySettings

@pytest.fixture
def mascot_adapter() -> MascotAdapter:
    settings = SynclySettings.from_yaml("settings/mascot_test.yaml")
    cfg = EnvSettings().from_env_file(".env")
    client = InMemoryFTPClient(
        host=cfg.get("MASCOT_FTP_HOST"),
        user=cfg.get("MASCOT_FTP_USER"),
        password=cfg.get("MASCOT_FTP_PASSWORD")
    )
    adapter = MascotAdapter(cfg=cfg, settings=settings, client=client)
    return adapter

@pytest.mark.integration
def test_mascot_adapter_get_products(mascot_adapter):
    products = list(mascot_adapter._get_products())
    assert products, "No products were loaded from FTP server"
    # Optionally, add more assertions about product fields
    for product in products:
        assert "ean_number" in product
        assert "article_number" in product
        assert "stock_status" in product
        assert "reorder_status" in product

@pytest.mark.integration
def test_mascot_load_products(mascot_adapter):
    mascot_adapter.load_products()
    products = mascot_adapter.get_all(mascot_adapter.product)
    assert products, "No Products loaded in"
