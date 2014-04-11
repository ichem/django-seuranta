if (jQuery !== undefined) {
    var django = {
        'jQuery':jQuery,
    };
}
(function($) {
    $(document).ready(function() {
	$.getScript('//cdnjs.cloudflare.com/ajax/libs/moment-timezone/0.0.3/moment-timezone.min.js', function(){
	$.getScript('/static/seuranta/js/moment-timezone-data.min.js', function(){
        if( $("#id_timezone").length>0 ){
            $("<button/>")
            .text("Detect")
            .on(
                "click",
                function(e){
                    e.preventDefault();
                    $('#id_timezone').val(jstz.determine().name())
                }
            )
            .appendTo($('#id_timezone').parent());
            /*
            var tz_name = $('#id_timezone').val();
            $('.datetime').each(function(i, el){
                var a, b, c;
                a = $(el).children('.vDateField').val()
                b = $(el).children('.vTimeField').val()
                if (a && b){
                    c = moment(a+"T"+b+"Z").tz(tz_name).format()
                    $(el).children('.vDateField').val(c.slice(0,10))
                    $(el).children('.vTimeField').val(c.slice(11,19))
                }
            })
            */
        }
	});
	});
    });
})(django.jQuery);
