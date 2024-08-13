import datetime
import frappe
from frappe import _


@frappe.whitelist(allow_guest=1)
def item_wise_assets(
    filters={},
    fields=["*"],
    limit_start=0,
    limit_page_length=20,
    order_by=None,
    group_by=None,
):
    item_order_by = order_by

    if order_by and "price_list_rate" in order_by:
        item_order_by = None

    items = frappe.db.get_list(
        "Item",
        filters=frappe.parse_json(filters),
        fields=frappe.parse_json(fields),
        limit_start=limit_start,
        limit_page_length=limit_page_length,
        order_by=item_order_by,
        group_by=group_by,
    )

    custom_assets_list = frappe.db.get_all(
        "Product Image - Child",
        filters={"parenttype": "Item"},
        fields=["*"],
        order_by="parent",
        limit=None,
    )
    today = datetime.datetime.now().date()
    item_price = frappe.db.get_all(
        "Item Price",
        fields=[
            "item_code",
            "uom",
            "price_list",
            "price_list_rate",
            "valid_from",
            "valid_upto",
        ],
        filters={"valid_from": ["<=", today]},
        or_filters=[
            {"valid_upto": [">=", today]},
            {"valid_upto": ["is", "not set"]},
        ],
        limit=None,
    )

    item_price_list = {}
    for price in item_price:
        item_code = price["item_code"]
        if item_code not in item_price_list:
            item_price_list[item_code] = []
        item_price_list[item_code].append(price)

    grouped_asset_list = {}
    for item in custom_assets_list:
        parent = item["parent"]
        if parent not in grouped_asset_list:
            grouped_asset_list[parent] = []
        grouped_asset_list[parent].append(item)

    for item in items:
        item.custom_assets_list = grouped_asset_list.get(item.name, [])
        item.item_prices = item_price_list.get(item.name, [])
        item.price_list_rate = (
            item_price_list.get(item.name)[0].get("price_list_rate", 0)
            if item_price_list.get(item.name)
            else 0
        )

    if order_by == "price_list_rate asc":
        items = sorted(items, key=lambda x: x["price_list_rate"])
    elif order_by == "price_list_rate desc":
        items = sorted(items, key=lambda x: x["price_list_rate"], reverse=True)

    return items


@frappe.whitelist()
def get_color_code(item_attribute, template_code):
    data = frappe.db.sql(
        " select attribute_value from `tabItem Variant Attribute` where variant_of=%s and attribute=%s ",
        (template_code, item_attribute),
        as_dict=True,
    )

    # Use a set to remove duplicates
    unique_attribute_values = list({v["attribute_value"] for v in data})

    # Convert back to list of dictionaries if necessary
    unique_attribute_values = [{"attribute_value": v} for v in unique_attribute_values]

    return unique_attribute_values
