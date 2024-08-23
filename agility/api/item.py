import datetime
import frappe
from frappe import _


@frappe.whitelist(allow_guest=1)
def item_wise_assets(
    filters={},
    fields=["*"],
    limit_start=0,
    limit_page_length=100,
    order_by=None,
    group_by=None,
):
    # Adjust order
    item_order_by = order_by
    if order_by and "price_list_rate" in order_by:
        item_order_by = None

    # Fetch items
    items = frappe.db.get_list(
        "Item",
        filters=frappe.parse_json(filters),
        fields=frappe.parse_json(fields),
        limit_start=limit_start,
        limit_page_length=limit_page_length,
        order_by=item_order_by,
        group_by=group_by,
    )

    # print(items, "\n\n\n\n\n\n\nn\n\nn\n\n")

    # Fetch product images
    custom_assets_list = frappe.db.get_all(
        "Product Image - Child",
        filters={"parenttype": "Item"},
        fields=["*"],
        order_by="parent",
        limit=None,
    )

    # Group images
    grouped_asset_list = {}
    for item in custom_assets_list:
        parent = item["parent"]
        if parent not in grouped_asset_list:
            grouped_asset_list[parent] = []
        grouped_asset_list[parent].append(item)

    today = datetime.datetime.now().date()

    # Fetch item prices
    item_prices = frappe.db.get_all(
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

    # Group prices
    item_price_list = {}
    for price in item_prices:
        item_code = price["item_code"]
        if item_code not in item_price_list:
            item_price_list[item_code] = []
        item_price_list[item_code].append(price)


    attributes = frappe.get_all(
        "Variant Attribute",
        fields=["*"],
        filters={"parenttype": "Item"},
    )

    item_attribute_list = {}
    for attribute in attributes:
        parent = attribute["parent"]
        if parent not in item_attribute_list:
            item_attribute_list[parent] = []
        item_attribute_list[parent].append(attribute)

    def get_item_variants(item_name):
        item_variants = frappe.db.get_all(
            "Item",
            fields=["name", "variant_of"],
            filters={
                "variant_of": item_name,
                "has_variants": 0,
            },
        )

        attribute_groups = {}

        for variant in item_variants:
            # Fetch attributes for each variant
            attributes = frappe.get_all(
                "Item Variant Attribute",
                fields=["attribute", "attribute_value"],
                filters={"parent": variant["name"]},
            )

            for attr in attributes:
                attribute_name = attr["attribute"]
                attribute_value = attr["attribute_value"]

                if attribute_name not in attribute_groups:
                    attribute_groups[attribute_name] = {}

                if attribute_value not in attribute_groups[attribute_name]:
                    attribute_groups[attribute_name][attribute_value] = set()

                for other_attr in attributes:
                    if other_attr["attribute"] != attribute_name:
                        attribute_groups[attribute_name][attribute_value].add(
                            other_attr["attribute_value"]
                        )

        for attribute_name, value_group in attribute_groups.items():
            for attribute_value, related_values in value_group.items():
                attribute_groups[attribute_name][attribute_value] = list(related_values)

        return attribute_groups

    # # Attach data to items
    # for item in items:
    #     # item.variants = get_item_variants(item.name)
    #     item.custom_assets_list = grouped_asset_list.get(item.name, [])

    #     item.attributes = item_attribute_list.get(item.name, [])

    #     item.item_prices = item_price_list.get(item.name, [])
    #     item.price_list_rate = (
    #         item_price_list.get(item.name)[0].get("price_list_rate", 0)
    #         if item_price_list.get(item.name)
    #         else 0
    #     )

    unique_item_names = set()

    # Create a new list to hold unique items
    unique_items = []

    # Iterate through the items list
    for item in items:
        # Check if the item name is unique
        if item['name'] not in unique_item_names:
            # Add item name to the unique set
            unique_item_names.add(item['name'])
            
            # Append the unique item to the new list
            unique_items.append(item)

            # Populate item fields
            item['custom_assets_list'] = grouped_asset_list.get(item['name'], [])
            item['attributes'] = item_attribute_list.get(item['name'], [])
            item['item_prices'] = item_price_list.get(item['name'], [])
            item['price_list_rate'] = (
                item_price_list.get(item['name'])[0].get("price_list_rate", 0)
                if item_price_list.get(item['name'])
                else 0
            )


    if order_by == "price_list_rate asc":
        unique_items = sorted(unique_items, key=lambda x: x["price_list_rate"])
    elif order_by == "price_list_rate desc":
        unique_items = sorted(unique_items, key=lambda x: x["price_list_rate"], reverse=True)

    return unique_items


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


def template_wise_price_for_variants(doc, event):
    if doc.has_variants == 1:
        try:
            variants = frappe.get_list(
                "Item",
                filters={
                    "has_variants": 0,
                    "variant_of": doc.name,
                },
                fields=["name"],
            )

            for variant in variants:
                existing_price = frappe.get_all(
                    "Item Price",
                    filters={
                        "item_code": variant["name"],
                        "price_list": doc.custom_price_list,
                    },
                )

                if existing_price:
                    item_price = frappe.get_doc("Item Price", existing_price[0]["name"])
                    item_price.price_list_rate = doc.custom_rate
                    item_price.currency = doc.custom_currency
                    item_price.valid_from = doc.custom_valid_from
                    item_price.valid_upto = doc.custom_valid_upto
                else:
                    item_price = frappe.new_doc("Item Price")
                    item_price.item_code = variant["name"]
                    item_price.price_list = doc.custom_price_list
                    item_price.price_list_rate = doc.custom_rate
                    item_price.currency = doc.custom_currency
                    item_price.valid_from = doc.custom_valid_from
                    item_price.valid_upto = doc.custom_valid_upto

                item_price.save()

            frappe.db.commit()

        except Exception as e:
            frappe.db.rollback()


def set_price_for_new_variant(doc, event):
    if doc.has_variants == 0:
        try:
            item_template = frappe.get_list(
                "Item",
                filters={
                    "has_variants": 1,
                    "name": doc.variant_of,
                },
                fields=[
                    "name",
                    "custom_price_list",
                    "custom_rate",
                    "custom_currency",
                    "custom_valid_from",
                    "custom_valid_upto",
                ],
            )

            if item_template:
                item_template = item_template[0]

                # print(item_template)

                item_price = frappe.new_doc("Item Price")
                item_price.item_code = doc.name
                item_price.price_list = item_template["custom_price_list"]
                item_price.price_list_rate = item_template["custom_rate"]
                item_price.currency = item_template["custom_currency"]
                item_price.valid_from = item_template["custom_valid_from"]
                item_price.valid_upto = item_template["custom_valid_upto"]
                item_price.save()

                frappe.db.commit()
            else:
                print(f"No parent template found for item: {doc.variant_of}")

        except Exception as e:
            frappe.db.rollback()


@frappe.whitelist()
def add_variant_attribute_to_item_template(doc, event):
    if doc.has_variants != 1:
        item_name = doc.name
        item_template = doc.variant_of

        item = frappe.get_list(
            "Item",
            filters={
                "name": item_template,
                "has_variants": 1,
            },
            fields=["name"],
        )

        if item:
            item_attributes = frappe.get_all(
                "Item Variant Attribute",
                fields=["parent", "attribute", "attribute_value"],
                filters={"parent": item_name},
            )

            item_template = frappe.get_doc("Item", item_template)
            for attribute in item_attributes:
                item_template.append(
                    "custom_variant_attribute",
                    {
                        "attribute_type": attribute["attribute"],
                        "attribute_value": attribute["attribute_value"],
                        "item": doc.name,
                    },
                )

            item_template.save()

        frappe.db.commit()
