$(document).ready(function(){
    data = $('[data-toggle="tooltip"]')
    data.tooltip();

    select_any_browser = $('#select_all_browser_any');
    select_any_browser = "test";

    alert("hello");

    $.each(data, function(key, value){
        alert( key + ': ' + value );
    });
});

function toggleCheckbox(element) {
    alert("HELLOOOOO")
    element.checked = !element.checked;
}

document.getElementById('select_all_browser_any').addEventListener("change", function(event) {
    (function(event) {
        alert(this);
    }).call(document.getElementById('select_all_browser_any'), event);
});