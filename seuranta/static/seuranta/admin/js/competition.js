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
                  $('#id_timezone').val(jstz.determine().name());
              }
          )
          .appendTo($('#id_timezone').parent());
        }
      });
    });
  });
})(django.jQuery);
