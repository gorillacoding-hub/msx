(function () {
  "use strict";

  var params = new URLSearchParams(window.location.search);

  var title = params.get("title") || "MEDIA STATION X";
  var serversBox = document.getElementById("servers");
  var videoFrame = document.getElementById("videoFrame");
  var message = document.getElementById("message");
  var backButton = document.getElementById("back");

  document.getElementById("title").textContent = title;

  /*
   * Expected URL format:
   *
   * player.html?title=Episode
   * &server1=https%3A%2F%2Fexample.com%2Fembed1
   * &server2=https%3A%2F%2Fexample.com%2Fembed2
   *
   * Server URLs must be supplied by catalogue.json.
   */

  var servers = [];
  var index = 1;

  while (index <= 10) {
    var url = params.get("server" + index);

    if (url) {
      servers.push({
        name: "SERVER " + index,
        url: url
      });
    }

    index++;
  }

  function selectServer(server, button) {
    var buttons = serversBox.getElementsByTagName("button");
    var i;

    for (i = 0; i < buttons.length; i++) {
      buttons[i].className = "server";
    }

    button.className = "server active";

    message.style.display = "none";

    videoFrame.src = server.url;
  }

  function buildServers() {
    var i;
    var button;

    serversBox.innerHTML = "";

    if (!servers.length) {
      message.style.display = "block";
      message.textContent =
        "No servers were found for this episode.";
      return;
    }

    for (i = 0; i < servers.length; i++) {
      button = document.createElement("button");
      button.className = "server";
      button.textContent = servers[i].name;

      (function (server, currentButton) {
        currentButton.onclick = function () {
          selectServer(server, currentButton);
        };
      })(servers[i], button);

      serversBox.appendChild(button);
    }

    selectServer(
      servers[0],
      serversBox.getElementsByTagName("button")[0]
    );
  }

  backButton.onclick = function () {
    videoFrame.src = "about:blank";
    window.history.back();
  };

  document.addEventListener("keydown", function (event) {
    var key = event.keyCode;

    if (key === 8 || key === 461) {
      event.preventDefault();
      backButton.click();
    }
  });

  buildServers();

})();
