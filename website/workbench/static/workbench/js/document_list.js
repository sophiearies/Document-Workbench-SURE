const bindDocumentEventListeners = () => {
	var elements = document.getElementsByClassName('review_onclick');
	const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
	for (let i = 0; i < elements.length; i++) {
		elements[i].addEventListener('click', function() {
			$.ajax({
				method: 'POST',
				headers: {'X-CSRFToken': csrftoken},
				mode: 'same-origin',
				data: `selected_document_id=${this.dataset.documentId}`,
			}).done((html) => {
				document.open();
				document.write(html);
				document.close();
			});
			// document.getElementById('form_onclick_' + i).submit();
		});
	}
}
$(document).ready(function () {
	var table = $('#myTable').DataTable();
  
	bindDocumentEventListeners();
	$('#myTable').on('draw.dt', bindDocumentEventListeners);
  
	$('#myTable').on('click', 'tr', function () {
	  var id = table.row(this).id();
  
	  console.log('Clicked row id ' + id);
	});
  });