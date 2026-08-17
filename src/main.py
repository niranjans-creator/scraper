from src.scraper import BigBasketScraper
from src.csv_export import export_to_csv


def main():

    # =====================================================
    # INPUT
    # =====================================================

    url = input(
        "Enter BigBasket product URL: "
    ).strip()

    if not url:

        print(
            "No URL entered."
        )

        return

    try:

        print()
        print(
            "Starting BigBasket scraper..."
        )
        print()

        # =================================================
        # SCRAPER
        # =================================================

        scraper = BigBasketScraper(
            headless=False
        )

        product = scraper.scrape_product(
            url
        )

        # =================================================
        # PRODUCT
        # =================================================

        print()
        print(
            "=" * 60
        )

        print(
            "PRODUCT"
        )

        print(
            "=" * 60
        )

        print(
            f"Title: {product.title}"
        )

        print(
            f"Brand: {product.brand}"
        )

        print(
            f"Main Actual Price: "
            f"{product.actual_price}"
        )

        print(
            f"Main Selling Price: "
            f"{product.selling_price}"
        )

        # =================================================
        # VARIANTS
        # =================================================

        print()
        print(
            "VARIANTS"
        )

        print(
            "-" * 60
        )

        if product.variants:

            for index, variant in enumerate(
                product.variants,
                start=1
            ):

                print(
                    f"Variant {index}"
                )

                print(
                    f"Weight: "
                    f"{variant.weight}"
                )

                print(
                    f"Actual Price: "
                    f"{variant.actual_price}"
                )

                print(
                    f"Selling Price: "
                    f"{variant.selling_price}"
                )

                print(
                    "-" * 40
                )

        else:

            print(
                "No variants found."
            )

        # =================================================
        # DESCRIPTION
        # =================================================

        print()
        print(
            "Description:"
        )

        print(
            product.description
        )

        # =================================================
        # INGREDIENTS
        # =================================================

        print()
        print(
            "Ingredients:"
        )

        print(
            product.ingredients
        )

        # =================================================
        # IMAGES
        # =================================================

        print()
        print(
            "IMAGE URLS"
        )

        print(
            "-" * 60
        )

        if product.image_urls:

            for image in product.image_urls:

                print(
                    image
                )

        else:

            print(
                "No product images found."
            )

        # =================================================
        # CSV
        # =================================================

        export_to_csv(
            product
        )

        print()
        print(
            "=" * 60
        )

    except Exception as e:

        print()
        print(
            "ERROR:"
        )

        print(
            e
        )


if __name__ == "__main__":

    main()