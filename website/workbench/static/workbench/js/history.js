var popup1 = document.getElementById("popup_bg")
var openPopup1 = document.getElementById("popup_form_open")
var closePopup1 = document.getElementById('popup_form_close')
var closePopup2 = document.getElementById('popup_form_close_x')

openPopup1.addEventListener('click', () => {
	popup1.style.display = "block";
})

closePopup1.addEventListener('click', () => {
	popup1.style.display = "none";
})

closePopup2.addEventListener('click', () => {
	popup1.style.display = "none";
})

var elements = document.getElementsByClassName('review_onclick');

for (let i = 0; i < elements.length; i++) {

	elements[i].addEventListener('click', () => {

    var review_id = document.getElementById('review_onclick_' + i).value;
    document.getElementById("review_id_input").value = review_id;
    // popup1.style.display = "none";
    
		document.getElementById('history_form').submit();
	})
}