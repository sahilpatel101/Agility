
frappe.ui.form.on('Item', {
    custom_style_code: function (frm) {
        if (frm.doc.has_variants == 1) {
            frm.set_value("item_code", frm.doc.custom_style_code)
        }
        else
            frappe.msg.print("Internal error")
    },
    onload: function (frm) {
        frappe.call({
            method: "agility.api.item.get_color_code",
            args: {
                item_attribute: "Shoe Colour",
                template_code: frm.doc.name,
            },
            callback: function (r) {
                var data = r.message
                const colorOptions = data.map(item => item.attribute_value).join('\n');

                frm.fields_dict['custom_assets_list'].grid.update_docfield_property('color_code', 'options', colorOptions);
            }
        })
    }
});


