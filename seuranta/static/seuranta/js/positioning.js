var IntValCodec = (function(){
    var decodeValueFromString = function (encoded){
        var enc_len = encoded.length,
            i=0,
            shift = 0,
            result = 0,
            b = 0x20;
        while(b >= 0x20 && i<enc_len){
              b = encoded.charCodeAt(i) - 63;
              i += 1;
              result |= (b & 0x1f) << shift;
              shift += 5;
        }
        if(result&1){
            return [~(result>>>1), encoded.slice(i)];
        }else{
            return [result>>>1, encoded.slice(i)];
        }
    };
    var encodeNumber = function (num){
        var encoded = "";
        while(num >= 0x20){
            encoded += String.fromCharCode((0x20 | (num & 0x1f)) + 63);
            num = num >>> 5;
        }
        encoded += String.fromCharCode((num + 63));
        return encoded;
    };
    var encodeSignedNumber = function(num){
        var sgn_num = num*Math.pow(2,1);
        if(num < 0){
            sgn_num = ~(sgn_num);
        }
        return encodeNumber(sgn_num);
    };
    return {encodeSignedNumber:encodeSignedNumber, decodeValueFromString:decodeValueFromString};
})();

var Coordinates = function(c){
    this.latitude = c.latitude;
    this.longitude = c.longitude;
    this.accuracy = c.accuracy;

    this.distance = function(c){
        var C = Math.PI/180,
            dlat = this.latitude - c.latitude,
            dlon = this.longitude - c.longitude,
            a = Math.pow(Math.sin(C*dlat / 2), 2) + Math.cos(C*this.latitude) * Math.cos(C*c.latitude) * Math.pow(Math.sin(C*dlon / 2), 2);
        return 12756274 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    };

    this.distanceAccuracy = function(c){
        return this.accuracy+c.accurracy;
    };
};

var Position = function(l){
    this.timestamp = l.timestamp;
    this.coords = new Coordinates(l.coords);

    this.distance=function(p){
        return this.coords.distance(p.coords);
    };

    this.distanceAccuracy = function(p){
        return this.coords.distanceAccuracy(p.coords);
    };
    this.speed = function(p){
        return this.distance(p)/Math.abs(this.timestamp-p.timestamp);
    };
};

