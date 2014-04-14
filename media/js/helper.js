// расчитываем расстояние по двум координатам
function get_distance (lat1, lon1, lat2, lon2) {
	var R = 6371;
	var dLat = deg2rad(lat2-lat1);
	var dLon = deg2rad(lon2-lon1);
	var lat1 = deg2rad(lat1);
	var lat2 = deg2rad(lat2);

	var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
	        Math.sin(dLon/2) * Math.sin(dLon/2) * Math.cos(lat1) * Math.cos(lat2); 
	var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
	var d = R * c;
	return Math.round(d * 1000);  // converting to meters
}

function deg2rad(deg) {
  return deg * (Math.PI/180)
}

function sort_by_distance (a, b) {
	if (a.distance < b.distance)
		return -1
	if (a.distance > b.distance)
		return 1
	return 0
}

// method for repeating same string num times
String.prototype.repeat = function( num )
{
    return new Array( num + 1 ).join( this );
}

// add popup to marker
function add_popup(marker, coords) {
    marker.bindPopup('<b>'+coords["s_name"]+'</b><div>Адрес: '+coords["address"]+'</div><div>Телефон: '+coords["phone"]+'</div><a href="'+coords["url"]+'">Перейти к ДОУ</a>');
}