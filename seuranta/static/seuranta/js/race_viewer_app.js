var clock = ServerClock({url: '/api/time'});
var map = null;
var is_live = false;
var is_real_time = false;
var replay_offset = 0;
var competition = null;
var open_street_map = null;
var competitor_list = [];
var competitor_routes = {};
var routes_last_fetched = -Infinity;

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
  fetch_competitor_routes();
}

var fetch_competitor_list = function(url){
  url = url || "/api/competitor";
  var data={};
  if(url == "/api/competitor"){
    data.competition_id=competition.id
    data.result_per_page = 1000
    data.approval_status = 'approved'
  }
  $.ajax({
    url: url,
    data: data
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

var fetch_competitor_routes = function(url){
  url = url || "/api/route";
  var data = {};
  if(url == "/api/route"){
    data.competition_id = competition.id;
    if(routes_last_fetched!= -Infinity){
      data.start = routes_last_fetched;
    }
  }
  $.ajax({
    url: url,
    data: data
  }).done(function(response){
    $.each(response.results, function(ii, route_data){
      var route = PositionArchive.fromTks(route_data.encoded_data);
      if(competitor_routes[route_data.competitor]!==undefined){
        $.each(route.getArray(), function(jj, position){
          competitor_routes[route_data.competitor].add(position);
        });
      } else {
        competitor_routes[route_data.competitor] = route;
      }
    });
    if(response.next === null){
      routes_last_fetched = clock.now()/1e3
    } else {
      fetch_competitor_routes(response.next)
    }
  }).fail(function(){

  });
};

var display_competitor_list = function(){
    var list_div = $('<ul/>');
    list_div.addClass('media-list');
    $.each(competitor_list, function(ii, competitor){
      competitor.color = competitor.color || COLORS.get();
      competitor.is_shown = competitor.is_shown || true;
      var div = $('<li/>');
      div.addClass('media').html('\
        <div class="media-left"><i class="media-object fa fa-circle fa-3x" style="color:'+competitor.color+'"></i></div>\
        <div class="media-body"><b>'+competitor.name+'</b><br/>\
          <div class="btn-group btn-group-xs" role="group">\
            <button type="button" class="toggle_competitor_btn btn btn-default"><i class="fa fa-toggle-on"></i></button>\
            <button type="button" class="center_competitor_btn btn btn-default"><i class="fa fa-map-marker"></i></button>\
            <!-- <button type="button" class="competitor_options_btn btn btn-default"><i class="fa fa-cog"></i></button> -->\
          </div>\
        </div>')
      $(div).find('.toggle_competitor_btn').on('click', function(e){
        e.preventDefault();
        var icon = $(this).find('i');
        if(icon.hasClass('fa-toggle-on')){
          icon.removeClass('fa-toggle-on').addClass('fa-toggle-off');
          competitor.is_shown = false
        }else{
          icon.removeClass('fa-toggle-off').addClass('fa-toggle-on');
          competitor.is_shown = true;
        }
      })
      $(div).find('.center_competitor_btn').on('click', function(){
        zoom_on_competitor(competitor);
      })
      list_div.append(div);
      competitor.div = div;
    });

    $('#sidebar').html('');
    $('#sidebar').append(list_div);
}


var zoom_on_competitor = function(competitor){

}

var drawCompetitors = function(){

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

  $('#runners_show_button').on('click', function(e){
    e.preventDefault();
    if($('#sidebar').hasClass('hidden-xs')){
      $('#sidebar').removeClass('hidden-xs').addClass('col-xs-12');
      $('#map').addClass('hidden-xs').removeClass('col-xs-12');
    }else{
      $('#sidebar').addClass('hidden-xs').removeClass('col-xs-12');
      $('#map').removeClass('hidden-xs').addClass('col-xs-12');
    }
  })
})
