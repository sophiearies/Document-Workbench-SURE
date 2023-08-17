var back = document.getElementById("back");
back.addEventListener("click", goBack);

function goBack() { 
	window.history.back()
}