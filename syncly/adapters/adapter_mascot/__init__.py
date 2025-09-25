class MascotAdapter(ThirdPartyAdapter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.image_mode = 'contain'

    def __str__(self):
        return "MascotAdapter"

    def _get_products(self) -> Union[List[ProductRow], Generator[ProductRow, Any, Any]]: # type: ignore | Product Row is a typed dict IG that's not of a type dict
        assert self.conn

        with self.conn as client:
            files = set(client.list_files())
            required = {self.settings.mascot.product_data, self.settings.mascot.availability}
            missing = required - files
            if missing:
                raise ValueError(f"Missing files: {sorted(missing)} (found: {sorted(files)})")

            product_data: List[List[Any]] = xlsx_bytes_to_list(
                client.download_file(self.settings.mascot.product_data),
                include_header=False
            )

            availablity_csv = client.download_file(
                self.settings.mascot.availability,
            )
            availability_data = _create_availablity_mapping(availablity_csv)

            product_rows = []
            for product in product_data:
                product_row: ProductRow = {}
                for i, field in enumerate(ProductRow.__annotations__):
                    if i < len(product):
                        product_row[field] = product[i]
                    else:
                        product_row[field] = None
                avail = availability_data.get(product_row.get('ean_number'), {})
                product_row["stock_status"] = avail.get("stock_status")
                product_row["reorder_status"] = avail.get("reorder_status")
                product_rows.append(product_row)

                yield product_row

        return product_rows

    def load_products(self):

        brand = self.settings.ccv_shop.brand

        for pd in self._get_products():
            if _is_stocked(pd) and not _is_excluded(pd, self.settings):
                name = _build_name(pd, brand)

                try:
                    product, _ = cast(Tuple[ThirdPartyProduct, bool], self.get_or_instantiate(
                        model=self.product,
                        ids= {
                            "productnumber": f"{pd.get('article_number')}"
                        },
                        attrs = {
                            "name": _build_name(pd, brand),
                            "package": "kartonnen doos",
                            "price": _get_price(pd),
                            "description": wrap_style(_build_description(pd)),
                            "category": [str(pd.get('product_type'))],
                            "brand": normalize_string(brand),

                            "page_title": f"{name} ",
                            "meta_description":  _build_meta_description(pd)

                        },
                    ))
                except ValidationError as err:
                    pretty_validation_error(err)
                    raise err

                append_if_not_exists(pd.get("color"), product.colors)
                append_if_not_exists(pd.get("eu_size_part1"), product.sizing)
                append_if_not_exists((pd.get("color"), pd.get("product_image_1000px")), product.images)

        return cast(List[ThirdPartyProduct], self.get_all(self.product))
