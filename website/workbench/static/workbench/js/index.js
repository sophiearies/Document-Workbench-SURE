var $focused = "";
var currentFocus = "";
var checkFocus = "";

function yourFunction(){

  $focused = $(':focus');
  currentFocus = $focused.attr('id');
  checkFocus = document.getElementById("checkFocus").value;


  if ((checkFocus == "activeFalse") && ((currentFocus == "signinUsername") || (currentFocus == "signinPassword") || (currentFocus == "signupUsername") || (currentFocus == "signupPassword") || (currentFocus == "signupPasswordRepeat"))) {
    document.getElementById("form_div").style.boxShadow = "0px 0px 20px 3px rgb(0 0 0 / 90%)";
    document.getElementById("checkFocus").value = "activeTrue"
  }
  else if ((checkFocus == "activeTrue") && ((currentFocus != "signinUsername") && (currentFocus != "signinPassword") && (currentFocus != "signupUsername") && (currentFocus != "signupPassword") && (currentFocus != "signupPasswordRepeat"))) {
    document.getElementById("form_div").style.boxShadow = "0px 0px 10px 1px rgb(0 0 0 / 50%)";
    document.getElementById("checkFocus").value = "activeFalse"
  }

  setTimeout(yourFunction, 10);
}

yourFunction();

