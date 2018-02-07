odoo.define('web_map.FieldMap', function(require) {
"use strict";

var core = require('web.core');
var form_common = require('web.form_common');

var FieldMap = form_common.AbstractField.extend({
    template: 'FieldMap',
    start: function() {
        var self = this;
        var map = self.$('#google_map').prevObject[2];
        console.log(self.$('#google_map'));
        console.log(map);
        this.map = new google.maps.Map(map, {
            center: {lat:0,lng:0},
            zoom: 0,
            disableDefaultUI: true,
        });
         // Create the search box and link it to the UI element.
        var input = self.$('#pac-input').prevObject[0];

        console.log(input);
        var searchBox = new google.maps.places.SearchBox(input);
        this.map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);

        // Bias the SearchBox results towards current map's viewport.
        // this.map.addListener('bounds_changed', function() {
        //   searchBox.setBounds(this.map.getBounds());
        // });


        var markers = [];
        searchBox.addListener('places_changed', function() {
            console.log('places_changed');
            var places = searchBox.getPlaces();

              if (places.length == 0) {
                return;
              }

              // Clear out the old markers.
              markers.forEach(function(marker) {
                marker.setMap(null);
              });
              markers = [];

              // For each place, get the icon, name and location.
              var bounds = new google.maps.LatLngBounds();
              places.forEach(function(place) {
                if (!place.geometry) {
                  console.log("Returned place contains no geometry");
                  return;
                }
                var icon = {
                  url: place.icon,
                  size: new google.maps.Size(71, 71),
                  origin: new google.maps.Point(0, 0),
                  anchor: new google.maps.Point(17, 34),
                  scaledSize: new google.maps.Size(25, 25)
                };

                // Create a marker for each place.
                markers.push(new google.maps.Marker({
                  map: self.map,
                  icon: icon,
                  title: place.name,
                  position: place.geometry.location
                }));

                if (place.geometry.viewport) {
                  // Only geocodes have viewport.
                  bounds.union(place.geometry.viewport);
                } else {
                  bounds.extend(place.geometry.location);
                }
              });
              self.map.fitBounds(bounds);
        });
        this.marker = new google.maps.Marker({
            position: {lat:0,lng:0},
        });

        this.map.addListener('click', function(e) {
            if(!self.get("effective_readonly") && self.marker.getMap() == null) {
                self.marker.setPosition(e.latLng);
                self.marker.setMap(self.map);
                self.internal_set_value(JSON.stringify({position:self.marker.getPosition(),zoom:self.map.getZoom()}));
            }
        });
        this.map.addListener('zoom_changed', function() {
            if(!self.get("effective_readonly") && self.marker.getMap()) {
                self.internal_set_value(JSON.stringify({position:self.marker.getPosition(),zoom:self.map.getZoom()}));
            }
        });
        this.marker.addListener('click', function() {
            if(!self.get("effective_readonly")) {
                self.marker.setMap(null);
                self.internal_set_value(false);
            }
        });
        this.marker.addListener('dragend', function() {
            self.internal_set_value(JSON.stringify({position:self.marker.getPosition(),zoom:self.map.getZoom()}));
        });
        this.getParent().$('a[data-toggle="tab"]').on('shown.bs.tab', function() {
            self.trigger('resize');
        });
        this.getParent().on('attached', this.getParent(), function() {
            self.trigger('resize');
        });
        this.on('change:effective_readonly', this, this.update_mode);
        this.on('resize', this, this._toggle_label);
        this.update_mode();
        this._super();
    },
    render_value: function() {
        if(this.get_value()) {
            this.marker.setPosition(JSON.parse(this.get_value()).position);
            this.map.setCenter(JSON.parse(this.get_value()).position);
            this.map.setZoom(JSON.parse(this.get_value()).zoom);
            this.marker.setMap(this.map);
        } else {
            this.marker.setPosition({lat:0,lng:0});
            this.map.setCenter({lat:0,lng:0});
            this.map.setZoom(2);
            this.marker.setMap(null);
        }
    },
    update_mode: function() {
        if(this.get("effective_readonly")) {
            this.map.setOptions({
                disableDoubleClickZoom: true,
                draggable: false,
                scrollwheel: false,
            });
            this.marker.setOptions({
                draggable: false,
                cursor: 'default',
            });
        } else {
            this.map.setOptions({
                disableDoubleClickZoom: false,
                draggable: true,
                scrollwheel: true,
            });
            this.marker.setOptions({
                draggable: true,
                cursor: 'pointer',
            });
        }
    },
    _toggle_label: function() {
        this._super();
        google.maps.event.trigger(this.map, 'resize');
        if (!this.no_rerender) {
            this.render_value();
        }
    },
});

core.form_widget_registry.add('map', FieldMap);

return {
    FieldMap: FieldMap,
};

});