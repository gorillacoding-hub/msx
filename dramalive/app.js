(function(){
"use strict";
var codeInput=document.getElementById("fgCode");
var message=document.getElementById("message");
var entry=document.getElementById("entryPanel");
var playerPanel=document.getElementById("playerPanel");
var notice=document.getElementById("noticePanel");
var noticeTitle=document.getElementById("noticeTitle");
var noticeText=document.getElementById("noticeText");
var channelList=document.getElementById("channelList");
var video=document.getElementById("video");
var placeholder=document.getElementById("videoPlaceholder");
var hls=null,channels=[];

function show(el){entry.hidden=el!==entry;playerPanel.hidden=el!==playerPanel;notice.hidden=el!==notice;}
function fail(title,text){noticeTitle.textContent=title;noticeText.textContent=text;show(notice);}
function clean(s){return (s||"").replace(/&amp;/g,"&").trim();}
function parseM3U(src){
  var lines=src.replace(/^\uFEFF/,"").split(/\r?\n/),out=[],pending=null;
  lines.forEach(function(line){
    line=line.trim();if(!line)return;
    if(line.indexOf("#EXTINF:")===0){
      var name=line.substring(line.lastIndexOf(",")+1).trim()||"Unnamed channel";
      var logo=(line.match(/tvg-logo=["']([^"']*)/i)||[])[1]||"";
      var group=(line.match(/group-title=["']([^"']*)/i)||[])[1]||"";
      pending={name:name,logo:logo,group:group};
    }else if(line.charAt(0)!=="#"&&pending){
      pending.url=clean(line);out.push(pending);pending=null;
    }
  });return out;
}
function fetchPlaylist(code){
  var url="https://fgcode.org/"+encodeURIComponent(code);
  message.textContent="Loading playlist…";
  fetch(url,{method:"GET",mode:"cors",cache:"no-store"}).then(function(r){
    if(!r.ok)throw new Error("The FG Code service returned HTTP "+r.status+".");
    return r.text();
  }).then(function(text){
    if(!text||text.indexOf("#EXTM3U")===-1)throw new Error("The code did not return a standard M3U playlist.");
    var list=parseM3U(text);
    if(!list.length)throw new Error("This code returned an empty playlist. Some DramaLive codes rely on DramaLive's own catalogue service instead of containing channel entries. This standalone player cannot obtain that private catalogue from an empty M3U response.");
    channels=list;renderChannels();document.getElementById("playlistTitle").textContent="Channels ("+channels.length+")";show(playerPanel);
  }).catch(function(err){
    var detail=err&&err.message?err.message:"Unknown loading error.";
    if(/Failed to fetch|NetworkError|CORS/i.test(detail))detail="The FG Code host blocked browser access (CORS/network restriction). A secure server-side playlist relay would be required; this static TV page cannot bypass that restriction.";
    fail("Could not load FG Code",detail);
  });
}
function renderChannels(){
  channelList.innerHTML="";
  channels.forEach(function(ch,i){
    var b=document.createElement("button");b.className="channel";b.textContent=ch.name;b.setAttribute("type","button");
    b.addEventListener("click",function(){play(ch,i);});
    channelList.appendChild(b);
  });
  var first=channelList.querySelector("button");if(first)first.focus();
}
function play(ch,index){
  var buttons=channelList.querySelectorAll("button");Array.prototype.forEach.call(buttons,function(b){b.classList.remove("active");});
  if(buttons[index])buttons[index].classList.add("active");
  placeholder.hidden=true;video.hidden=false;
  if(hls){hls.destroy();hls=null;}
  video.pause();video.removeAttribute("src");video.load();
  if(window.Hls&&Hls.isSupported()&&/\\.m3u8($|\\?)/i.test(ch.url)){
    hls=new Hls();hls.loadSource(ch.url);hls.attachMedia(video);
  }else{video.src=ch.url;}
  video.play().catch(function(){});
}
function submit(){var code=codeInput.value.replace(/\\s+/g,"").trim();if(!code){message.textContent="Enter an FG Code first.";codeInput.focus();return;}fetchPlaylist(code);}
document.getElementById("continueBtn").addEventListener("click",submit);
document.getElementById("clearBtn").addEventListener("click",function(){codeInput.value="";message.textContent="Ready.";codeInput.focus();});
document.getElementById("backBtn").addEventListener("click",function(){if(hls){hls.destroy();hls=null;}video.pause();show(entry);codeInput.focus();});
document.getElementById("noticeBack").addEventListener("click",function(){show(entry);codeInput.focus();});
codeInput.addEventListener("keydown",function(e){if(e.key==="Enter"||e.keyCode===13)submit();});
document.addEventListener("keydown",function(e){
  if(e.key==="Escape"||e.keyCode===461){if(!playerPanel.hidden){document.getElementById("backBtn").click();}}
});
show(entry);
try { codeInput.blur(); document.getElementById("continueBtn").focus(); } catch(e) {}
/* Samsung TV remote navigation: do not trap arrow keys inside the text field. */
document.addEventListener("keydown",function(e){
  var k=e.key||"";
  var active=document.activeElement;
  if(entry.hidden) return;
  if(active===codeInput && (k==="ArrowDown"||e.keyCode===40)){
    e.preventDefault();document.getElementById("continueBtn").focus();return;
  }
  if((active===document.getElementById("continueBtn")||active===document.getElementById("clearBtn")) &&
     (k==="ArrowUp"||e.keyCode===38)){
    e.preventDefault();codeInput.focus();return;
  }
  if(active===document.getElementById("continueBtn") && (k==="ArrowRight"||e.keyCode===39)){
    e.preventDefault();document.getElementById("clearBtn").focus();return;
  }
  if(active===document.getElementById("clearBtn") && (k==="ArrowLeft"||e.keyCode===37)){
    e.preventDefault();document.getElementById("continueBtn").focus();return;
  }
});
}());