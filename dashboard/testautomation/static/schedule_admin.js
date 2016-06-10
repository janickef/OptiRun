$(document).ready(function() {
    alert();
    toggleDisabling($("#id_repeat"));
    toggleEndBy();

    $("#id_repeat").click(function(event) {
        toggleDisabling($("#id_repeat"));
        toggleEndBy();
    });

    $("input:radio[name='range']").click(function(event) {
        toggleEndBy();
    });

    $("input:submit[name='_save'], input:submit[name='_continue'], input:submit[name='_addanother']").click(function(event) {
        toggleElement("input:radio[name='recurrence_rule']", false)
        toggleElement("input:radio[name='range']", false)
        toggleElement(".field-end_by input[class='vDateField']", false)
        toggleElement(".field-end_by input[class='vTimeField']", false)
    });
});

function toggleDisabling(target) {
    if (target.is(':checked')) {
        toggleElement("input:radio[name='recurrence_rule']", false)
        toggleElement("input:radio[name='range']", false)
    } else {
        toggleElement("input:radio[name='recurrence_rule']", true)
        toggleElement("input:radio[name='range']", true)
    }
}

function toggleEndBy() {
    if ($("#id_repeat").is(":checked") && $("#id_range_1").is(":checked")) {
        toggleElement(".field-end_by input[class='vDateField']", false)
        toggleElement(".field-end_by input[class='vTimeField']", false)
        $(".field-end_by .datetimeshortcuts").show();
    } else {
        toggleElement(".field-end_by input[class='vDateField']", true)
        toggleElement(".field-end_by input[class='vTimeField']", true)
        $(".field-end_by .datetimeshortcuts").hide();
    }
}

function toggleElement(selector, disabled) {
    $(selector).each(function () {
        $(this).prop("disabled", disabled);
    });
}