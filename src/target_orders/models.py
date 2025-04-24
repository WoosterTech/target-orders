import datetime as dt
import re
from decimal import Decimal
from typing import TYPE_CHECKING, Self

from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, HttpUrl

from target_orders.utilities.bases import SimpleListRoot

if TYPE_CHECKING:
    from playwright.sync_api import ElementHandle


class ElementNotFoundError(Exception):
    """Custom exception for when an element is not found in the HTML."""

    pass


class TargetBaseModel(BaseModel):
    pass


class OrderItem(TargetBaseModel):
    name: str
    image_url: HttpUrl

    @classmethod
    def parse_tag(cls, tag: Tag) -> Self:
        name = cls._parse_name(tag=tag)
        image_url = cls._parse_image_url(tag=tag)

        return cls(
            name=name,
            image_url=image_url,
        )

    @staticmethod
    def _parse_name(tag: Tag) -> str:
        return str(tag["alt"]) if tag.has_attr("alt") else ""

    @staticmethod
    def _parse_image_url(tag: Tag) -> HttpUrl:
        assert hasattr(tag, "src"), "Tag does not have 'src' attribute"
        return HttpUrl(str(tag["src"]))


class Order(TargetBaseModel):
    order_date: dt.date
    order_total: Decimal
    order_number: str
    order_url: str
    delivery_status: str
    items: list[OrderItem]

    @classmethod
    def parse_html(cls, inner_html: str) -> Self:
        soup = BeautifulSoup(inner_html, "html.parser")

        order_date = cls._parse_order_date(soup=soup)
        order_total = cls._parse_order_total(soup=soup)
        order_number = cls._parse_order_number(soup=soup)
        order_url = cls._parse_order_url(soup=soup)
        delivery_status = cls._parse_delivery_status(soup=soup)
        items = cls._parse_items(soup=soup)

        return cls(
            order_date=order_date,
            order_total=order_total,
            order_number=order_number,
            order_url=order_url,
            delivery_status=delivery_status,
            items=items,
        )

    @staticmethod
    def _parse_order_date(soup: BeautifulSoup) -> dt.date:
        date_element = soup.find("p", class_="h-text-bold")
        if date_element is None:
            raise ElementNotFoundError("Date element not found")
        date_str = date_element.text.strip()

        return dt.datetime.strptime(date_str, "%b %d, %Y")

    @staticmethod
    def _parse_order_total(soup: BeautifulSoup) -> Decimal:
        total_element = soup.find("p", string=re.compile(r"^\$\d"))
        if total_element is None:
            raise ElementNotFoundError("Total element not found")
        total_str = total_element.text.strip()
        return Decimal(total_str.replace("$", "").replace(",", ""))

    @staticmethod
    def _parse_order_number(soup: BeautifulSoup) -> str:
        order_number_element = soup.find("p", string=re.compile(r"^#\d+"))
        if order_number_element is None:
            raise ElementNotFoundError("Order number element not found")
        order_number_str = order_number_element.text.strip()
        return order_number_str.lstrip("#")

    @staticmethod
    def _parse_order_url(soup: BeautifulSoup) -> str:
        order_url_element = soup.find("a", href=re.compile(r"^/orders/"))
        if order_url_element is None:
            raise ElementNotFoundError("Order URL element not found")
        assert isinstance(order_url_element, Tag), "order_url_element is not a Tag"
        return str(order_url_element["href"])

    @staticmethod
    def _parse_delivery_status(soup: BeautifulSoup) -> str:
        delivery_status_element = soup.find("h2")
        if delivery_status_element is None:
            raise ElementNotFoundError("Delivery status element not found")
        delivery_status_str = delivery_status_element.text.strip()
        return delivery_status_str

    @staticmethod
    def _parse_items(soup: BeautifulSoup) -> list[OrderItem]:
        items = []
        item_elements = soup.find_all("img", alt=True, src=True)
        for item_element in item_elements:
            assert isinstance(item_element, Tag), "item_element is not a Tag"
            try:
                item = OrderItem.parse_tag(item_element)
                items.append(item)
            except ElementNotFoundError as e:
                print(f"Error parsing item: {e}")
        return items


class Orders(SimpleListRoot[Order]):
    @classmethod
    def parse_elements(cls, elements: "list[ElementHandle]") -> Self:
        orders = [Order.parse_html(element.inner_html()) for element in elements]
        return cls(root=orders)
