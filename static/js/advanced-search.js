(function() {
    'use strict';

    window.addEventListener('load', function() {
        var form = document.getElementById('advanced-search');
        form.addEventListener('submit', function(event) {
            if (form.checkValidity() === false) {
                event.preventDefault();
                event.stopPropagation();
            }
            console.log("In success listener");
            form.classList.add('was-validated');
        }, false);
    }, false);
})();

function addSearchRow() {
    // var currentRow = $(this).parent();
    var searchRow = $(".search-row:last");
    var currentSize = $(".search-row").length;
    var newRow = searchRow.clone();
    newRow.children().each(function(index) {
        $(this).children("select, input").each(function() {
            var currentId = $(this).prop("id");
            currentId = currentId.replace(/([\d*])/, currentSize);
            $(this).prop("id", currentId);
            $(this).prop("name", currentId);
            $(this).val("");
        });
    });
    searchRow.after(newRow);
}
