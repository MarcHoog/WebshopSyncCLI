from diffsync_cli.clients.perfion.parsing import perfion_resp_to_dict

# TOOD: Should like be moved to it's own file eventually but for now this is fine
EXPECTED_PERFION_RESPONSE = {
         "id": "95537",
         "Value": "101001Antramel3XL",
         "Category": "T-shirts",
         "ItemNumber": "101001",
         "ItemName": "T-shirt 145 Gram",
         "TColor": "Anthracite Melange",
         "ERPColor": "Antramel",
         "TSizeNewDW": "3XL",
         "EANCode": "8718326154452",
         "TProductColor": "101001Antramel",
         "ItemSize": "1010013XL",
         "BrandName": "TRICORP CASUAL",
         "TColorCombination": "Uni color",
         "ERPGrossPrice1": "11.22",
         "ERPSalesCurrency1": "EUR",
         "TOldProductNumber": "T145",
         "Description": "Het T-shirt 145 Gram is een klassieker in de collectie van Tricorp. Het T-shirt\u00a0heeft een\u00a0doekgewicht van\u00a0145 gram. Dit Tricorp T-shirt bestaat voor 100% uit gekamd katoen en maakt onderdeel uit van het label Tricorp Casual. H\u00e9t werkshirt bij uitstek is leverbaar in een brede maatrange en in maar liefst 18 verschillende kleuren. Perfect voor elke professional dus!",
         "TWeight": "145",
         "TNettoWeight": "240",
         "LengthCM": "41",
         "WidthCM": "75",
         "HeightCM": "0.2",
         "KindofFabric": "Gebreid doek",
         "TMultiStandard": "Nee",
         "DWQuality": "60% katoen / 40% polyester",
         "DWMaterial": "Katoen",
         "TConstruction": "Single Jersey",
         "DWGender": "Unisex",
         "DWCollar": "Ronde hals",
         "DWSleeveLength": "Korte mouw",
         "DWOekoTex": "Oeko-Tex\u00ae",
         "DWFit": "Regular pasvorm",
         "DWFitAll": "Regular pasvorm",
         "DWLaundryWash01": "Maximum temperatuur 40\u00b0C, normaal centrifugeren",
         "DWLaundryBleach02": "Niet bleken",
         "DWLaundryDry03": "Niet drogen in droogtrommel",
         "DWLaundryIron04": "Strijken op maximaal 150 \u00b0C",
         "DWLaundryDryClean05": "Geen professionele droogreiniging",
         "BaseProductImageUrl": "https://artikelinfo.tricorp.com/productimages/UnicontaTemp/101001antramelside.png",
         "ProductImageUrlBack": "https://artikelinfo.tricorp.com/productimages/UnicontaTemp/101001antramelback.png",
         "ProductImageUrlFront": "https://artikelinfo.tricorp.com/productimages/UnicontaTemp/101001antramelfront.png",
         "ProductImageUrlLeft": "https://artikelinfo.tricorp.com/productimages/UnicontaTemp/101001antramelleft.png",
         "ProductImageUrlRight": "https://artikelinfo.tricorp.com/productimages/UnicontaTemp/101001antramelright.png",
         "ProductionCountry": "Pakistan",
         "CountryofOriginISO2": "PK",
         "ERPPackagingUnit": "10",
         "ERPPackagingQty": "50",
         "HSCode": "6109100010",
         "ItemOnWeb": "Yes",
         "OekotexLevel": "Article",
         "OekotexCertificate": "08.HBD.63845",
         "OekotexAnnex": "Annex 6, Class I",
         "ProductPageUrl": "https://www.tricorp.com/product/t-shirt-145-gram",
         "Url02": "https://artikelinfo.tricorp.com/DoC/10%20Casual/Tricorp_Productinformatie_101001.pdf"
     }

def _get_perfion_output(path: str):
     with open(path, "r") as f:
        raw_response = f.read()
        return perfion_resp_to_dict(raw_response)

def test_parse_perfion_response():

    result = _get_perfion_output("data/perfion/responses/perfion_output_single_product.xml")

    assert result.get("totalCount") != None
    assert isinstance(result.get("totalCount"), int)
    assert isinstance(result.get("products"), list)

def test_parse_perfion_product_attributes():

    result = _get_perfion_output("data/perfion/responses/perfion_output_single_product.xml")
    assert len(result.get("products", [])) == 1
    product = result["products"][0]
    assert product == EXPECTED_PERFION_RESPONSE
