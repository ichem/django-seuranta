var clock = ServerClock({url: '/api/time'});
var map = null;
var is_live = false;
var is_real_time = false;
var replay_offset = 0;
var competition_data = null;
var open_street_map = null;

var COLORS = new function(){
    var colors = ["#09F","#3D0","#F09","#D30","#30D","#DD0","#2DD","#D00","#D33","#00D","#DD2","#BFB"],
        $t = this;
    $t.cnt = -1;
    $t.get = function(){
        this.cnt++;
        if( this.cnt==colors.length )this.cnt = 0;
        return colors[this.cnt];
    };
    return $t;
};

var load_competition = function(competition_id){
  $.ajax({
    url: "/api/competition/"+competition_id
  }).done(
    on_load_competition
  ).fail(
    function(){
      alert('Could not load competition');
    }
  );
}

var on_load_competition = function(response){
  competition_data = response;
  map.setView(
    [competition_data.latitude, competition_data.longitude],
    competition_data.zoom
  );
  if(competition_data.map.display_mode === "map"){
    map.removeLayer(open_street_map);
  }else if(competition_data.map.background_tile_url !== ""){
    map.removeLayer(open_street_map);
    L.tileLayer(
      competition_data.map.background_tile_url,
      {maxZoom: 18}
    ).addTo(map);
  }

}

var load_competitors = function(competition_id){
  $.ajax({
    url: "/api/competitor/",
    data: {
      competition_id: competition_id
    }
  }).done(
    on_load_competitors
  ).fail(
    function(){
      alert('Could not load competitors');
    }
  );
}

var on_load_competitors = function(response){
/*
  (function draw(){
    drawCompetitors(clock.now()-30*1e3)
    setTimeout(draw, 200);
  })();
*/
};

var drawCompetitors = function(time){

}

$(function() {
  map = L.map('map', {
    center: [15, 0],
    zoom: 3
  });
  open_street_map = L.tileLayer('http://{s}.tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png', {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    maxZoom: 18
  })
  open_street_map.addTo(map);

  var url = window.location.href;
  var competition_id = url.match(/^.*\/watch\/(.{22})\/?$/)[1];
  load_competition(competition_id);
  load_competitors(competition_id);
})
