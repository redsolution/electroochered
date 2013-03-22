{% extends "gis/admin/openlayers.js" %}
{% load sadiki_core_tags %}
{% block base_layer %}
    {% load_settings %}
    new OpenLayers.Layer.OSM("OSM", {{ settings.OPENLAYERS_URLS|safe }});
{% endblock %}
