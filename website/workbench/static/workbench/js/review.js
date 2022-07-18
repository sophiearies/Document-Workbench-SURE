'use strict';

;( function ( document, window, index )
{
	var inputs = document.querySelectorAll( '.input_file' );
	Array.prototype.forEach.call( inputs, function( input )
	{
		var label	 = input.nextElementSibling,
			labelVal = label.innerHTML;

		input.addEventListener( 'change', function( e )
		{
			var fileName = '';
			if( this.files && this.files.length > 1 )
				fileName = ( this.getAttribute( 'data-multiple-caption' ) || '' ).replace( '{count}', this.files.length );
			else
				fileName = "1 document selected";

			if( fileName )
				label.querySelector( 'span' ).innerHTML = fileName;
			else
				label.innerHTML = labelVal;
		});
	});
  
}( document, window, 0 ));

var classifier_options = document.getElementsByClassName('option');
classifier_options[0].classList.add("classifier_option_selected");

for (let i = 0; i < classifier_options.length; i++) {

	classifier_options[i].addEventListener('click', () => {

    var option_number = i + 1
    document.getElementById("selected_classifier").value = option_number;

		var option_id = classifier_options[i].id

		classifier_options[i].classList.add("classifier_option_selected");

		for (let j = 0; j < classifier_options.length; j++) {

			if (classifier_options[j].id != option_id) {
				classifier_options[j].classList.remove("classifier_option_selected");
			}

		}

	})
}