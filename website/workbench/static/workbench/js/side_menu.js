window.onload = function(){ 

  $('#btn').click(function(){
    $(".sidebar").toggleClass("active");

    if($(".sidebar" ).hasClass("active")) {
      $('.brand_custom').attr('style', function(i,s) { return (s || '') + 'color: black !important;' });
    }
    else {
      $('.brand_custom').attr('style', function(i,s) { return (s || '') + 'color: white !important;' });
    }
  });
};
