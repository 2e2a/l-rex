var warn = false;
$(document).ready(function(){
    document.querySelectorAll('form').forEach(function (form) {
        $(form).data('serialize', $(form).serialize());
    });
    $(window).bind('beforeunload', function(e) {
        document.querySelectorAll('form').forEach(function (form) {
            if($(form).serialize() != $(form).data('serialize')) warn = true;
        });
        if(warn) return true;
    });
});
