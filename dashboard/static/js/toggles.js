/*function toggle_browsers_any(source) {
    var source_num = source.getAttribute("name").split("_")[0];

    checkbox_name = source_num + "_browsers";
    checkboxes = document.getElementsByName(checkbox_name);

    if (source.checked) {
        for(var i = 0, n = checkboxes.length; i < n; i++) {
            checkboxes[i].checked = false;
        }
    }

    else {
        source.checked = true;
    }
}

function toggle_browsers(source) {
    var source_num = source.getAttribute("name").split("_")[0];

    checkbox_name = source_num + "_browser_any";
    any_checkbox = document.getElementById(checkbox_name);

    if (source.checked) {
        any_checkbox.checked = false;
    } else {
        checkbox_name = source_num + "_browsers";
        checkboxes = document.getElementsByName(checkbox_name);

        var checked = 0;
        for(var i = 0, n = checkboxes.length; i < n; i++) {
            if (checkboxes[i].checked){
                checked = checked + 1;
            }
        }
        if (checked == 0){
            any_checkbox.checked = true;
        }
    }
}*/