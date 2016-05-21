$(document).ready(function() {

    /*
    $(".breadcrumbs").replaceWith(
    '<div class="breadcrumbs">' +
    '<a href="/admin/">Home</a> › ' +
    '<a href="/admin/testautomation/">Testautomation</a> › ' +
    '<a href="/admin/testautomation/testcase">Test Cases</a> › ' +
    'Test Environment' +
    '</div>'
    )
    */

    /*
    This function is called every time SELECT ALL RANDOM BROWSER is clicked
    */
    $("#select_all_browser_any").click(function(event) {
        if ($(event.target).is(':checked')) {
            $("input:checkbox[name$='_browsers']").each(function () {
                $(this).prop("checked", false);
            });

            $("input:checkbox[name^='browsers_']").each(function () {
                $(this).prop("checked", false);
            });

            $("input:checkbox[name$='_browsers_any']").each(function () {
                $(this).prop("checked", true);
            });
        } else {
            $(event.target).prop("checked", true);
        }
    });

    /*
    This function is called every time SELECT ALL SPECIFIC BROWSER is clicked
    */
    $("[name^='browsers_']").click(function(event) {
        var browser = $(event.target).attr('name').split("_").slice(-1)[0];
        var id = "_browser_" + browser;
        var selector = "input:checkbox[id$='"+id+"']";

        if ($(event.target).is(':checked')) {
            $(selector).each(function () {
                $(this).prop("checked", true);
            });

            $("input:checkbox[name$='_browsers_any']").each(function () {
                $(this).prop("checked", false);
            });

            $("input:checkbox[name$='_browsers_any']").each(function () {
                $(this).prop("checked", false);
            });

            $("#select_all_browser_any").prop("checked", false);
        } else {
            $(selector).each(function () {
                $(this).prop("checked", false);
            });

            var id_arr = [];

            $("input:checkbox[name$='_browsers_any']").each(function () {
                id_arr.push($(this).attr('name').split("_")[0]);
            });

            for (var i = 0, n = id_arr.length; i < n; i++) {
               var tc_selector = "input:checkbox[name='"+id_arr[i]+"_browsers']";

               if ($(tc_selector+":checked").length == 0) {
                    $("input:checkbox[id='" + id_arr[i] + "_browsers_any']").each(function () {
                        $(this).prop("checked", true);
                    });
                }
            }

            if ($("input:checkbox[id$='_browsers_any']:checked").length == $("input:checkbox[id$='_browsers_any']").length) {
                $("#select_all_browser_any").prop("checked", true);
            }
        }
    });

    $("[name$='_browsers']").click(function(event) {
        if ($(event.target).is(':checked')) {
            var id = $(event.target).attr('name').split("_")[0];
            $("input:checkbox[id='"+id+"_browsers_any']").each(function () {
                $(this).prop("checked", false);
            });

            var checkbox_ids = $(event.target).attr('id').replace(id, "");

            if ($("input:checkbox[id$='"+checkbox_ids+"']:checked").length == $("input:checkbox[id$='"+checkbox_ids+"']").length){
                $("input:checkbox[id='select_all_browsers_" + $(event.target).attr('id').split("_").slice(-1)[0] + "']").each(function () {
                        $(this).prop("checked", true);
                });
            }

            $("#select_all_browser_any").prop("checked", false);
        } else {
            var id = $(event.target).attr('name').split("_")[0];

            if ($("input:checkbox[id^='"+id+"_browser_']:checked").length == 0) {
                $("input:checkbox[id='"+id+"_browsers_any']").each(function () {
                    $(this).prop("checked", true);
                });
            }

            $("input:checkbox[id='select_all_browsers_" + $(event.target).attr('id').split("_").slice(-1)[0] + "']").each(function () {
                    $(this).prop("checked", false);
            });

            if ($("input:checkbox[id$='_browsers_any']:checked").length == $("input:checkbox[id$='_browsers_any']").length) {
                $("input:checkbox[id='select_all_browser_any']").each(function () {
                    $(this).prop("checked", true);
                });
            }
        }
    });

    $("[name$='_browsers_any']").click(function(event) {
        if ($(event.target).is(':checked')) {
            var id = $(event.target).attr('name').split("_")[0];

            $("input:checkbox[id^='"+id+"_browser_']").each(function () {
                $(this).prop("checked", false);
            });

            $("[name$='_browsers_any']")

            if ($("[name$='_browsers_any']:checked").length == $("[name$='_browsers_any']").length) {
                $("input:checkbox[id='select_all_browser_any']").each(function () {
                    $(this).prop("checked", true);
                });
            }

            $("input:checkbox[name^='browsers_']").each(function () {
                $(this).prop("checked", false);
            });

        } else {
            $(event.target).prop("checked", true);
        }
    });
});