var elements = document.getElementsByClassName('review_onclick');

for (let i = 0; i < elements.length; i++) {

	elements[i].addEventListener('click', () => {
		document.getElementById('form_onclick_' + i).submit();
	})
}