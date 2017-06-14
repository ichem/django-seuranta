var clock = ServerClock({url: '/api/time'});
var map = null;
var is_live_mode = false;
var is_real_time = true;
var replay_offset = 0;
var competition = null;
var open_street_map = null;
var competitor_list = [];
var competitor_routes = {};
var routes_last_fetched = -Infinity;
var time_offset_s = 0;
var playback_rate = 1;
var playback_paused = true;
var prev_display_refresh = 0;
var tail_length = 60;
var is_currently_fetching_routes = false;
var current_time = 0;

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

var has_competition_started = function(){
    var start = +new Date(competition.start_date);
    var now = +clock.now();
    return start < now;
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
  if(competition.map.display_mode === "map" || competition.map.display_mode === "map+bck"){
    var anchors = [
        [competition.map.top_left_lat, competition.map.top_left_lng],
        [competition.map.top_right_lat, competition.map.top_right_lng],
        [competition.map.bottom_right_lat, competition.map.bottom_right_lng],
        [competition.map.bottom_left_lat, competition.map.bottom_left_lng]
    ];
    var transformedImage = L.imageTransform(competition.map.public_url, anchors);
    transformedImage.addTo(map);
  }
  check_race_started();
}

var check_race_started = function(){
  if(has_competition_started()){
    $("#before_race_modal").hide();  
    if(is_competition_live()){
      select_live_mode();
    } else {
      $("#live_button").hide();
      select_replay_mode();
    }
    fetch_competitor_list();
    fetch_competitor_routes();
  }else{
    window.setTimeout(check_race_started, 1000);
  }
}

var select_live_mode = function(e){
  if(e !== undefined){
    e.preventDefault();
  }
  if(is_live_mode){
    return;
  }
  $("#live_button").addClass('active');
  $("#replay_button").removeClass('active');
  $("#replay_mode_buttons").hide();
  $("#replay_control_buttons").hide();
  time_offset_s = -competition.live_delay;
  is_live_mode=true;

  (function while_live(){
    if(+clock.now()-routes_last_fetched > -time_offset_s*1e3 && !is_currently_fetching_routes){
      fetch_competitor_routes();
    }
    current_time = +clock.now()-5*1e3+time_offset_s*1e3;
    draw_competitors();
    if(is_live_mode){
      setTimeout(while_live, 100);
    }
  })()
}

var select_replay_mode = function(e){
  if(e !== undefined){
    e.preventDefault();
  }
  if(!is_live_mode && $("#replay_button").hasClass('active')){
    return;
  }
  $("#live_button").removeClass('active');
  $("#replay_button").addClass('active');
  $("#replay_mode_buttons").show();
  $("#replay_control_buttons").show();
  is_live_mode=false;
  prev_shown_time = +new Date(competition.start_date);
  playback_paused = true;
  playback_rate = 1;
  prev_display_refresh = +clock.now();
  (function while_replay(){
    if(is_competition_live() && +clock.now()-routes_last_fetched > -time_offset_s*1e3 && !is_currently_fetching_routes){
      fetch_competitor_routes();
    }
    var actual_playback_rate = playback_paused?0:playback_rate;
    current_time = prev_shown_time + (+clock.now() - prev_display_refresh)*actual_playback_rate;
    current_time = Math.min(+clock.now(), current_time, +new Date(competition.end_date));
    draw_competitors();
    prev_shown_time = current_time;
    prev_display_refresh = +clock.now();
    if(!is_live_mode){
      setTimeout(while_replay, 100);
    }
  })()
}

