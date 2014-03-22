/* server_clock.js */
var ServerClock = function(opts){
    var default_options = {
            drift: 0,                        // The Server/Client clock drift
            time_api_url: null               // The Server time api URL
        },
        options = $.extend({},default_options, opts),
        drift = options.drift,
        $$ = this;
    if(options.time_api_url){
        (function syncClock(){
            //Do some ajax magic to get the clock drift
            var client_request_time = +new Date();
	        $.ajax({
	            type:"GET",
	            url:options.time_api_url,
	            data:{t:+client_request_time/1e3},
	            dataType:"json"
	        })
			.done(function(data){
    	    	var now = +new Date(),
    				server_time = data.time*1e3,
    				request_drift = data.drift*1e3,
    				response_drift = now - server_time,
    				response_time = (now - client_request_time)/2,
    				avg_drift = (request_drift - response_drift) /2;
    			drift += avg_drift-response_time;
			});
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