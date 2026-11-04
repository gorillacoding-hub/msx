(function () {
    "use strict";

    
    // =========================================
    // MEDIA STATION X - CIMA4U PLAYER
    // Compatible with older Samsung Tizen browsers
    // =========================================

    var serversBox = document.getElementById("servers");
    var videoFrame = document.getElementById("videoFrame");
    var message = document.getElementById("message");
    var backButton = document.getElementById("back");
    var titleElement = document.getElementById("title");

    // -----------------------------------------
    // Read URL parameters (ES5 compatible)
    // -----------------------------------------

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
                // Keep the original value if decoding fails.
            }

            if (key === name) {
                return value;
            }
        }

        return "";
    }

    // -----------------------------------------
    // Get title
    // -----------------------------------------

    var title = getParameter("title");

    if (!title) {
        title = "MEDIA STATION X";
    }

    titleElement.textContent = title;

    // -----------------------------------------
    // Read server URLs
    // -----------------------------------------

    var servers = [];
    var index = 1;

    while (index <= 10) {
        var serverUrl = getParameter("server" + index);

        if (serverUrl) {
            servers.push({
                name: "SERVER " + index,
                url: serverUrl
            });
        }

        index++;
    }

    // -----------------------------------------
    // Select and load a server
    // -----------------------------------------

    function selectServer(server, button) {
        var buttons = serversBox.getElementsByTagName("button");
        var i;

        for (i = 0; i < buttons.length; i++) {
            buttons[i].className = "server";
        }

        button.className = "server active";

        message.style.display = "none";

        // Load the selected video host directly.
        videoFrame.src = server.url;
    }

    // -----------------------------------------
    // Create server buttons
    // -----------------------------------------

    function buildServers() {
        var i;
        var button;

        serversBox.innerHTML = "";

        if (!servers || servers.length === 0) {
            message.style.display = "block";
            message.textContent =
                "No playable servers were found for this title.";

            return;
        }

        message.style.display = "none";

        for (i = 0; i < servers.length; i++) {
            button = document.createElement("button");

            button.className = "server";
            button.textContent = servers[i].name;
            button.tabIndex = 0;

            (function (server, currentButton) {
                currentButton.onclick = function () {
                    selectServer(server, currentButton);
                };
            })(servers[i], button);

            serversBox.appendChild(button);
        }

        // Automatically load the first server.
        selectServer(
            servers[0],
            serversBox.getElementsByTagName("button")[0]
        );
    }

    // -----------------------------------------
    // Back button
    // -----------------------------------------

    backButton.onclick = function () {
        videoFrame.src = "about:blank";

        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = "index.html";
        }
    };

    // -----------------------------------------
    // Samsung TV remote BACK key support
    // -----------------------------------------

    document.addEventListener("keydown", function (event) {
        event = event || window.event;

        var key = event.keyCode || event.which;

        // Backspace / Samsung remote back key
        if (key === 8 || key === 461) {
            event.preventDefault();
            backButton.onclick();
        }
    });

    // -----------------------------------------
    // Initialize player
    // -----------------------------------------

    buildServers();

})();
