function set_fields_for_user(id){
    if (django.jQuery("#"+id).val() == "is_operator"){
        django.jQuery("fieldset.operator").show()
    }
    else{
        django.jQuery("fieldset.operator").hide()
    }
    if (django.jQuery("#"+id).val() == "is_sadik_operator"){
        django.jQuery("fieldset.sadik_operator").show()
    }
    else{
        django.jQuery("fieldset.sadik_operator").hide()
    }
}

django.jQuery(document).ready(function(){
    set_fields_for_user("id_user_type");
    django.jQuery("#id_user_type").change(function(){
        set_fields_for_user("id_user_type")
    });
})
