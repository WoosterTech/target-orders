import abc
import datetime as dt
import re
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Self

from attrmagic import SimpleRoot
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel, HttpUrl

if TYPE_CHECKING:
    from bs4.element import PageElement
    from playwright.sync_api import ElementHandle


class ElementNotFoundError(Exception):
    """Custom exception for when an element is not found in the HTML."""

    pass


class TargetBaseModel(BaseModel, abc.ABC):
    @classmethod
    @abc.abstractmethod
    def parse_html(cls, inner_html: str | Tag) -> Self:
        """Parse HTML content into a model instance.

        Args:
            inner_html (str | Tag): The HTML content to parse.

        Returns:
            Self: An instance of the model.
        """
        pass


class OrderItem(TargetBaseModel):
    name: str
    image_url: HttpUrl

    @classmethod
    def parse_html(cls, inner_html: str | Tag) -> Self:
        if isinstance(inner_html, str):
            soup = BeautifulSoup(inner_html, "html.parser")
        else:
            soup = inner_html

        return cls(
            name=cls._parse_name(tag=soup), image_url=cls._parse_image_url(tag=soup)
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
    def parse_html(cls, inner_html: str | Tag) -> Self:
        if isinstance(inner_html, str):
            soup = BeautifulSoup(inner_html, "html.parser")
        else:
            soup = inner_html

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
    def _parse_order_date(soup: Tag) -> dt.date:
        date_element = soup.find("p", class_="h-text-bold")
        if date_element is None:
            raise ElementNotFoundError("Date element not found")
        date_str = date_element.text.strip()

        return dt.datetime.strptime(date_str, "%b %d, %Y")

    @staticmethod
    def _parse_order_total(soup: Tag) -> Decimal:
        total_element = soup.find("p", string=re.compile(r"^\$\d"))
        if total_element is None:
            raise ElementNotFoundError("Total element not found")
        total_str = total_element.text.strip()
        return Decimal(total_str.replace("$", "").replace(",", ""))

    @staticmethod
    def _parse_order_number(soup: Tag) -> str:
        order_number_element = soup.find("p", string=re.compile(r"^#\d+"))
        if order_number_element is None:
            raise ElementNotFoundError("Order number element not found")
        order_number_str = order_number_element.text.strip()
        return order_number_str.lstrip("#")

    @staticmethod
    def _parse_order_url(soup: Tag) -> str:
        order_url_element = soup.find("a", href=re.compile(r"^/orders/"))
        if order_url_element is None:
            raise ElementNotFoundError("Order URL element not found")
        assert isinstance(order_url_element, Tag), "order_url_element is not a Tag"
        return str(order_url_element["href"])

    @staticmethod
    def _parse_delivery_status(soup: Tag) -> str:
        delivery_status_element = soup.find("h2")
        if delivery_status_element is None:
            raise ElementNotFoundError("Delivery status element not found")
        delivery_status_str = delivery_status_element.text.strip()
        return delivery_status_str

    @staticmethod
    def _parse_items(soup: Tag) -> list[OrderItem]:
        items: list[OrderItem] = []
        item_elements = soup.find_all("img", alt=True, src=True)
        for item_element in item_elements:
            assert isinstance(item_element, Tag), "item_element is not a Tag"
            try:
                item = OrderItem.parse_html(item_element)
                items.append(item)
            except ElementNotFoundError as e:
                print(f"Error parsing item: {e}")
        return items


class Orders(SimpleRoot[Order]):
    @classmethod
    def parse_html(cls, inner_html: str | Tag):
        """Parse orders from HTML.

        Args:
            inner_html (str | Path): HTML string or path to HTML file.
        """
        if isinstance(inner_html, str):
            soup = BeautifulSoup(inner_html, "html.parser")
        else:
            soup = inner_html

        orders_div_list = soup.select("div[data-test='order-details-link']")
        elements: list[PageElement] = []
        for order_div in orders_div_list:
            elements.extend(order_div.contents)

        orders = [Order.parse_html(order_div) for order_div in orders_div_list]
        return cls(root=orders)

    @classmethod
    def parse_elements(cls, elements: "list[ElementHandle]") -> Self:
        orders = [Order.parse_html(element.inner_html()) for element in elements]
        return cls(root=orders)


def parse_orders_from_html(html: str | Path) -> Orders:
    """Parse orders from HTML.

    Args:
        html (str | Path): HTML string or path to HTML file.

    Returns:
        Orders: A list of orders.
    """
    if isinstance(html, Path):
        html = html.read_text(encoding="utf-8")

    return Orders.parse_html(html)
