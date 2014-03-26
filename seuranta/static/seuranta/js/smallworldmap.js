/*
 * @version 2014-03-22 smallWorld
 * @author Raphael Stefanini
 * Small World Library
 */

Point = (function(){
    function P(x, y){
        this.x = x;
        this.y = y;
    }
    return P;
})();

LatLon = (function(){
    var p = "prototype",
    m = Math,
    mcos = m.cos,
    msin = m.sin,
    mpow = m.pow,
    msqr = m.sqrt;
    function L(lat, lon){
        this.lat = lat;
        this.lon = lon;
    }
    L[p].distance = function(latlon){
        var C = m.PI/180,
        dlat = this.lat - latlon.lat,
        dlon = this.lon - latlon.lon,
        a = mpow(msin(C*dlat / 2), 2) + mcos(C*this.lat) * mcos(C*latlon.lat) * mpow(msin(C*dlon / 2), 2);
        return 12756274 * m.atan2(msqr(a), msqr(1 - a));
    };
    return L;
})();

SpheroidProjection = (function(){
    var p = "prototype",
    m = Math,
    pi = m.PI,
    _180 = 180.0,
    rad = 6378137,
    originShift = pi * rad,
    pi_180 = pi/_180;
    function S(){}
    S[p].LatLonToMeters = function(latlon){
        return new Point(
            latlon.lon*rad*pi_180,
            m.log(m.tan((90+latlon.lat)*pi_180/2))*rad
        );
    },
    S[p].MetersToLatLon = function(mxy){
        return new LatLon(
            (2*m.atan(m.exp(mxy.y/rad))-pi/2)/pi_180,
            mxy.x/rad/pi_180
        );
    },
    S[p].resolution = function(zoom){
        return (2 * originShift) / (256 * m.pow(2, zoom));
    },
    S[p].zoomForPixelSize = function(pixelSize ){
        for(i=0; i<30; i++){
            if(pixelSize > resolution(i)){
                return m.max(i-1,0);
            }
        }
    },
    S[p].pixelsToMeters = function(px, py, zoom){
        var res = resolution( zoom ),
            mx = px * res - originShift,
            my = py * res - originShift;
        return new Point(mx, my);
    };
    return S;
})();

