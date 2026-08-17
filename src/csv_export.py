import csv
from pathlib import Path

from src.models import Product


def export_to_csv(
    product,
    filename=None
):

    # =====================================================
    # OUTPUT LOCATION
    # =====================================================

    if filename is None:

        project_root = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        output_dir = (
            project_root /
            "scraped products"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = (
            output_dir /
            "bigbasket_products.csv"
        )

    else:

        filename = Path(
            filename
        )

        filename.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    # =====================================================
    # CSV COLUMNS
    # =====================================================

    fieldnames = [

        "title",

        "brand",

        "weight",

        "actual_price",

        "selling_price",

        "description",

        "ingredients",

        "image_urls"
    ]

    rows = []

    # =====================================================
    # VARIANTS
    # =====================================================

    if product.variants:

        for variant in product.variants:

            rows.append({

                "title":
                    product.title,

                "brand":
                    product.brand,

                "weight":
                    variant.weight,

                "actual_price":
                    variant.actual_price,

                "selling_price":
                    variant.selling_price,

                "description":
                    product.description,

                "ingredients":
                    product.ingredients,

                "image_urls":
                    " | ".join(
                        product.image_urls
                    )
            })

    # =====================================================
    # NO VARIANTS
    # =====================================================

    else:

        rows.append({

            "title":
                product.title,

            "brand":
                product.brand,

            "weight":
                "",

            "actual_price":
                product.actual_price,

            "selling_price":
                product.selling_price,

            "description":
                product.description,

            "ingredients":
                product.ingredients,

            "image_urls":
                " | ".join(
                    product.image_urls
                )
        })

    # =====================================================
    # WRITE CSV
    # =====================================================

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    print()
    print(
        f"# Saved to: {filename}"
    )

    return filename