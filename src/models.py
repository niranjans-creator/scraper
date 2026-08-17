from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Variant:
    weight: str = ""
    actual_price: Optional[float] = None
    selling_price: Optional[float] = None

    def to_dict(self):
        return {
            "weight": self.weight,
            "actual_price": self.actual_price,
            "selling_price": self.selling_price,
        }


@dataclass
class Product:
    title: str = ""
    brand: str = ""
    description: str = ""

    actual_price: Optional[float] = None
    selling_price: Optional[float] = None

    ingredients: str = ""

    image_urls: List[str] = field(
        default_factory=list
    )

    variants: List[Variant] = field(
        default_factory=list
    )

    def to_dict(self):
        return {
            "title": self.title,
            "brand": self.brand,
            "description": self.description,
            "actual_price": self.actual_price,
            "selling_price": self.selling_price,
            "ingredients": self.ingredients,
            "image_urls": self.image_urls,
            "variants": [
                variant.to_dict()
                for variant in self.variants
            ],
        }