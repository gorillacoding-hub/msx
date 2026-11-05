(function () {
    "use strict";

    var serversBox = document.getElementById("servers");
    var videoFrame = document.getElementById("videoFrame");
    var message = document.getElementById("message");
    var backButton = document.getElementById("back");
    var titleElement = document.getElementById("title");
    var servers = [];
    var currentServer = 0;

    function getParameter(name) {
        var query = window.location.search.substring(1);
        var parts = query.split("&");
        var i;
        var pair;
        var key;
        var value;

        for (i = 0; i < parts.length; i++) {
            pair = parts[i].split("=");
            key = pair[0] || "";
            value = pair.slice(1).join("=") || "";

            try {
                key = decodeURIComponent(key.replace(/\+/g, " "));
                value = decodeURIComponent(value.replace(/\+/g, " "));
            } catch (error) {
                /* Keep the original parameter if decoding fails. */
            }

            if (key === name) {
                return value;
            }
        }

        return "";
    }

    function isHttpUrl(value) {
        return /^https?:\/\//i.test(String(value || ""));
    }

    function setMessage(value) {
        message.innerHTML = "";
        message.appendChild(document.createTextNode(String(value || "")));
        message.style.display = "block";
    }

    function hideMessage() {
        message.style.display = "none";
    }

    function selectServer(index) {
        var buttons = serversBox.getElementsByTagName("button");
        var i;

        if (index < 0 || index >= servers.length) {
            return;
        }

        currentServer = index;

        for (i = 0; i < buttons.length; i++) {
            buttons[i].className = i === index ? "server-button active" : "server-button";
        }

        hideMessage();
        videoFrame.src = servers[index].url;
    }

    function buildServers() {
        var i;
        var button;

        serversBox.innerHTML = "";

        for (i = 1; i <= 10; i++) {
            var url = getParameter("server" + i);
            if (url && isHttpUrl(url)) {
                servers.push({
                    name: getParameter("serverName" + i) || "SERVER " + i,
                    url: url
                });
            }
        }

        if (!servers.length) {
            setMessage("No playable servers were found for this title. Go back and choose another title.");
            return;
        }

        for (i = 0; i < servers.length; i++) {
            button = document.createElement("button");
            button.type = "button";
            button.className = "server-button";
            button.tabIndex = 0;
            button.appendChild(document.createTextNode(servers[i].name));

            (function (serverIndex, currentButton) {
                currentButton.onclick = function () {
                    selectServer(serverIndex);
                };
            })(i, button);

            serversBox.appendChild(button);
        }

        selectServer(0);
    }

    function goBack() {
        videoFrame.src = "about:blank";
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = "index.html";
        }
    }

    backButton.onclick = goBack;

    document.addEventListener("keydown", function (event) {
        event = event || window.event;
        var key = event.keyCode || event.which;
        var buttons = serversBox.getElementsByTagName("button");

        if (key === 8 || key === 27 || key === 461 || key === 10009) {
            if (event.preventDefault) {
                event.preventDefault();
            }
            goBack();
            return;
        }

        if ((key === 37 || key === 39) && buttons.length) {
            var next = currentServer + (key === 37 ? -1 : 1);
            if (next >= 0 && next < buttons.length) {
                if (event.preventDefault) {
                    event.preventDefault();
                }
                buttons[next].focus();
            }
        }
    }, false);

    var title = getParameter("title");
    titleElement.innerHTML = "";
    titleElement.appendChild(document.createTextNode(title || "CIMA4U PLAYER"));
    buildServers();
}());
