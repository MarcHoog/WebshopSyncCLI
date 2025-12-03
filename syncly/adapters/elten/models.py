"""
Data models for Elten adapter.

This module defines TypedDict models representing the structure of Elten CSV data.
"""

from typing import Optional, TypedDict


class ProductRow(TypedDict, total=False):
    """
    TypedDict model representing a single row from the Elten CSV file.

    Maps to the CSV columns provided by Elten.
    """
    # Supplier information
    supplier_iln: Optional[str]  # LIEFERANTEN_ILN
    supplier_name: Optional[str]  # LIEFERANTEN_NAME

    # Article identification
    manufacturer_ean: Optional[str]  # HERSTELLER_ARTIKELEAN
    manufacturer_article_nr_index: Optional[str]  # HERSTELLER_ARTIKELNR_INDEX
    manufacturer_article_nr: Optional[str]  # HERSTELLER_ARTIKELNR
    manufacturer_article_size: Optional[str]  # HERSTELLER_ARTIKELGROESSE
    manufacturer_article_range: Optional[str]  # HERSTELLER_ARTIKELSORTIMENT
    manufacturer_article_name: Optional[str]  # HERSTELLER_ARTIKELNAME
    manufacturer_article_description_1: Optional[str]  # HERSTELLER_ARTIKELBEZEICHNUNG1
    manufacturer_article_description_2: Optional[str]  # HERSTELLER_ARTIKELBEZEICHNUNG2
    manufacturer_article_group: Optional[str]  # HERSTELLER_ARTIKELGRUPPE

    # Pricing and validity
    valid_from: Optional[str]  # GUELTIG_AB
    currency: Optional[str]  # WAEHRUNG
    vat_domestic: Optional[str]  # MWST_INLAND
    list_price: Optional[str]  # LISTENPREIS
    price_unit: Optional[str]  # PREISEINHEIT

    # Customs and origin
    customs_tariff_number: Optional[str]  # ZOLLTARIFNR
    country_of_origin: Optional[str]  # URSPRUNGSLAND
    country_of_origin_iso: Optional[str]  # URSPRUNGSLAND-ISO-3166-A2

    # Classification
    eclass: Optional[str]  # ECLASS
    eclass_version: Optional[str]  # ECLASS_VERSION

    # Physical properties
    weight_per_unit: Optional[str]  # GEWICHTPROME
    reference_unit: Optional[str]  # BEZUGS_ME
    content_unit: Optional[str]  # INHALT_ME
    content_quantity: Optional[str]  # INHALT_MENGE

    # Material specifications (A01-A14)
    upper_material: Optional[str]  # A01_OBERMATERIAL
    lining_material: Optional[str]  # A02_FUTTERMATERIAL
    tongue: Optional[str]  # A03_LASCHE
    insole: Optional[str]  # A04_EINLEGESOHLE
    midsole: Optional[str]  # A05_BRANDSOHLE
    puncture_protection: Optional[str]  # A06_DURCHTRITTSCHUTZ
    sole: Optional[str]  # A07_SOHLE
    toe_protection: Optional[str]  # A08_SPITZENSCHUTZ
    toe_cap: Optional[str]  # A10_ZEHENSCHUTZKAPPE
    norm: Optional[str]  # A09_NORM
    additional_info_1: Optional[str]  # A11_ZUSATZINFO1
    additional_info_2: Optional[str]  # A12_ZUSATZINFO2
    misc_1: Optional[str]  # A13_SONSTIGES1
    misc_2: Optional[str]  # A14_SONSTIGES2

    # Media
    media: Optional[str]  # MEDIA
