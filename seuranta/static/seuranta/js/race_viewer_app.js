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
var time_offset = 0;
var playback_speed = 1;
var tail_length = 60;
var fetching_routes = false;

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
var is_competition_live = function(){
    var start = + new Date(competition.start_date);
    var end = + new Date(competition.end_date);
    var now = + clock.now();
    return (start < now && now < end);
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
  if(is_competition_live()){
    select_live_mode();
  }
  fetch_competitor_list();
  fetch_competitor_routes();
}

var select_live_mode = function(){
  $("#live_button").addClass('active');
  $("#replay_button").removeClass('active');
  $("#replay_mode_buttons").hide();
  $("#replay_control_buttons").hide();
  time_offset = -competition.live_delay;
  playback_speed = 1;
  is_live_mode=true;

  (function while_live(){
    if(+clock.now()-routes_last_fetched > -time_offset*1e3 && !fetching_routes){
      fetch_competitor_routes();
    }
    draw_competitors();
    if(is_live_mode){
      setTimeout(while_live, 100)
    }
  })()
}

var select_replay_mode = function(){
  $("#live_button").removeClass('active');
  $("#replay_button").addClass('active');
  $("#replay_mode_buttons").show();
  $("#replay_control_buttons").show();
  is_live_mode=false
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
  fetching_routes = true;
  url = url || "/api/route";
  var data = {};
  if(url == "/api/route"){
    data.competition_id = competition.id;
    if(routes_last_fetched!= -Infinity){
      data.created_after = routes_last_fetched/1e3;
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
      routes_last_fetched = +clock.now();
      fetching_routes = false;
      draw_competitors(true);
    } else {
      fetch_competitor_routes(response.next)
    }
  }).fail(function(){
    fetching_routes = false;
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


var zoom_on_competitor = function(compr){
  var route = competitor_routes[compr.id]
  var loc = route.getByTime(+clock.now()+time_offset);
  map.setView([loc.coords.latitude, loc.coords.longitude])
}

var draw_competitors = function(){
  $.each(competitor_list, function(ii, competitor){
    if(!competitor.is_shown){
      return;
    }
    var route = competitor_routes[competitor.id]
    if(route != undefined){
      var loc = route.getByTime(+clock.now()-5*1e3+time_offset*1e3);
      if(competitor.map_marker == undefined){
        competitor.map_marker = L.circleMarker([loc.coords.latitude, loc.coords.longitude],
                                               {weight:5, radius: 7, color: competitor.color, fill: false, fillOpacity:0});
        competitor.map_marker.addTo(map);
      }else{
        competitor.map_marker.setLatLng([loc.coords.latitude, loc.coords.longitude]);
      }
      var tail = route.extractInterval(+clock.now()-5*1e3+time_offset*1e3-tail_length*1e3,
                                       +clock.now()-5*1e3+time_offset*1e3);
      var tail_latlng = []
      $.each(tail.getArray(), function(jj, pos){
        tail_latlng.push([pos.coords.latitude, pos.coords.longitude]);
      })
      if(competitor.tail == undefined){
        competitor.tail = L.polyline(tail_latlng, {color: competitor.color});
        competitor.tail.addTo(map);
      }else{
        competitor.tail.setLatLngs(tail_latlng);
      }
    }
  })
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