var PositionArchive = function(){
    var positions = [];
    var _locationOf = function(element, start, end) {
        start = typeof(start)!=="undefined"?start:0;
        end = typeof(end)!=="undefined"?end:(positions.length-1);
        var pivot = Math.floor(start + (end - start) / 2);
        if(end-start<0){
            return start;
        }
        if(positions[start].timestamp >= element.timestamp){
            return start;
        }
        if(positions[end].timestamp <= element.timestamp){
            return end+1;
        }
        if(positions[pivot].timestamp == element.timestamp) {
            return pivot;
        }
        if(end-start<=1){
            return start+1;
        }
        if(element.timestamp > positions[pivot].timestamp) {
            return _locationOf(element, pivot, end);
        } else {
            return _locationOf(element, start, pivot-1);
        }
    };
    this.add = function(pos) {
        if(pos.timestamp===null){
            return;
        }
        var index = _locationOf(pos);
        if(positions.length>0 && index<positions.length && positions[index].timestamp==pos.timestamp){
            positions[index] = pos;
        }else if(positions.length>0 && index>=positions.length && positions[positions.length-1].timestamp==pos.timestamp){
            positions[positions.length-1]=pos;
        }else{
            positions.splice(index, 0, pos);
        }
        return this;
    };
    this.eraseInterval = function(start, end){
        var index_s=_locationOf({timestamp:start}),
            index_e=_locationOf({timestamp:end});
        while(index_s>0 && positions[index_s-1].timestamp>=start){
            index_s--;
        }
        while(index_e<positions.length-1 && positions[index_e].timestamp<=end){
            index_e++;
        }
        positions.splice(index_s, index_e-index_s);
        return this;
    };
    this.getByIndex = function(i) {
        return positions[i];
    };
    this.getPositionsCount = function() {
        return positions.length;
    };
    this.getArray = function(){
        return positions;
    };
    this.getByTime = function(t){
        var index=_locationOf({timestamp:t});
        if(index===0){
            return positions[0];
        }
        if(index>positions.length-1){
            return positions[positions.length-1];
        }
        if(positions[index].timestamp==t){
            return positions[index];
        }else{
            var prev = positions[index-1],
                next = positions[index],
                r = (t-prev.timestamp)/(next.timestamp-prev.timestamp),
                lat = (next.coords.latitude*r+(1-r)*prev.coords.latitude),
                lon = (next.coords.longitude*r+(1-r)*prev.coords.longitude),
                acc = (next.coords.accuracy*r+(1-r)*prev.coords.accuracy);
            return new Position({
                timestamp:t,
                coords:{
                    latitude:lat,
                    longitude:lon,
                    accuracy:acc
                }
            });
        }
    };
    this.extractInterval = function(t1, t2){
        var index=_locationOf({timestamp:t1}),
            i1, i2, prev, next, r, lat, lon, acc,
            result = new PositionArchive();
        if(index===0){
            i1 = 0;
        }
        else if(index>positions.length-1){
            i1 = positions.length-1;
        }
        else if(positions[index].timestamp==t1){
            i1 = index;
        }else{
            prev = positions[index-1],
            next = positions[index],
            r = (t1-prev.timestamp)/(next.timestamp-prev.timestamp),
            lat = (next.coords.latitude*r+(1-r)*prev.coords.latitude),
            lon = (next.coords.longitude*r+(1-r)*prev.coords.longitude),
            acc = (next.coords.accuracy*r+(1-r)*prev.coords.accuracy);
            result.add(new Position({
                timestamp:t1,
                coords:{
                    latitude:lat,
                    longitude:lon,
                    accuracy:acc
                }
            }));
            i1 = index;
        }
        index=_locationOf({timestamp:t2});
        if(index===0){
            i2 = 0;
        }
        else if(index>positions.length-1){
            i2 = positions.length-1;
        }
        else if(positions[index].timestamp==t2){
            i2 = index;
        }else{
            prev = positions[index-1],
            next = positions[index],
            r = (t2-prev.timestamp)/(next.timestamp-prev.timestamp),
            lat = (next.coords.latitude*r+(1-r)*prev.coords.latitude),
            lon = (next.coords.longitude*r+(1-r)*prev.coords.longitude),
            acc = (next.coords.accuracy*r+(1-r)*prev.coords.accuracy);
            result.add(new Position({
                timestamp:t2,
                coords:{
                    latitude:lat,
                    longitude:lon,
                    accuracy:acc
                }
            }));
            i2 = index-1;
        }
        for(var i=i1; i<=i2; i++){
            result.add(positions[i]);
        }
        return result;
    };
    this.getDuration = function() {
        if(positions.length<=1) {
            return 0;
        } else {
            return positions[positions.length-1].timestamp-positions[0].timestamp;
        }
    };
    this.getAge = function(now){
        now = now===null?(+new Date()):now;
        if(positions.length===0) {
            return 0;
        } else {
            return now-positions[0].timestamp;
        }
    };
    this.exportCSV = function(){
        var raw_csv="timestamp, latitude, longitude, accuracy\n";
        for(var i=0;i<positions.length;i++){
            var l = positions[i];
            raw_csv += [l.timestamp, l.coords.latitude, l.coords.longitude, l.coords.accuracy].join(", ");
            raw_csv+= "\n";
        }
        return raw_csv;
    };

    this.exportTks = function(){
        if(positions.length===0) {
            return "";
        }
        var YEAR2000=Date.parse("2000-01-01T00:00:00Z"),
            prev_pos = new Position({timestamp:YEAR2000, coords:{latitude:0, longitude:0, accuracy:0}}),
            raw="",
            last_skipped_t=null;

        for(var i=0;i<positions.length;i++){
            var k = positions[i],
                dt = k.timestamp-prev_pos.timestamp,
                dlat = k.coords.latitude-prev_pos.coords.latitude,
                dlon = k.coords.longitude-prev_pos.coords.longitude;

            if( Math.round(dlat*1e5)===0 && Math.round(dlon*1e5)===0 && i!=positions.length-1){
                last_skipped_t = k.timestamp;
            }else{
                if(last_skipped_t!==null && i!=positions.length-1){
                    dt = last_skipped_t-prev_pos.timestamp;
                    raw += IntValCodec.encodeSignedNumber(Math.round(dt/1e3)) +
                        IntValCodec.encodeSignedNumber(0)+
                        IntValCodec.encodeSignedNumber(0);

                    prev_pos.timestamp=prev_pos.timestamp+Math.round(dt/1e3)*1e3;

                    dt = k.timestamp-prev_pos.timestamp;
                    last_skipped_t=null;
                }
                raw += IntValCodec.encodeSignedNumber(Math.round(dt/1e3)) +
                    IntValCodec.encodeSignedNumber(Math.round(dlat*1e5)) +
                    IntValCodec.encodeSignedNumber(Math.round(dlon*1e5));
                prev_pos = new Position(
                {
                    timestamp:prev_pos.timestamp+Math.round(dt/1e3)*1e3,
                    coords:{
                        latitude:prev_pos.coords.latitude+Math.round(dlat*1e5)/1e5,
                        longitude:prev_pos.coords.longitude+Math.round(dlon*1e5)/1e5,
                        accuracy:0
                    }
                });
            }
        }
        return raw;
    };
};
PositionArchive.fromTks=function(encoded){
    var YEAR2000=Date.parse("2000-01-01T00:00:00Z"),
        prev_t=YEAR2000, prev_lat=0, prev_lon=0,
        enc_len = encoded.length, r, pts=new PositionArchive(), prev_enc="";
    while(enc_len>0){
        prev_enc = encoded;

        r = IntValCodec.decodeValueFromString(encoded);
        var t = prev_t + r[0]*1e3;
        encoded = r[1];

        r = IntValCodec.decodeValueFromString(encoded);
        var lat = prev_lat + r[0];
        encoded = r[1];

        r = IntValCodec.decodeValueFromString(encoded);
        var lon = prev_lon + r[0];
        encoded = r[1];

        prev_t = t;
        prev_lat = lat;
        prev_lon = lon;

        pts.add(new Position({'timestamp':t, 'coords':{'latitude':lat/1e5, 'longitude':lon/1e5, 'accuracy':0}}));

        enc_len = encoded.length;
    }
    return pts;
};
