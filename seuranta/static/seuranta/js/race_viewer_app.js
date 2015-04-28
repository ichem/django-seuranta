var clock = ServerClock({url: '/api/time'});
var map = null;
var is_live = false;
var is_real_time = false;
var replay_offset = 0;
var competition = null;
var open_street_map = null;
var competitor_list = []

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
  competition = response;
  map.setView(
    [competition.latitude, competition.longitude],
    competition.zoom
  );
  if(competition.map.display_mode === "map"){
    map.removeLayer(open_street_map);
  }else if(competition.map.background_tile_url !== ""){
    map.removeLayer(open_street_map);
    L.tileLayer(
      competition.map.background_tile_url,
      {maxZoom: 18}
    ).addTo(map);
  }
  fetch_competitor_list();
}

var fetch_competitor_list = function(url){
  url = url || "/api/competitor";
  $.ajax({
    url: url,
    data: {
      competition_id: competition.id,
      result_per_page: 1000,
      approval_status: 'approved'
    }
  }).done(function(response){
    var results;
    if(response.previous === null){
      results = [];
    }else{
      results = competitor_list;
    }
    results = results.concat(response.results)
    competitor_list = results;
    if(response.next === null){
      display_competitor_list();
    } else {
      fetch_competitor_list(response.next);
    }
  }).fail(function(){
  });
};

var display_competitor_list = function(){
    var list_div = $('<ul/>');
    list_div.addClass('media-list');
    $.each(competitor_list, function(ii, competitor){
      competitor.color = COLORS.get();
      var div = $('<li/>');
      div.addClass('media').html('\
        <div class="media-left"><a href="#"><i class="media-object fa fa-square fa-3x" style="color:'+competitor.color+'"></i></a></div>\
        <div class="media-body"><b>'+competitor.name+'</b></div>')
      list_div.append(div);
      competitor.div = div;
    });
    $('#sidebar').append(list_div)
}

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
  var competition_id = url.match(/^.*\/watch\/(.{22})\/?(\?(.*))?(#(.*))?$/)[1];
  load_competition(competition_id);
})
