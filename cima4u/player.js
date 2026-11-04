
/*
 * Cima4U Player Controller
 * Samsung Tizen 4.0 / Chromium 56 compatible
 */

var CIMA_PLAYER = {

    currentServer: 0,

    servers: (window.CIMA_CONFIG &&
              window.CIMA_CONFIG.PLAYER_SERVERS)
              ? window.CIMA_CONFIG.PLAYER_SERVERS : [],

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
        var buttons = document.getElementsByClassName("server-button");

        for (var i = 0; i < buttons.length; i++) {
            buttons[i].className = "server-button";

            if (i === this.currentServer) {
                buttons[i].className += " active";
            }
        }
    },

    createButtons: function() {
        var container = document.getElementById("serverButtons");

        if (!container) {
            return;
        }

        container.innerHTML = "";

        if (!this.servers.length) {
            container.innerHTML = "No video servers configured.";
            return;
        }

        for (var i = 0; i < this.servers.length; i++) {
            var button = document.createElement("button");

            button.className = "server-button";
            button.innerHTML = this.servers[i].name;
            button.setAttribute("data-index", i);

            button.onclick = function() {
                var index = parseInt(
                    this.getAttribute("data-index"),
                    10
                );

                CIMA_PLAYER.open(index);
            };

            container.appendChild(button);
        }

        /* Automatically load the first server */
        this.open(0);

        /* Put remote focus on the first server button */
        var firstButton = container.getElementsByTagName("button")[0];

        if (firstButton) {
            firstButton.focus();
        }
    }
};
