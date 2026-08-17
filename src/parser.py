import json
import re

from bs4 import BeautifulSoup

from src.models import Product, Variant


class BigBasketParser:

    # =====================================================
    # MAIN PARSER
    # =====================================================

    def parse(self, html):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        product = Product()

        # -------------------------------------------------
        # Page text
        # -------------------------------------------------

        page_text = soup.get_text(
            " ",
            strip=True
        )

        # -------------------------------------------------
        # JSON / Next.js data
        # -------------------------------------------------

        json_data = self.extract_json_data(
            soup
        )

        # -------------------------------------------------
        # Basic product information
        # -------------------------------------------------

        product.title = self.extract_title(
            soup,
            json_data
        )

        product.brand = self.extract_brand(
            soup,
            json_data
        )

        product.description = self.extract_description(
            soup,
            json_data
        )

        # -------------------------------------------------
        # Main price
        # -------------------------------------------------

        (
            product.actual_price,
            product.selling_price
        ) = self.extract_prices(
            soup,
            json_data,
            page_text
        )

        # -------------------------------------------------
        # Ingredients
        # -------------------------------------------------

        product.ingredients = self.extract_ingredients(
            soup,
            json_data,
            page_text
        )

        # -------------------------------------------------
        # Images
        # -------------------------------------------------

        product.image_urls = self.extract_images(
            soup,
            json_data
        )

        # -------------------------------------------------
        # Variants
        # -------------------------------------------------

        product.variants = self.extract_variants(
            soup,
            json_data,
            page_text
        )

        # -------------------------------------------------
        # If variants don't contain the main product,
        # add the main product as a variant.
        # -------------------------------------------------

        main_weight = self.extract_weight(
            product.title
        )

        if (
            main_weight
            and product.selling_price is not None
        ):

            exists = False

            for variant in product.variants:

                if self.normalise_weight(
                    variant.weight
                ) == self.normalise_weight(
                    main_weight
                ):

                    exists = True
                    break

            if not exists:

                product.variants.insert(
                    0,
                    Variant(
                        weight=main_weight,
                        actual_price=product.actual_price,
                        selling_price=product.selling_price
                    )
                )

        return product

    # =====================================================
    # JSON DATA
    # =====================================================

    def extract_json_data(self, soup):

        data = []

        for script in soup.find_all(
            "script"
        ):

            script_text = script.string

            if not script_text:

                script_text = script.get_text()

            if not script_text:

                continue

            script_text = script_text.strip()

            if not script_text:

                continue

            script_type = (
                script.get("type") or ""
            ).lower()

            # -------------------------------------------------
            # JSON-LD
            # -------------------------------------------------

            if "ld+json" in script_type:

                try:

                    parsed = json.loads(
                        script_text
                    )

                    if isinstance(
                        parsed,
                        list
                    ):

                        data.extend(
                            parsed
                        )

                    else:

                        data.append(
                            parsed
                        )

                except Exception:
                    pass

            # -------------------------------------------------
            # Next.js
            # -------------------------------------------------

            elif (
                script.get("id")
                == "__NEXT_DATA__"
            ):

                try:

                    parsed = json.loads(
                        script_text
                    )

                    data.append(
                        parsed
                    )

                except Exception:
                    pass

            # -------------------------------------------------
            # Other JSON-looking scripts
            # -------------------------------------------------

            elif (
                script_text.startswith("{")
                or script_text.startswith("[")
            ):

                try:

                    parsed = json.loads(
                        script_text
                    )

                    data.append(
                        parsed
                    )

                except Exception:
                    pass

        return data

    # =====================================================
    # FIND JSON VALUE
    # =====================================================

    def find_json_value(
        self,
        data,
        keys
    ):

        if isinstance(
            keys,
            str
        ):

            keys = [
                keys
            ]

        if isinstance(
            data,
            dict
        ):

            # Exact keys first
            for key in keys:

                if key in data:

                    value = data[key]

                    if value not in (
                        None,
                        "",
                        [],
                        {}
                    ):

                        return value

            # Recursive search
            for value in data.values():

                result = self.find_json_value(
                    value,
                    keys
                )

                if result not in (
                    None,
                    "",
                    [],
                    {}
                ):

                    return result

        elif isinstance(
            data,
            list
        ):

            for item in data:

                result = self.find_json_value(
                    item,
                    keys
                )

                if result not in (
                    None,
                    "",
                    [],
                    {}
                ):

                    return result

        return None

    # =====================================================
    # TITLE
    # =====================================================

    def extract_title(
        self,
        soup,
        json_data
    ):

        value = self.find_json_value(
            json_data,
            [
                "name",
                "productName",
                "product_name",
                "title"
            ]
        )

        if isinstance(
            value,
            str
        ):

            value = self.clean_text(
                value
            )

            if len(value) > 2:

                return value

        meta = soup.find(
            "meta",
            attrs={
                "property": "og:title"
            }
        )

        if meta:

            value = meta.get(
                "content"
            )

            if value:

                return self.clean_text(
                    value
                )

        h1 = soup.find(
            "h1"
        )

        if h1:

            value = self.clean_text(
                h1.get_text(
                    " ",
                    strip=True
                )
            )

            if value:

                return value

        title = soup.find(
            "title"
        )

        if title:

            value = self.clean_text(
                title.get_text(
                    " ",
                    strip=True
                )
            )

            if value:

                return value

        return ""

    # =====================================================
    # BRAND
    # =====================================================

    def extract_brand(
        self,
        soup,
        json_data
    ):

        value = self.find_json_value(
            json_data,
            [
                "brand"
            ]
        )

        if isinstance(
            value,
            dict
        ):

            value = (
                value.get("name")
                or value.get("label")
            )

        if isinstance(
            value,
            str
        ):

            value = self.clean_text(
                value
            )

            if value:

                return value

        text = soup.get_text(
            " ",
            strip=True
        )

        patterns = [

            r"\bBrand\s*:\s*([^|]+)",

            r"\bBrand\s+([A-Za-z0-9&!.' -]{2,80})"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                value = self.clean_text(
                    match.group(1)
                )

                if value:

                    return value

        return ""

    # =====================================================
    # DESCRIPTION
    # =====================================================

    def extract_description(
        self,
        soup,
        json_data
    ):

        value = self.find_json_value(
            json_data,
            [
                "description",
                "productDescription",
                "product_description"
            ]
        )

        if isinstance(
            value,
            str
        ):

            value = self.clean_text(
                value
            )

            if len(value) > 20:

                return value

        meta = soup.find(
            "meta",
            attrs={
                "name": "description"
            }
        )

        if meta:

            value = meta.get(
                "content"
            )

            if value:

                value = self.clean_text(
                    value
                )

                if len(value) > 20:

                    return value

        headings = soup.find_all(
            [
                "h2",
                "h3",
                "h4",
                "strong"
            ]
        )

        for heading in headings:

            heading_text = self.clean_text(
                heading.get_text(
                    " ",
                    strip=True
                )
            ).lower()

            if heading_text in (
                "description",
                "product description",
                "about the product"
            ):

                parent = heading.parent

                if parent:

                    value = self.clean_text(
                        parent.get_text(
                            " ",
                            strip=True
                        )
                    )

                    value = re.sub(
                        r"^description\s*:?\s*",
                        "",
                        value,
                        flags=re.IGNORECASE
                    )

                    if len(value) > 20:

                        return value

        return ""

    # =====================================================
    # MAIN PRICES
    # =====================================================

    def extract_prices(
        self,
        soup,
        json_data,
        page_text
    ):

        actual_price = self.find_price_value(
            json_data,
            [
                "mrp",
                "MRP",
                "maximumRetailPrice",
                "maximum_retail_price",
                "originalPrice",
                "original_price",
                "listPrice",
                "list_price"
            ]
        )

        selling_price = self.find_price_value(
            json_data,
            [
                "sellingPrice",
                "selling_price",
                "salePrice",
                "sale_price",
                "offerPrice",
                "offer_price",
                "discountedPrice",
                "discounted_price",
                "price"
            ]
        )

        # -------------------------------------------------
        # Visible MRP
        # -------------------------------------------------

        if actual_price is None:

            patterns = [

                r"(?:MRP|Maximum\s+Retail\s+Price)"
                r"\s*[:\-]?\s*"
                r"(?:Rs\.?|₹)?\s*"
                r"([\d,]+(?:\.\d+)?)"
            ]

            for pattern in patterns:

                match = re.search(
                    pattern,
                    page_text,
                    re.IGNORECASE
                )

                if match:

                    actual_price = self.to_float(
                        match.group(1)
                    )

                    break

        # -------------------------------------------------
        # Visible selling price
        # -------------------------------------------------

        if selling_price is None:

            patterns = [

                r"(?:Selling\s+Price|Sale\s+Price|Offer\s+Price)"
                r"\s*[:\-]?\s*"
                r"(?:Rs\.?|₹)?\s*"
                r"([\d,]+(?:\.\d+)?)",

                r"(?:Now\s+available\s+at|Now\s+available)"
                r"\s*(?:for|at)?\s*"
                r"(?:Rs\.?|₹)?\s*"
                r"([\d,]+(?:\.\d+)?)"
            ]

            for pattern in patterns:

                match = re.search(
                    pattern,
                    page_text,
                    re.IGNORECASE
                )

                if match:

                    selling_price = self.to_float(
                        match.group(1)
                    )

                    break

        # -------------------------------------------------
        # Generic prices
        # -------------------------------------------------

        prices = re.findall(
            r"(?:₹|Rs\.?)\s*"
            r"([\d,]+(?:\.\d+)?)",
            page_text,
            flags=re.IGNORECASE
        )

        numeric_prices = []

        for value in prices:

            price = self.to_float(
                value
            )

            if price is not None:

                numeric_prices.append(
                    price
                )

        if selling_price is None:

            if numeric_prices:

                selling_price = numeric_prices[0]

        if actual_price is None:

            if len(numeric_prices) >= 2:

                actual_price = max(
                    numeric_prices
                )

        if (
            actual_price is not None
            and selling_price is not None
            and actual_price < selling_price
        ):

            actual_price, selling_price = (
                selling_price,
                actual_price
            )

        return (
            actual_price,
            selling_price
        )

    # =====================================================
    # FIND PRICE IN JSON
    # =====================================================

    def find_price_value(
        self,
        data,
        keys
    ):

        value = self.find_json_value(
            data,
            keys
        )

        if isinstance(
            value,
            dict
        ):

            value = (
                value.get("value")
                or value.get("amount")
                or value.get("price")
            )

        return self.to_float(
            value
        )

    # =====================================================
    # VARIANT EXTRACTION
    # =====================================================

    def extract_variants(
        self,
        soup,
        json_data,
        page_text
    ):

        variants = []

        # -------------------------------------------------
        # 1. Search JSON recursively
        # -------------------------------------------------

        self.collect_variants_from_json(
            json_data,
            variants
        )

        # -------------------------------------------------
        # 2. Search HTML text for weight + price
        # -------------------------------------------------

        self.collect_variants_from_text(
            page_text,
            variants
        )

        # -------------------------------------------------
        # 3. Search HTML elements
        # -------------------------------------------------

        self.collect_variants_from_html(
            soup,
            variants
        )

        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------

        unique = []

        seen = set()

        for variant in variants:

            if not variant.weight:

                continue

            key = (
                self.normalise_weight(
                    variant.weight
                ),
                variant.actual_price,
                variant.selling_price
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            unique.append(
                variant
            )

        return unique

    # =====================================================
    # COLLECT VARIANTS FROM JSON
    # =====================================================

    def collect_variants_from_json(
        self,
        data,
        variants
    ):

        if isinstance(
            data,
            dict
        ):

            # -------------------------------------------------
            # First inspect this object
            # -------------------------------------------------

            weight = self.find_direct_weight(
                data
            )

            actual_price = self.find_direct_price(
                data,
                [
                    "mrp",
                    "MRP",
                    "maximumRetailPrice",
                    "maximum_retail_price",
                    "originalPrice",
                    "original_price",
                    "listPrice",
                    "list_price"
                ]
            )

            selling_price = self.find_direct_price(
                data,
                [
                    "sellingPrice",
                    "selling_price",
                    "salePrice",
                    "sale_price",
                    "offerPrice",
                    "offer_price",
                    "discountedPrice",
                    "discounted_price",
                    "price"
                ]
            )

            # -------------------------------------------------
            # Sometimes price itself is nested
            # -------------------------------------------------

            if (
                weight
                and (
                    actual_price is not None
                    or selling_price is not None
                )
            ):

                variants.append(
                    Variant(
                        weight=weight,
                        actual_price=actual_price,
                        selling_price=selling_price
                    )
                )

            # -------------------------------------------------
            # Search children
            # -------------------------------------------------

            for value in data.values():

                self.collect_variants_from_json(
                    value,
                    variants
                )

        elif isinstance(
            data,
            list
        ):

            for item in data:

                self.collect_variants_from_json(
                    item,
                    variants
                )

    # =====================================================
    # FIND DIRECT WEIGHT
    # =====================================================

    def find_direct_weight(
        self,
        data
    ):

        weight_keys = [

            "weight",
            "size",
            "packSize",
            "pack_size",
            "quantity",
            "unit",
            "displayName",
            "display_name",
            "variantName",
            "variant_name"
        ]

        for key in weight_keys:

            if key not in data:

                continue

            value = data[key]

            if isinstance(
                value,
                dict
            ):

                value = (
                    value.get("name")
                    or value.get("label")
                    or value.get("value")
                )

            if not isinstance(
                value,
                str
            ):

                continue

            value = self.clean_text(
                value
            )

            if self.looks_like_weight(
                value
            ):

                return value

        # -------------------------------------------------
        # Search common nested variant fields
        # -------------------------------------------------

        for key in (
            "variant",
            "productVariant",
            "product_variant",
            "item",
            "sku"
        ):

            value = data.get(
                key
            )

            if isinstance(
                value,
                dict
            ):

                nested = self.find_direct_weight(
                    value
                )

                if nested:

                    return nested

        return ""

    # =====================================================
    # FIND DIRECT PRICE
    # =====================================================

    def find_direct_price(
        self,
        data,
        keys
    ):

        for key in keys:

            if key not in data:

                continue

            value = data[key]

            if isinstance(
                value,
                dict
            ):

                value = (
                    value.get("value")
                    or value.get("amount")
                    or value.get("price")
                )

            price = self.to_float(
                value
            )

            if price is not None:

                return price

        return None

    # =====================================================
    # COLLECT VARIANTS FROM TEXT
    # =====================================================

    def collect_variants_from_text(
        self,
        page_text,
        variants
    ):

        # -------------------------------------------------
        # Matches things such as:
        #
        # 500 g ₹35
        # 1 kg ₹54.50
        # 250 g Rs. 20
        # -------------------------------------------------

        pattern = re.compile(
            r"("
            r"\d+(?:\.\d+)?"
            r"\s*"
            r"(?:kg|kgs|g|gm|gms|gram|grams|"
            r"ml|l|ltr|litre|litres|"
            r"pcs|pc|piece|pieces)"
            r")"
            r"\s*"
            r"(?:₹|Rs\.?)"
            r"\s*"
            r"([\d,]+(?:\.\d+)?)",
            re.IGNORECASE
        )

        matches = pattern.findall(
            page_text
        )

        for weight, price in matches:

            selling_price = self.to_float(
                price
            )

            if selling_price is None:

                continue

            variants.append(
                Variant(
                    weight=self.clean_text(
                        weight
                    ),
                    selling_price=selling_price
                )
            )

    # =====================================================
    # COLLECT VARIANTS FROM HTML
    # =====================================================

    def collect_variants_from_html(
        self,
        soup,
        variants
    ):

        # -------------------------------------------------
        # Look at buttons, labels and selectable elements.
        # -------------------------------------------------

        elements = soup.find_all(
            [
                "button",
                "label",
                "li",
                "span",
                "div"
            ]
        )

        for element in elements:

            text = self.clean_text(
                element.get_text(
                    " ",
                    strip=True
                )
            )

            if not text:

                continue

            if len(text) > 80:

                continue

            if not self.looks_like_weight(
                text
            ):

                continue

            # Look for price in this element
            # or nearby parent.

            price_text = text

            parent = element.parent

            if parent:

                parent_text = self.clean_text(
                    parent.get_text(
                        " ",
                        strip=True
                    )
                )

                if len(parent_text) <= 200:

                    price_text += " " + parent_text

            price_match = re.search(
                r"(?:₹|Rs\.?)\s*"
                r"([\d,]+(?:\.\d+)?)",
                price_text,
                re.IGNORECASE
            )

            if not price_match:

                continue

            price = self.to_float(
                price_match.group(1)
            )

            if price is None:

                continue

            variants.append(
                Variant(
                    weight=text,
                    selling_price=price
                )
            )

    # =====================================================
    # CHECK WEIGHT
    # =====================================================

    @staticmethod
    def looks_like_weight(
        value
    ):

        if not value:

            return False

        return bool(
            re.search(
                r"\b\d+(?:\.\d+)?\s*"
                r"(?:kg|kgs|g|gm|gms|gram|grams|"
                r"ml|l|ltr|litre|litres|"
                r"pcs|pc|piece|pieces)\b",
                value,
                re.IGNORECASE
            )
        )

    # =====================================================
    # EXTRACT WEIGHT FROM TITLE
    # =====================================================

    def extract_weight(
        self,
        title
    ):

        if not title:

            return ""

        match = re.search(
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:kg|kgs|g|gm|gms|gram|grams|"
            r"ml|l|ltr|litre|litres|"
            r"pcs|pc|piece|pieces)\b",
            title,
            re.IGNORECASE
        )

        if match:

            return self.clean_text(
                match.group(0)
            )

        return ""

    # =====================================================
    # NORMALISE WEIGHT
    # =====================================================

    @staticmethod
    def normalise_weight(
        value
    ):

        if not value:

            return ""

        value = value.lower()

        value = re.sub(
            r"\s+",
            "",
            value
        )

        value = value.replace(
            "kgs",
            "kg"
        )

        value = value.replace(
            "gms",
            "g"
        )

        value = value.replace(
            "gm",
            "g"
        )

        value = value.replace(
            "grams",
            "g"
        )

        value = value.replace(
            "gram",
            "g"
        )

        value = value.replace(
            "litres",
            "l"
        )

        value = value.replace(
            "litre",
            "l"
        )

        value = value.replace(
            "ltr",
            "l"
        )

        value = value.replace(
            "ml",
            "ml"
        )

        return value

    # =====================================================
    # INGREDIENTS
    # =====================================================

    def extract_ingredients(
        self,
        soup,
        json_data,
        page_text
    ):

        value = self.find_json_value(
            json_data,
            [
                "ingredients",
                "ingredient",
                "Ingredients"
            ]
        )

        if isinstance(
            value,
            list
        ):

            value = ", ".join(
                str(item)
                for item in value
            )

        if isinstance(
            value,
            str
        ):

            value = self.clean_text(
                value
            )

            if value:

                return value

        patterns = [

            r"Ingredients\s*[:\-]\s*"
            r"(.*?)(?=\s+"
            r"(?:Nutritional|Nutrition|"
            r"Product Information|Other Product Info|"
            r"Disclaimer|Storage|Shelf Life|"
            r"Country of Origin|$))",

            r"Ingredients\s+"
            r"(.*?)(?=\s+"
            r"(?:Nutritional|Nutrition|"
            r"Product Information|Other Product Info|"
            r"Disclaimer|Storage|Shelf Life|"
            r"Country of Origin|$))"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                page_text,
                re.IGNORECASE | re.DOTALL
            )

            if match:

                value = self.clean_text(
                    match.group(1)
                )

                if value:

                    return value

        headings = soup.find_all(
            [
                "h2",
                "h3",
                "h4",
                "strong"
            ]
        )

        for heading in headings:

            heading_text = self.clean_text(
                heading.get_text(
                    " ",
                    strip=True
                )
            ).lower()

            if "ingredient" not in heading_text:

                continue

            parent = heading.parent

            if parent:

                value = self.clean_text(
                    parent.get_text(
                        " ",
                        strip=True
                    )
                )

                value = re.sub(
                    r"^Ingredients\s*[:\-]?\s*",
                    "",
                    value,
                    flags=re.IGNORECASE
                )

                if value:

                    return value

        return ""

    # =====================================================
    # IMAGES
    # =====================================================

    def extract_images(
        self,
        soup,
        json_data
    ):

        images = []

        # -------------------------------------------------
        # JSON images
        # -------------------------------------------------

        self.collect_images_from_json(
            json_data,
            images
        )

        # -------------------------------------------------
        # HTML images
        # -------------------------------------------------

        for img in soup.find_all(
            "img"
        ):

            attributes = [

                "src",
                "data-src",
                "data-original",
                "data-lazy-src",
                "data-image",
                "data-image-url",
                "data-original-src"
            ]

            for attribute in attributes:

                value = img.get(
                    attribute
                )

                if value:

                    self.add_image(
                        value,
                        images
                    )

            # -------------------------------------------------
            # srcset
            # -------------------------------------------------

            srcset = img.get(
                "srcset"
            )

            if srcset:

                for item in srcset.split(","):

                    url = item.strip().split(
                        " "
                    )[0]

                    self.add_image(
                        url,
                        images
                    )

            # -------------------------------------------------
            # lazy-loaded source tags
            # -------------------------------------------------

            parent = img.parent

            if parent:

                source = parent.find(
                    "source"
                )

                if source:

                    for attribute in (
                        "src",
                        "srcset",
                        "data-srcset"
                    ):

                        value = source.get(
                            attribute
                        )

                        if not value:

                            continue

                        if "srcset" in attribute:

                            for item in value.split(","):

                                url = item.strip().split(
                                    " "
                                )[0]

                                self.add_image(
                                    url,
                                    images
                                )

                        else:

                            self.add_image(
                                value,
                                images
                            )

        # -------------------------------------------------
        # Deduplicate
        # -------------------------------------------------

        result = []

        seen = set()

        for url in images:

            clean_url = re.sub(
                r"\?.*$",
                "",
                url
            )

            if clean_url in seen:

                continue

            seen.add(
                clean_url
            )

            result.append(
                url
            )

        return result

    # =====================================================
    # COLLECT JSON IMAGES
    # =====================================================

    def collect_images_from_json(
        self,
        data,
        images
    ):

        if isinstance(
            data,
            dict
        ):

            for key, value in data.items():

                key_lower = str(
                    key
                ).lower()

                if key_lower in (
                    "image",
                    "images",
                    "imageurl",
                    "image_url",
                    "imageurls",
                    "image_urls",
                    "imagepath",
                    "image_path",
                    "thumbnail",
                    "thumbnailurl",
                    "thumbnail_url"
                ):

                    self.add_json_image(
                        value,
                        images
                    )

                else:

                    self.collect_images_from_json(
                        value,
                        images
                    )

        elif isinstance(
            data,
            list
        ):

            for item in data:

                self.collect_images_from_json(
                    item,
                    images
                )

    # =====================================================
    # ADD JSON IMAGE
    # =====================================================

    def add_json_image(
        self,
        value,
        images
    ):

        if isinstance(
            value,
            str
        ):

            self.add_image(
                value,
                images
            )

        elif isinstance(
            value,
            list
        ):

            for item in value:

                self.add_json_image(
                    item,
                    images
                )

        elif isinstance(
            value,
            dict
        ):

            for key in (
                "url",
                "src",
                "image",
                "imageUrl",
                "image_url"
            ):

                if key in value:

                    self.add_json_image(
                        value[key],
                        images
                    )

    # =====================================================
    # ADD IMAGE
    # =====================================================

    def add_image(
        self,
        url,
        images
    ):

        if not url:

            return

        url = str(
            url
        ).strip()

        if url.startswith(
            "//"
        ):

            url = "https:" + url

        if not url.startswith(
            "http://"
        ) and not url.startswith(
            "https://"
        ):

            return

        if self.is_valid_product_image(
            url
        ):

            images.append(
                url
            )

    # =====================================================
    # IMAGE VALIDATION
    # =====================================================

    @staticmethod
    def is_valid_product_image(
        url
    ):

        lower = url.lower()

        if (
            "bbassets.com" not in lower
            and "bigbasket.com" not in lower
        ):

            return False

        # Avoid obvious banners
        if (
            "banner_images" in lower
            or "/banner/" in lower
            or "banner" in lower
        ):

            return False

        # Avoid tiny UI icons
        if (
            "logo" in lower
            or "icon" in lower
            or "sprite" in lower
        ):

            return False

        return True

    # =====================================================
    # CLEAN TEXT
    # =====================================================

    @staticmethod
    def clean_text(
        value
    ):

        if value is None:

            return ""

        value = str(
            value
        )

        value = value.replace(
            "\xa0",
            " "
        )

        value = re.sub(
            r"\s+",
            " ",
            value
        )

        return value.strip()

    # =====================================================
    # FLOAT
    # =====================================================

    @staticmethod
    def to_float(
        value
    ):

        if value is None:

            return None

        try:

            if isinstance(
                value,
                (int, float)
            ):

                return float(
                    value
                )

            value = str(
                value
            )

            value = value.replace(
                ",",
                ""
            )

            match = re.search(
                r"\d+(?:\.\d+)?",
                value
            )

            if not match:

                return None

            return float(
                match.group(0)
            )

        except Exception:

            return None