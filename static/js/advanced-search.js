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
    console.log("New row is trying to href " + this);
}
