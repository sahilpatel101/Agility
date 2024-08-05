from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
import frappe
from erpnext.controllers.accounts_controller import (
    AccountsController,
    get_taxes_and_charges,
)


# from erpnext.controllers.accounts_controller.get_taxes_and_charges


# ? SALES ORDER
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
        doc.save()  # Ensure changes are saved
        frappe.db.commit()  # Commit the transaction

    print("Updated doc:", doc.as_dict())
