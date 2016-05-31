function toggle(source) {
    if ($("#" + source + "-nested").is(":visible")) {
        $("#" + source + "-nested").hide();
        $("#" + source + "-right").html('<i class="fa fa-caret-down" aria-hidden="true"></i>');
    }
    else {
        $("#" + source + "-nested").fadeIn();
        $("#" + source + "-right").html('<i class="fa fa-caret-up" aria-hidden="true"></i>');
    }
}