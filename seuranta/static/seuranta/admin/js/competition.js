if (jQuery !== undefined) {
    var django = {
        'jQuery':jQuery,
    };
}
(function($) {
  $(document).ready(function() {
    if($("#id_timezone").length > 0){
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

    $('head').append( $('<link rel="stylesheet" type="text/css" />').attr('href', '//cdn.leafletjs.com/leaflet-0.7.3/leaflet.css') );
    $.getScript( "//cdn.leafletjs.com/leaflet-0.7.3/leaflet.js" , function(){
      $.each($(".field-latitude"), function(index, element){
        var latitude = parseFloat($(element).find('input').val())
        var longitude = parseFloat($(element).parent().find('.field-longitude input').val())
        var zoom = parseInt($(element).parent().find('.field-zoom input').val())
        var map_id = 'map_'+index
        $("<div/>")
        .attr({id: map_id})
        .css('height', '400px')
        .appendTo($(element).parent());

        var map = L.map(map_id).setView([latitude, longitude], zoom);
        // add an OpenStreetMap tile layer
        L.tileLayer('//{s}.tile.osm.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        var marker = L.marker([latitude, longitude], {draggable:'true'})
        .addTo(map)
        marker.on('dragend', function(event){
          var position = event.target.getLatLng();
          $(element).find('input').val(position.lat);
          $(element).parent().find('.field-longitude input').val(position.lng);
          $(element).parent().find('.field-zoom input').val(map.getZoom());
        });
      });
    })
  });
})(django.jQuery);
