
frappe.ui.form.on('Item', {
    custom_style_code: function (frm) {
        // Check if the item status is 'Template'
        if (frm.doc.has_variants == 1) {
            console.log("workinggggg");
            frm.set_value("item_code", frm.doc.custom_style_code)
        }
        else
            frappe.msg.print("Internal error")
    },
    // onload: function (frm) {
    //     frappe.call({
    //         method: "get_variant_attribute_value",
    //         args: {
    //             item_attribute: "Colour"
    //         },
    //         callback: function (r) {
    //             var data = r.data
    //             const colorOptions = data.map(item => item.attribute_value).join('\n');
    //             frm.fields_dict['custom_asset_list'].grid.update_docfield_property('color_code', 'options', colorOptions);
    //         }
    //     })
    // }
});
