from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
import frappe
from erpnext.controllers.accounts_controller import (
    AccountsController,
    get_taxes_and_charges,
)


def sales_order_set_taxes_and_totals(doc, events):
    print("Function called with doc:", doc.name)

    taxes_and_charges = get_taxes_and_charges(
        master_doctype="Sales Taxes and Charges Template",
        master_name=doc.taxes_and_charges,
    )

    print("Taxes and Charges:", taxes_and_charges)

    if taxes_and_charges:
        for row in taxes_and_charges:
            doc.append("taxes", row)
        doc.save()
        frappe.db.commit()
