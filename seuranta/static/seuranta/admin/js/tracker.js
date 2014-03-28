if (jQuery !== undefined) {
    var django = {
        'jQuery':jQuery,
    };
}
(function($) {
    $(document).ready(function() {
        if( $('#tracker_form').length>0 ){
            $('#tracker_form').submit();
        }
        var proto = document.location.protocol,
            domain = document.domain
        
        $.each($(".tracker_link"), function(i, el){
            var abs_link = $(el).attr("href"),
                full_link = proto+"//"+domain+abs_link;
                $(el).append("<br/>").qrcode({text:full_link});
        })
    });
})(django.jQuery);
