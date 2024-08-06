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
    items = frappe.db.get_list(
        "Item",
        filters=frappe.parse_json(filters),
        fields=frappe.parse_json(fields),
        limit_start=limit_start,
        limit_page_length=limit_page_length,
        order_by=order_by,
        group_by=group_by,
    )

    custom_assets_list = frappe.db.get_all(
        "Product Image - Child",
        filters={"parenttype": "Item"},
        fields=["*"],
        order_by="parent",
        limit=None,
    )

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
        limit=None,
    )

    item_price_map = {}
    for price in item_price:
        item_code = price["item_code"]
        if item_code not in item_price_map:
            item_price_map[item_code] = []
        item_price_map[item_code].append(price)

    grouped_asset_list = {}
    for item in custom_assets_list:
        parent = item["parent"]
        if parent not in grouped_asset_list:
            grouped_asset_list[parent] = []
        grouped_asset_list[parent].append(item)

    for item in items:
        item.custom_assets_list = grouped_asset_list.get(item.name, [])
        item.item_prices = item_price_map.get(item.name, [])

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