var fetch_competitor_list = function(url){
  url = url || "/api/competitor";
  var data={};
  if(url == "/api/competitor"){
    data.competition_id = competition.id;
    data.results_per_page = 1000;
    data.approval_status = 'approved';
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
  is_currently_fetching_routes = true;
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
      is_currently_fetching_routes = false;
    } else {
      fetch_competitor_routes(response.next);
    }
  }).fail(function(){
    is_currently_fetching_routes = false;
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
          competitor.is_shown = false;
          map.removeLayer(competitor.map_marker);
          map.removeLayer(competitor.name_marker);
          map.removeLayer(competitor.tail);
          competitor.map_marker = null;
          competitor.name_marker = null;
          competitor.tail = null;
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
  var route = competitor_routes[compr.id];
  var time_t = current_time;
  if(!is_real_time){
    time_t += +new Date(compr.start_time) - new Date(competition.start_date);
  }
  var loc = route.getByTime(time_t);
  map.setView([loc.coords.latitude, loc.coords.longitude]);
}
var get_progress_bar_text = function(){
    var result = '';
    var viewed_time = current_time;
    if(!is_real_time){
        viewed_time -= new Date(competition.start_date);
        var t = viewed_time/1e3;
        to2digits = function(x){return ('0'+Math.floor(x)).slice(-2);},
        result += t > 3600 ? Math.floor(t/3600) + ':': '';
        result += to2digits((t / 60) % 60) + ':' + to2digits(t % 60);
    }else{
        result = moment(+new Date(viewed_time)).tz(competition.timezone).format('HH:mm:ss');
    }
    return result;
}
var draw_competitors = function(){
  // play/pause button
  if(playback_paused){
    var html = '<i class="fa fa-play"></i> x'+playback_rate;
    if($('#play_pause_button').html() != html){
      $('#play_pause_button').html(html);
    }
  } else {
    var html = '<i class="fa fa-pause"></i> x'+playback_rate;
    if($('#play_pause_button').html() != html){
      $('#play_pause_button').html(html);
    }
  }
  // progress bar
  var perc = is_live_mode ? 100 : (current_time-new Date(competition.start_date))/(Math.min(+clock.now(), new Date(competition.end_date))-new Date(competition.start_date))*100
  $('#progress_bar').css('width', perc+'%').attr('aria-valuenow', perc);
  $('#progress_bar_text').html(get_progress_bar_text());
  $.each(competitor_list, function(ii, competitor){
    if(!competitor.is_shown){
      return;
    }
    var route = competitor_routes[competitor.id]
    if(route != undefined){
      var viewed_time = current_time;
      if(!is_live_mode && !is_real_time && competitor.start_time){
        viewed_time += new Date(competitor.start_time) - new Date(competition.start_date);
      }
      var loc = route.getByTime(viewed_time);
      if(!isNaN(loc.coords.latitude)){
        if(competitor.map_marker == undefined){
          competitor.map_marker = L.circleMarker([loc.coords.latitude, loc.coords.longitude],
                                                 {weight:5, radius: 7, color: competitor.color, fill: false, fillOpacity:0, opacity: 0.75});
          competitor.name_marker = L.marker([loc.coords.latitude, loc.coords.longitude],
                                            {icon: L.divIcon({className: 'runner-icon',
                                                              html: '<span style="-webkit-text-fill-color: '+competitor.color+';">'+competitor.short_name+'</span>'})
                                            });
          competitor.map_marker.addTo(map);
          competitor.name_marker.addTo(map);
        }else{
          competitor.map_marker.setLatLng([loc.coords.latitude, loc.coords.longitude]);
          competitor.name_marker.setLatLng([loc.coords.latitude, loc.coords.longitude]);
        }
      }
      var tail = route.extractInterval(viewed_time-tail_length*1e3, viewed_time);
      var tail_latlng = [];
      $.each(tail.getArray(), function(jj, pos){
        if(!isNaN(pos.coords.latitude)){
          tail_latlng.push([pos.coords.latitude, pos.coords.longitude]);
        }
      })
      if(competitor.tail == undefined){
        competitor.tail = L.polyline(tail_latlng, {color: competitor.color, opacity: 0.75});
        competitor.tail.addTo(map);
      }else{
        competitor.tail.setLatLngs(tail_latlng);
      }
    }
  })
}

$(function() {
  $("#before_race_modal").modal('show').on('hide.bs.modal', function(e){
      e.preventDefault();
  });
  map = L.map('map', {
    center: [15, 0],
    zoom: 3
  });
  open_street_map = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://mapbox.com">Mapbox</a>',
    maxZoom: 18
  });
  open_street_map.addTo(map);

  var url = window.location.href;
  var competition_id = url.match(/^.*\/watch\/(.{11})\/?(\?(.*))?(#(.*))?$/)[1];
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

  $('#live_button').on('click', select_live_mode);
  $('#replay_button').on('click', select_replay_mode);
  $('#play_pause_button').on('click', press_play_pause_button);
  $('#next_button').on('click', function(e){
    e.preventDefault();
    playback_rate = playback_rate*2;
  });
  $('#prev_button').on('click', function(e){
    e.preventDefault();
    playback_rate = Math.max(1, playback_rate/2);
  });
  $('#real_time_button').on('click', function(e){
    e.preventDefault();
    is_real_time=true;
    $('#real_time_button').addClass('active');
    $('#mass_start_button').removeClass('active');
  });
  $('#mass_start_button').on('click', function(e){
    e.preventDefault();
    is_real_time=false;
    $('#real_time_button').removeClass('active');
    $('#mass_start_button').addClass('active');
  });
  $('#full_progress_bar').on('click', press_progress_bar)
})

var press_play_pause_button = function(e){
  e.preventDefault();
  playback_paused = !playback_paused;
}

var press_progress_bar = function(e){
  var perc = (e.pageX - $('#full_progress_bar').offset().left)/$('#full_progress_bar').width();
  current_time = +new Date(competition.start_date)+(Math.min(clock.now(), +new Date(competition.end_date))-new Date(competition.start_date))*perc;
  prev_shown_time = current_time;
}
