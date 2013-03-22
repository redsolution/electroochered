/* Copyright (c) 2006-2008 MetaCarta, Inc., published under the Clear BSD
 * license.  See http://svn.openlayers.org/trunk/openlayers/license.txt for the
 * full text of the license. */


/**
 * @requires OpenLayers/Layer/SphericalMercator.js
 * @requires OpenLayers/Layer/EventPane.js
 * @requires OpenLayers/Layer/FixedZoomLevels.js
 */

/**
 * Class: OpenLayers.Layer.Yandex
 * Displays maps from russian search portal Yandex.ru
 *
 * Inherits from:
 *  - <OpenLayers.Layer.SphericalMercator>
 *  - <OpenLayers.Layer.EventPane>
 *  - <OpenLayers.Layer.FixedZoomLevels>
 */
OpenLayers.Layer.Yandex = OpenLayers.Class(
    OpenLayers.Layer.EventPane,
    OpenLayers.Layer.FixedZoomLevels, {

    /**
     * Constant: MIN_ZOOM_LEVEL
     * {Integer} 1
     */
    MIN_ZOOM_LEVEL: 1,

    /**
     * Constant: MAX_ZOOM_LEVEL
     * {Integer} 17
     */
    MAX_ZOOM_LEVEL: 17,

    /**
     * Constant: RESOLUTIONS
     * {Array(Float)} Hardcode these resolutions so that they are more closely
     *                tied with the standard wms projection
     */
    RESOLUTIONS: [
        1.40625,
        0.703125,
        0.3515625,
        0.17578125,
        0.087890625,
        0.0439453125,
        0.02197265625,
        0.010986328125,
        0.0054931640625,
        0.00274658203125,
        0.001373291015625,
        0.0006866455078125,
        0.00034332275390625,
        0.000171661376953125,
        0.0000858306884765625,
        0.00004291534423828125,
        0.00002145767211914062,
        0.00001072883605957031,
        0.00000536441802978515
    ],

	attribution:'',

    /**
     * APIProperty: type
     * {YMaps.Type}
     */
    type: null,

    /**
     * APIProperty: sphericalMercator
     * {Boolean} Should the map act as a mercator-projected map? This will
     *     cause all interactions with the map to be in the actual map
     *     projection, which allows support for vector drawing, overlaying
     *     other maps, etc.
     */
    sphericalMercator: false,

    /**
     * Property: dragObject
     */
    dragObject: null,

    /**
     * Constructor: OpenLayers.Layer.Yandex
     *
     * Parameters:
     * name - {String} A name for the layer.
     * options - {Object} An optional object whose properties will be set
     *     on the layer.
     */
    initialize: function(name, options) {
        OpenLayers.Layer.EventPane.prototype.initialize.apply(this, arguments);
        OpenLayers.Layer.FixedZoomLevels.prototype.initialize.apply(this,
                                                                    arguments);
        this.addContainerPxFunction();
        if (this.sphericalMercator) {
            OpenLayers.Util.extend(this, OpenLayers.Layer.SphericalMercator);
            this.initMercatorParameters();
        }
    },

    /**
     * Method: loadMapObject
     * Load the YMaps and register appropriate event listeners. If we can't
     * load YMaps, then display a warning message.
     *
     * To load YMaps import yanedx javascript to your html page use the following statment in <head>
     * <script src="http://api-maps.yandex.ru/1.0/?key=YOUR_KEY" type="text/javascript"></script>
     */
    loadMapObject:function() {
        try {            
            this.mapObject = new YMaps.Map( this.div );
            this.mapObject.disableDragging();
            this.dragPanMapObject = null;
        } catch (e) {
            OpenLayers.Console.error(e);
        }

    },

    /**
     * APIMethod: setMap
     * Overridden from EventPane because if a map type has been specified,
     *     we need to attach a listener for the first moveend -- this is how
     *     we will know that the map has been centered. Only once the map has
     *     been centered is it safe to change the gmap object's map type.
     *
     * Parameters:
     * map - {<OpenLayers.Map>}
     */
    setMap: function(map) {
        OpenLayers.Layer.EventPane.prototype.setMap.apply(this, arguments);

        if (this.type != null) {
            this.map.events.register("moveend", this, this.setMapType);
        }
    },

    /**
     * Method: setMapType
     * The map has been centered, and a map type was specified, so we
     *     set the map type on the gmap object, then unregister the listener
     *     so that we dont keep doing this every time the map moves.
     */
    setMapType: function() {
        if (this.mapObject.getCenter() != null) {
            this.mapObject.setType(this.type);//setType is function of YMaps.Map
            this.map.events.unregister("moveend", this, this.setType);
        }
    },

    /**
     * APIMethod: onMapResize
     *
     * Parameters:
     * evt - {Event}
     */
    onMapResize: function() {
        if(this.visibility) {
            this.mapObject.redraw();
        } else {
            this.windowResized = true;
        }
    },

    /**
     * Method: display
     * Hide or show the layer
     *
     * Parameters:
     * display - {Boolean}
     */
    display: function(display) {
        OpenLayers.Layer.EventPane.prototype.display.apply(this, arguments);
        if(this.div.style.display == "block" && this.windowResized) {
            this.mapObject.redraw();
            this.windowResized = false;
        }
    },

/* TRANSLATION: MapObject Bounds <-> OpenLayers.Bounds */
    /**
     * APIMethod: getOLBoundsFromMapObjectBounds
     *
     * Parameters:
     * moBounds - {Object}
     *
     * Returns:
     * {<OpenLayers.Bounds>} An <OpenLayers.Bounds>, translated from the
     *                       passed-in MapObject Bounds.
     *                       Returns null if null value is passed in.
     */
    getOLBoundsFromMapObjectBounds: function(moBounds) {
        var olBounds = null;
        if (moBounds != null) {
            var sw = moBounds.getSouthWest();
            var ne = moBounds.getNorthEast();
            if (this.sphericalMercator) {
                sw = this.forwardMercator(sw.lng(), sw.lat());
                ne = this.forwardMercator(ne.lng(), ne.lat());
            } else {
                sw = new OpenLayers.LonLat(sw.lng(), sw.lat());
                ne = new OpenLayers.LonLat(ne.lng(), ne.lat());
            }
            olBounds = new OpenLayers.Bounds(sw.lon,
                                             sw.lat,
                                             ne.lon,
                                             ne.lat );
        }
        return olBounds;
    },

    /**
     * APIMethod: getMapObjectBoundsFromOLBounds
     *
     * Parameters:
     * olBounds - {<OpenLayers.Bounds>}
     *
     * Returns:
     * {Object} A MapObject Bounds, translated from olBounds
     *          Returns null if null value is passed in
     */
    getMapObjectBoundsFromOLBounds: function(olBounds) {
        var moBounds = null;
        if (olBounds != null) {
            var sw = this.sphericalMercator ?
              this.inverseMercator(olBounds.bottom, olBounds.left) :
              new OpenLayers.LonLat(olBounds.bottom, olBounds.left);
            var ne = this.sphericalMercator ?
              this.inverseMercator(olBounds.top, olBounds.right) :
              new OpenLayers.LonLat(olBounds.top, olBounds.right);
            moBounds = new YMaps.GeoBounds (new YMaps.GeoPoint(sw.lon, sw.lat),
                                         new YMaps.GeoPoint(ne.lon, ne.lat));
        }
        return moBounds;
    },

    /**
     * Method: addContainerPxFunction
     * Hack-on function because GMAPS does not give it to us
     *
     * Parameters:
     * geoPoint - {GLatLng}
     *
     * Returns:
     * {Point} A YMaps.Point (x,y) specifying YMaps.GeoPoint (geocoordinates) translated into "Container" pixel position
     */
    addContainerPxFunction: function() {
        if ((typeof YMaps.Map != "undefined") && !YMaps.Map.prototype.fromLatLngToContainerPixel) {

            YMaps.Map.prototype.fromLatLngToContainerPixel = function(geoPoint) {
                // first we translate into "DivPixel"
                var divPoint = this.fromLatLngToDivPixel(geoPoint);
                // locate the sliding "Div" div
                var div = this.getContainer().firstChild.firstChild;
                //adjust by the offset of "Div"
                divPoint.x += div.offsetLeft;
                divPoint.y += div.offsetTop;
                return divPoint;
            };
        }
    },

    /**
     * APIMethod: getWarningHTML
     *
     * Returns:
     * {String} String with information on why layer is broken, how to get
     *          it working.
     */
    getWarningHTML:function() {
        return OpenLayers.i18n("yandexWarning");
    },


    /************************************
     *                                  *
     *   MapObject Interface Controls   *
     *                                  *
     ************************************/


  // Get&Set Center, Zoom

    /**
     * APIMethod: setMapObjectCenter
     * Set the mapObject to the specified center and zoom
     *
     * Parameters:
     * center - {Object} MapObject LonLat format
     * zoom - {int} MapObject zoom format
     */
    setMapObjectCenter: function(center, zoom) {
        this.mapObject.setCenter(center, zoom);
    },

    /**
     * APIMethod: dragPanMapObject
     *
     * Parameters:
     * dX - {Integer}
     * dY - {Integer}
     */
    dragPanMapObject: function(dX, dY) {
        this.dragObject.moveBy(new YMaps.Size(-dX, dY));
    },

    /**
     * APIMethod: getMapObjectCenter
     *
     * Returns:
     * {Object} The mapObject's current center in Map Object format
     */
    getMapObjectCenter: function() {
        return this.mapObject.getCenter();
    },

    /**
     * APIMethod: getMapObjectZoom
     *
     * Returns:
     * {Integer} The mapObject's current zoom, in Map Object format
     */
    getMapObjectZoom: function() {
        return this.mapObject.getZoom();
    },


  // LonLat <> Pixel Translation

    /**
     * APIMethod: getMapObjectLonLatFromMapObjectPixel
     *
     * Parameters:
     * moPixel - {Object} MapObject Pixel format
     *
     * Returns:
     * {Object} MapObject LonLat translated from MapObject Pixel
     */
    getMapObjectLonLatFromMapObjectPixel: function(moPixel) {
        //return this.mapObject.fromContainerPixelToLatLng(moPixel);
        return this.mapObject.converter.mapPixelsToCoordinates(moPixel);
    },

    /**
     * APIMethod: getMapObjectPixelFromMapObjectLonLat
     *
     * Parameters:
     * moLonLat - {Object} MapObject LonLat format
     *
     * Returns:
     * {Object} MapObject Pixel transtlated from MapObject LonLat
     */
    getMapObjectPixelFromMapObjectLonLat: function(moLonLat) {
        return this.mapObject.converter.coordinatesToMapPixels(moLonLat);
    },


  // Bounds

    /**
     * APIMethod: getMapObjectZoomFromMapObjectBounds
     *
     * Parameters:
     * moBounds - {Object} MapObject Bounds format
     *
     * Returns:
     * {Object} MapObject Zoom for specified MapObject Bounds
     */
    getMapObjectZoomFromMapObjectBounds: function(moBounds) {
        this.mapObject.setBounds(moBounds);
        return this.mapObject.getZoom();
    },

    /************************************
     *                                  *
     *       MapObject Primitives       *
     *                                  *
     ************************************/


  // LonLat

    /**
     * APIMethod: getLongitudeFromMapObjectLonLat
     *
     * Parameters:
     * moLonLat - {Object} MapObject LonLat format
     *
     * Returns:
     * {Float} Longitude of the given MapObject LonLat
     */
    getLongitudeFromMapObjectLonLat: function(moLonLat) {
        return this.sphericalMercator ?
          this.forwardMercator(moLonLat.getLng(), moLonLat.getLat()).lon :
          moLonLat.getLng();
    },

    /**
     * APIMethod: getLatitudeFromMapObjectLonLat
     *
     * Parameters:
     * moLonLat - {Object} MapObject LonLat format
     *
     * Returns:
     * {Float} Latitude of the given MapObject LonLat
     */
    getLatitudeFromMapObjectLonLat: function(moLonLat) {
        var lat = this.sphericalMercator ?
          this.forwardMercator(moLonLat.getLng(), moLonLat.getLat()).lat :
          moLonLat.getLat();
        return lat;
    },

    /**
     * APIMethod: getMapObjectLonLatFromLonLat
     *
     * Parameters:
     * lon - {Float}
     * lat - {Float}
     *
     * Returns:
     * {Object} MapObject LonLat built from lon and lat params
     */
    getMapObjectLonLatFromLonLat: function(lon, lat) {
        var gLatLng;
        if(this.sphericalMercator) {
            var lonlat = this.inverseMercator(lon, lat);
            gLatLng = new YMaps.GeoPoint(lonlat.lon, lonlat.lat);
        } else {
            gLatLng = new YMaps.GeoPoint(lon, lat);
        }
        return gLatLng;
    },

  // Pixel

    /**
     * APIMethod: getXFromMapObjectPixel
     *
     * Parameters:
     * moPixel - {Object} MapObject Pixel format
     *
     * Returns:
     * {Integer} X value of the MapObject Pixel
     */
    getXFromMapObjectPixel: function(moPixel) {
        return moPixel.x;
    },

    /**
     * APIMethod: getYFromMapObjectPixel
     *
     * Parameters:
     * moPixel - {Object} MapObject Pixel format
     *
     * Returns:
     * {Integer} Y value of the MapObject Pixel
     */
    getYFromMapObjectPixel: function(moPixel) {
        return moPixel.y;
    },

    /**
     * APIMethod: getMapObjectPixelFromXY
     *
     * Parameters:
     * x - {Integer}
     * y - {Integer}
     *
     * Returns:
     * {Object} MapObject Pixel from x and y parameters
     */
    getMapObjectPixelFromXY: function(x, y) {
        return new YMaps.Point(x, y);
    },

    CLASS_NAME: "OpenLayers.Layer.Yandex"
});
