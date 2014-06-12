/* server_clock.js */
var ServerClock = function(opts){
    var default_options = {
            drift: 0,                        // The Server/Client clock drift
            time_api_url: null               // The Server time api URL
        },
        options = $.extend({},default_options, opts),
        drift = options.drift,
        drifts = [],
        $$ = this;
    function on_server_response(request_time){
        return function(response){
            if(response.status=="OK"){
                var now = +new Date(),
                    server_time = response.data.timestamp*1e3,
                    request_drift = response.data.drift*1e3,
                    response_drift = now - server_time,
                    response_time = (now - request_time)/2,
                    avg_drift = (request_drift - response_drift) /2,
                    total_drifts=0;
                drifts.push(avg_drift-response_time);
                for (var k=0; k<drifts.length; k++){
                    total_drifts += drifts[k];
                }
                drift = total_drifts/drifts.length;
            }
        }
    }
    if(options.time_api_url){
        (function syncClock(){
            //Do some ajax magic to get the clock drift
            drifts = [];
            for(var i=0; i<3; i++){
                var client_request_time = +new Date();
                $.ajax({
                    type:"POST",
                    url:options.time_api_url,
                    data:{timestamp:+client_request_time/1e3},
                    dataType:"json"
                })
                .done(on_server_response(client_request_time));
            }
            setTimeout(syncClock, 300*1e3);
        })();
    }
    $$.now = function(){
        return +new Date()+drift;
    }
    $$.getDrift = function(){
        return drift;
    }
    return $$;
}
