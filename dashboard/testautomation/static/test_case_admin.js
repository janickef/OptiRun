$( document ).ready(function() {
    alert("hello");
    (function($) {
        $(function() {
            var verified = $('#field-end_by');

            // show/hide on load based on pervious value of selectField
            toggleVerified(selectField.val());

            // show/hide on change
            selectField.change(function() {
                toggleVerified($(this).val());
            });
        });
})(django.jQuery);

function($) {
    alert("hello");
    $(function() {
        var selectField = $('#id_recurrence_rule'),
            verified = $('#id_end_by');

        //alert(JSON.stringify(selectField));
        //alert(JSON.stringify(verified));

        function toggleVerified(value) {
            value == 0 ? verified.show() : verified.hide();
        }

        // show/hide on load based on pervious value of selectField
        toggleVerified(selectField.val());

        // show/hide on change
        selectField.change(function() {
            toggleVerified($(this).val());
            $(".class_field-end_by").hide()
            //alert($("#id_title").val());
            $("#id_title").hide()
        });
    });
})(django.jQuery);