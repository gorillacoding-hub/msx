(function(){
"use strict";
var link=document.getElementById("open");
var status=document.getElementById("status");
function openOfficial(){
  status.textContent="Opening the official DramaLive app…";
  window.location.href="https://web.dramalive.app/";
}
link.addEventListener("click",function(e){e.preventDefault();openOfficial();});
document.addEventListener("keydown",function(e){
  var k=e.key||"";
  if(k==="Enter"||e.keyCode===13){openOfficial();}
});
/* Focus the action for TV remotes; do not force a timed redirect that can race MSX. */
try{link.focus();}catch(e){}
}());