if (jQuery !== undefined) {
    var django = {
        'jQuery':jQuery,
    };
}
(function($) {
    $(document).ready(function() {
        $("<button/>")
        .text("Detect")
        .on("click", function(e){
            e.preventDefault()
            $("#id_timezone").val(jstz.determine().name())
        })
        .appendTo($("#id_timezone").parent())
    });
})(django.jQuery);