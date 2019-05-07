if (!$) {
    $ = django.jQuery;
}
$.fx.off = false; 
$(function(){
	//Hide staff payment options if the event isn't enforcing staff auth tokens.  
	//TODO: Abstract this for general use.  
	$('form').delegate('#id_useAuthToken','change',function() {
        if(this.checked) {
            $('#id_staffEventRegistration').parent().parent().stop(true,true).slideDown(200); 
			$('#id_staffEventRegistration').attr('checked',false); 
        }
		else{
			$('#id_staffEventRegistration').parent().parent().stop(true,true).slideUp(200); 
		}
        $('#textbox1').val(this.checked);        
    });
});