
/*
 * Cima4U Player Controller
 * Samsung Tizen 4.0 / Chromium 56
 */

var CIMA_PLAYER = {

    currentServer: 0,
    servers: [],

    getParameter: function(name) {
        var query = window.location.search.substring(1);
        var parts = query.split("&");

        for (var i = 0; i < parts.length; i++) {
            var pair = parts[i].split("=");

            if (decodeURIComponent(pair[0]) === name) {
                return decodeURIComponent(
                    (pair[1] || "").replace(/\+/g, " ")
                );
            }
        }

        return "";
    },

    loadServers: function() {
        var i;
        var url;
        var name;

        this.servers = [];

        for (i = 1; i <= 10; i++) {
            url = this.getParameter("server" + i);

            if (!url) {
                continue;
            }

            if (url.indexOf("https://") !== 0) {
                continue;
            }

            name = this.getParameter("name" + i);

            this.servers.push({
                name: name || "Server " + i,
                url: url
            });
        }

        /* Backward compatibility with configured servers */
        if (!this.servers.length &&
            window.CIMA_CONFIG &&
            window.CIMA_CONFIG.PLAYER_SERVERS) {

            this.servers = window.CIMA_CONFIG.PLAYER_SERVERS;
        }
    },

    open: function(index) {
        if (index < 0 || index >= this.servers.length) {
            return;
        }

        var server = this.servers[index];
        var frame = document.getElementById("playerFrame");

        if (!server || !server.url || !frame) {
            return;
        }

        this.currentServer = index;
        frame.src = server.url;

        this.updateButtons();
    },

    updateButtons: function() {
        var buttons =
            document.getElementsByClassName("server-button");

        for (var i = 0; i < buttons.length; i++) {
            buttons[i].className = "server-button";

            if (i === this.currentServer) {
                buttons[i].className += " active";
            }
        }
    },

    createButtons: function() {
        var container =
            document.getElementById("serverButtons");

        if (!container) {
            return;
        }

        this.loadServers();
        container.innerHTML = "";

        if (!this.servers.length) {
            container.innerHTML =
                "No video servers were provided for this episode.";
            return;
        }

        for (var i = 0; i < this.servers.length; i++) {
            var button = document.createElement("button");

            button.className = "server-button";
            button.innerHTML = this.servers[i].name;
            button.setAttribute("data-index", i);

            button.onclick = function() {
                CIMA_PLAYER.open(
                    parseInt(
                        this.getAttribute("data-index"),
                        10
                    )
                );
            };

            container.appendChild(button);
        }

        this.open(0);

        var firstButton =
            container.getElementsByTagName("button")[0];

        if (firstButton) {
            firstButton.focus();
        }
    }
};
