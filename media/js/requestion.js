$(document).ready(function() {
    // прячем select со всем ТО, в дальнейшем модифицируем его средствами
    // jQuery, не показывая пользователю, и отправляем при подтверждении формы
    $('#id_areas').hide();
});

// центрируем карту по ТО
function center_area(id) {
    areas_all.forEach(function(area) {
        console.log(area);
        if (area.id == id) {
            try {
                map.setView([area.center[1], area.center[0]], 13);
            } catch(err) {
                console.log(err);
            }
            }
    });
}

// условный центр списка садиков
function get_center(sadik_list) {
    return sadik_list.reduce(getAverageCoords, {location: [0, 0]});
}

// добавляем выбранную ТО к areas
$(document).on("change", ".areas_all", function() {
    var id = $(this).val();
    // собственно само добавление
    $('#id_areas option').each(function() {
        if (this.value==id) {
            this.selected = true;
            areas_ids.push(parseInt(id));
            console.log(areas_ids, id);
            renderMarkers(sadik_location_data, map)
        };
    });
    // центрируем карту по ТО
    try {
        center_area(id);
    } catch(err) {
        console.log(err);
    }

    // создаем и отображаем новое поле с выбранной ТО
    $(this).prev().prev().before(' \
    <p class="field-value hidden-input"> \
        <a id="area_map_anchor" class="icon-map-marker" href="#" onclick="center_area(' + id + '); return false"></a> \
        <a id="' + id + '" class="value value-anchor" href="#" onclick="show_kidgardens(this); return false">' + $(this).children(":selected").text() + '</a> \
        <span class="caret caret-right caret-margins"></span> \
        <a href="#" onclick="del_field(this); return false"> \
        <img id="area-close" src="/static/img/remove.png"></a> \
    </p> \
    <ul class="kidgs_list unstyled"></ul>');

    // помечаем блок измененным
    var container_el = $(this).parents('.field');
    field_changed(container_el);
    // удаляем поле select
    $(this).remove();
});

// По клику на ссылку выводим еще один select с ТО
function add_area(element) {
    $(element).before(' \
    <select class="areas_all"> \
        {% for area in areas_all %} \
            <option value="{{ area.id }}">{{ area }}</option> \
        {% endfor %} \
    </select>');
}


function getAverageCoords(prev, curr, ind, arr) {
    if (arr.length == 1) {
        return arr[0].location;
    }
    if (ind < (arr.length - 1)) {
        return { location: [ prev.location[0] + curr.location[0],
                 prev.location[1] + curr.location[1] ] }
    }
    else {
        return [ (prev.location[0] + curr.location[0]) / arr.length,
                 (prev.location[1] + curr.location[1]) / arr.length ]
    }
}

// показываем детские сады под ТО
function show_kidgardens(elem) {
    var ul = $(elem).parent().next();
    var items = $(elem).parent().next().children()
    if (items.length <=0) {
        $(elem).next().removeClass("caret-right");
        for (s in sadik_location_data) {
            var sadik = sadik_location_data[s];
            if (elem.id == sadik.area_id) {
                var li = $('<li/>')
                    .text(sadik.name)
                    .appendTo(ul);
                var a = $('<a/>')
                    .attr('onclick', 'center_to_kidgdn(this); return false')
                    .attr('id', sadik.id)
                    .attr('href', '#')
                    .prependTo(li);
                var img = $('<img/>')
                    .attr('src', '/static/img/sadik-icon-gray.png')
                    .attr('height', '11')
                    .attr('width', '11')
                    .prependTo(a);
                if (areas_ids) {
                    img.attr('src', '/static/img/sadik-icon-yellow.png')
                }
                if (pref_sadiks_ids.indexOf(sadik.id) >= 0){
                    img.attr('src', '/static/img/sadik-icon.png')
                }
            }
        };
    }
    else {
        items.remove();
        $(elem).next().addClass("caret-right");
    }
}

// удаление ТО пользователем по нажатию на кнопку 'X'
function del_field(element) {
    var parent = $(element.parentElement);
    var id = parent.children('a').next().attr('id');
    $('#id_areas option').each(function() {
        if (this.value==id) {
            this.selected = false;
            var index = areas_ids.indexOf(parseInt(id));
            areas_ids.splice(index, 1);
            renderMarkers(sadik_location_data, map)
        };
    });
    $(parent).next().remove();
    $(parent).remove();
}
