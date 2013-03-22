$(document).ready(function() {
//    $.datepicker.setDefaults($.datepicker.regional["ru"]);
    $.datepicker.setDefaults({showOn: "both",
        buttonImage: "/static/img/calendar.gif",
        buttonImageOnly: true,
        changeMonth: true,
        changeYear: true,
        dateFormat: 'dd-mm-yy'
    });
});