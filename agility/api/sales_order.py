import frappe
from frappe.utils import getdate


@frappe.whitelist()
def itemcart(customer, items):
    if isinstance(items, str):
        import json

        items = json.loads(items)

    for item in items:
        if isinstance(item.get("delivery_date"), str):
            item["delivery_date"] = getdate(item["delivery_date"])

    existing_orders = frappe.get_all(
        "Sales Order",
        filters={"customer": customer, "status": "Draft"},
        fields=["name"],
    )

    if existing_orders:
        # Update existing Sales Order
        sales_order = frappe.get_doc("Sales Order", existing_orders[0].name)

        for item in items:
            item_exists = False
            for so_item in sales_order.items:
                if so_item.item_code == item["item_code"]:
                    so_item.qty += item["qty"]
                    so_item.delivery_date = item["delivery_date"]
                    item_exists = True
                    break

            if not item_exists:
                sales_order.append(
                    "items",
                    {
                        "item_code": item["item_code"],
                        "qty": item["qty"],
                        "delivery_date": item["delivery_date"],
                    },
                )

        sales_order.save()
        frappe.db.commit()
        return sales_order

    else:
        # Create a new Sales Order
        sales_order = frappe.get_doc(
            {
                "doctype": "Sales Order",
                "customer": customer,
                "set_warehouse": "All Warehouses - AD",
                "items": items,
            }
        )

        sales_order.insert(ignore_permissions=True, ignore_mandatory=1)
        frappe.db.commit()
        return sales_order
