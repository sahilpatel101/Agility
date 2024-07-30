import frappe
from frappe import _



@frappe.whitelist()
def item_wise_assets():
    items = frappe.db.get_list(
        "Item",
        filters={},
        fields=["*"],
        # order_by="name",
        limit=None,
    )

    #! GET CHILD DOCTYPE LIST
    custom_assets_list = frappe.db.get_all(
        "Product Images - Child",
        filters={"parenttype": "Item"},
        fields=["*"],
        order_by="parent",
        limit=None,
    )

    #! GROUP THEM BASED ON FIELD "PARENT"
    grouped_asset_list = {}
    for item in custom_assets_list:
        parent = item["parent"]
        if parent not in grouped_asset_list:
            grouped_asset_list[parent] = []
        grouped_asset_list[parent].append(item)

    #! APPEND CHILD INTO PARENT DOCTYPE LIST
    for asset in items:
        if asset.name in grouped_asset_list:
            asset.asset_list = grouped_asset_list[asset.name]

    return items
