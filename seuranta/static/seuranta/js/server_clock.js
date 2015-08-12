/* server_clock.js */
var ServerClock = function(opts){
  if (!(this instanceof ServerClock)) return new ServerClock(opts);

  var defaultOptions = { url: null },
      options = $.extend({}, defaultOptions, opts),
      drifts = [],
      $$ = this;

  function getAverageDrift(){
    var total_drift = 0;
    for(var ii=0; ii < drifts.length; ii++){
        total_drift += drifts[ii];
    }
    return total_drift/drifts.length;
  }

  function onServerResponse(requestTime){
    return function(response){
      var now = +new Date(),
          serverTime = response.time*1e3,
          drift = serverTime - (now + requestTime)/2;
      drifts.push(drift);
    };
  }

  if(options.url){
    (function syncClock(){
      setTimeout(syncClock, 300*1e3);    // Every 5 minutes
      drifts = [];
      (function fetchServerTime(){
        if(drifts.length < 3){
          setTimeout(fetchServerTime, 500);    // Every 5 minutes
          var clientRequestTime = +new Date();
          $.ajax({
            type: 'GET',
            url: options.url,
            dataType: 'json'
          })
          .done(onServerResponse(clientRequestTime));
        }
      })();
    })();
  }

  this.now = function(){
    return new Date(+new Date() + getAverageDrift());
  };

  this.getDrift = function(){
    return getAverageDrift();
  };
};
