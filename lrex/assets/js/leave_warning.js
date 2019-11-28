var warn = false;
var isSubmit = false;
$(document).ready(function(){
    document.querySelectorAll('form').forEach(function (form) {
        $(form).data('serialize', $(form).serialize());
        form.addEventListener('submit', function () {
            isSubmit = true;
        })
    });
    $(window).bind('beforeunload', function(e) {
        document.querySelectorAll('form').forEach(function (form) {
            if($(form).serialize() != $(form).data('serialize')) warn = true;
        });
        if(warn && !isSubmit) return true;
    });
});