SmallWorld=(function(){
    var p = "prototype",
    m = Math,
    mpow = m.pow,
    method_callback = function (object, method) {
        return function() {return method.apply(object, arguments);};
    },
    proj = new SpheroidProjection(),
    solveAffine = function (r1, s1, t1, r2, s2, t2, r3, s3, t3) {
        var a = (((t2 - t3) * (s1 - s2)) - ((t1 - t2) * (s2 - s3)))
            / (((r2 - r3) * (s1 - s2)) - ((r1 - r2) * (s2 - s3))),
        b = (((t2 - t3) * (r1 - r2)) - ((t1 - t2) * (r2 - r3)))
            / (((s2 - s3) * (r1 - r2)) - ((s1 - s2) * (r2 - r3))),
        c = t1 - (r1 * a) - (s1 * b);
        return [a, b, c];
    },
    derive = function (A, B) {
        var a0 = B[0], a1 = A[0],
        b0 = B[1], b1 = A[1],
        c0 = B[2], c1 = A[2],
        e = 1e-15, x, y;
        a0.x-=e;a0.y+=e;b0.x+=e;b0.y-=e;a1.x+=e;a1.y+=e;b1.x-=e;b1.y-=e;
        x = solveAffine(a0.x, a0.y, a1.x, b0.x, b0.y, b1.x, c0.x, c0.y, c1.x);
        y = solveAffine(a0.x, a0.y, a1.y, b0.x, b0.y, b1.y, c0.x, c0.y, c1.y);
        return [x[0], x[1], x[2], y[0], y[1], y[2]];
    };
    function M(target, map_url, cal_pts, bg_url, overlay_img_url, on_loaded, extra_border){
        var cal_pts_meter = [
                proj.LatLonToMeters(cal_pts[0]),
                proj.LatLonToMeters(cal_pts[1]),
                proj.LatLonToMeters(cal_pts[2])
            ],
            map_image = new Image();
        
        this.coordsToXy = derive(cal_pts, cal_pts_meter);
        this.xyToCoords = derive(cal_pts_meter, cal_pts);
        
        this.map_w = 0;
        this.map_h = 0;
        
        map_image.onload = method_callback(this, function() {
            this.map_w = map_image.width;
            this.map_h = map_image.height;
            this.draw(target);
        });
        map_image.src = map_url;
        this.map_url = map_url;
        this.on_loaded = on_loaded || function(){};
        this.bg_url = bg_url;
        this.overlay_img_url = overlay_img_url;
        this.extra_border = typeof extra_border == 'undefined'?true:extra_border;
    }
    M[p].draw = function(el_id){
        var el = $("#"+el_id);
        if(this.bg_url){
            el.css("background", "url('"+this.bg_url+"') #cceeff");
        }else{
            el.css("background", "#cceeff");
        }
        el.css("cursor", "pointer");

        this.view_W = el.width();
        this.view_H = el.height();
        this.current_zoom = 0;

        this.view_x = 0;
        this.view_y = 0;
        this.current_zoom = 0;
        this.start_drag_x = 0;
        this.start_drag_y = 0;
        this.markers = [];
        this.routes = [];
        this.el = el;
        this.paper = Raphael(el_id, this.view_W, this.view_H);
        
        // add a border
        if(this.extra_border){
            this.paper.rect(-10, -10, this.map_w+20, this.map_h+20).attr({fill:"#FFF"}); 
        }
        this.map_img = this.paper.image(this.map_url, 0, 0, this.map_w, this.map_h);

        if(this.overlay_img_url){
            if(this.extra_border){
                this.paper.image(this.overlay_img_url, -10, -10, this.map_w+20, this.map_h+20);
            }else{
                this.paper.image(this.overlay_img_url, 0, 0, this.map_w, this.map_h);
            }
        }
        
        this.mask = this.paper.rect(0, 0, this.view_W, this.view_H).attr({fill:"#FFF", opacity:0}).drag(
            method_callback(this, function(dx, dy, x, y){
                this.el.css("cursor", "move");
                this.view_x = this.start_drag_x-dx/mpow(2, this.current_zoom);
                this.view_y = this.start_drag_y-dy/mpow(2, this.current_zoom);
                this.paper.setViewBox(this.view_x, this.view_y, this.view_W, this.view_H, false);
                this.mask.attr({x:this.view_x, y:this.view_y})
            }),
            method_callback(this, function(x, y){
                this.start_drag_x = this.view_x;
                this.start_drag_y = this.view_y;
            }),
            method_callback(this, function(x, y){
                this.el.css("cursor", "pointer");
            })
        );
        $(window).bind("resize", method_callback(this, M[p]._on_resize));
        this.on_loaded();
    };
    M[p]._on_resize = function(){
        this.paper.setSize(this.el.width(), this.el.height());
        this._on_zoom();
    };
    M[p].zoom_in = function(){
        var f = mpow(2, this.current_zoom)
        this.view_x += this.el.width()/f/4;//  |   [  ]   |
        this.view_y += this.el.height()/f/4;// |  [    ]  |
        this.current_zoom++;
        this._on_zoom();
    };
    M[p].zoom_out = function(){
        this.current_zoom--;
        var f = mpow(2, this.current_zoom)
        this.view_x -= this.el.width()/f/4;
        this.view_y -= this.el.height()/f/4;
        this._on_zoom();
    };
    M[p]._on_zoom = function(){
        var f = mpow(2, this.current_zoom);
        
        this.view_W = this.el.width()/f;
        this.view_H = this.el.height()/f;
        
        this.mask.attr({
            x:this.view_x,
            y:this.view_y, 
            width:this.view_W, 
            height:this.view_H
        });
        
        this.paper.setViewBox(this.view_x, this.view_y, this.view_W, this.view_H, false);

        for(i=0;i<this.markers.length;i++){
            this.markers[i]._redraw();
        }
    };
    M[p].LatLonToMapXY = function(latlon){
        var mxy = proj.LatLonToMeters(latlon),
            x = mxy.x*this.coordsToXy[0]+mxy.y*this.coordsToXy[1]+this.coordsToXy[2],
            y = mxy.x*this.coordsToXy[3]+mxy.y*this.coordsToXy[4]+this.coordsToXy[5];
        return new Point(x, y);
    };
    M[p].MapXYToLatLon = function(xy){
        var x, y;
        x = xy.x*this.xyToCoords[0]+xy.y*this.xyToCoords[1]+this.xyToCoords[2];
        y = xy.x*this.xyToCoords[3]+xy.y*this.xyToCoords[4]+this.xyToCoords[5];
        return proj.MetersToLatLon(new Point(x, y));
    };
    M[p].ViewPortXYToLatLon = function(xy){
        var x, y;
        x = (xy.x/mpow(2, this.current_zoom) + this.view_x);
        y = (xy.y/mpow(2, this.current_zoom) + this.view_y);
        return this.MapXYToLatLon(new Point(x,y));
    };
    M[p].center = function(latlon){
        var xy = this.LatLonToMapXY(latlon);
        this.view_x = xy.x-this.view_W/2;
        this.view_y = xy.y-this.view_H/2;
        this.paper.setViewBox(this.view_x, this.view_y, this.view_W, this.view_H, false);
    };
    function K(latlon, color, text){
        this.latlon = latlon;
        this.color = color || "#09F";
        this.text = text || "";
        this.size = 9;
    }
    K[p].draw = function(map){
        var xy = map.LatLonToMapXY(this.latlon), c = this.color;
        this.map = map;
        this.circle = map.paper.circle(xy.x, xy.y, this.size).attr({"stroke":c, opacity:.75, "stroke-width":4});
        this.name = map.paper.text(xy.x+13, xy.y+13, this.text).attr({"font-size":"20px", "fill":c, "stroke":c, "text-anchor":"start"});
        map.markers.push(this);
        map.mask.toFront();
    };
    K[p].move = function(latlon){
        this.latlon = latlon;
        this._redraw();
    };
    K[p]._redraw = function(){
        var xy = this.map.LatLonToMapXY(this.latlon),
        s=mpow(2, this.map.current_zoom);
        this.circle.attr({
            cx:xy.x,
            cy:xy.y,
            r:this.size/s
        });
        this.name.attr({
            x:xy.x+15/s,
            y:xy.y+15/s,
            "font-size":(20/s)+"px"
        });
    };
    K[p].show = function(coords){
        this.name.show();
        this.circle.show();
    };
    K[p].hide = function(coords){
        this.name.hide();
        this.circle.hide();
    };
    function P(coords, color){
        this.coords = coords;
        this.color = color || "#09F";
        this.width = 4;
    }
    P[p].draw = function(map){
        this.map = map;
        var path_val="M", i, xy;
        for(i=0; i<this.coords.length; i++){
            if(i>0){
                path_val+="L";
            }
            xy = map.LatLonToMapXY(this.coords[i]);
            path_val+=[xy.x,xy.y].join(" ");
        }
        this.path = map.paper.path(path_val).attr({stroke:this.color, opacity:.75, "stroke-width":this.width, "stroke-linejoin":"round"});
        map.routes.push(this);
        map.mask.toFront();
    };
    P[p].set_new_path = function(coords){
        var path_val="M", xy;
        this.coords = coords;
        for(i=0;i<coords.length;i++){
            if(i>0){
                path_val+="L";
            }
            xy=this.map.LatLonToMapXY(coords[i]);
            path_val+=[xy.x,xy.y].join(" ");
            this.path.attr({path:path_val});
        }
    };
    P[p].show = function(coords){
        this.path.show();
    };
    P[p].hide = function(coords){
        this.path.hide();
    };
    return {Map:M, Marker:K, Route:P};
})();

