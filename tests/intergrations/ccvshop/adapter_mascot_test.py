import pytest
from pydantic import ValidationError
from syncly.intergrations.ccvshop.adapters.adapter_mascot import MascotAdapter
from syncly.clients.mascot.client import InMemoryFTPClient
from syncly.config import SynclySettings
from syncly.utils import get_env, load_env_files

@pytest.fixture
def mascot_adapter() -> MascotAdapter:
    settings = SynclySettings.from_yaml("settings/mascot_test.yaml")
    load_env_files(".env")
    client = InMemoryFTPClient(
        host=get_env("MASCOT_FTP_HOST"),
        user=get_env("MASCOT_FTP_USER"),
        password=get_env("MASCOT_FTP_PASSWORD")
    )
    adapter = MascotAdapter(settings=settings, client=client)
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

    for product in products:
        splitted_name = product.name.split(' ')
        assert "nan" not in splitted_name

    assert products, "No Products loaded in"
