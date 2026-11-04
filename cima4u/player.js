
/*
 * Cima4U Player Controller
 * Samsung Tizen 4.0 compatible
 */

var CIMA_PLAYER = {

    currentServer: 0,

    servers: CIMA_CONFIG.PLAYER_SERVERS,

    open: function(index) {
        if (index < 0 || index >= this.servers.length) {
            return;
        }

        this.currentServer = index;

        var frame = document.getElementById("playerFrame");

        if (frame) {
            frame.src = this.servers[index].url;
        }

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

        for (var i = 0; i < this.servers.length; i++) {
            var button = document.createElement("button");

            button.className = "server-button";
            button.innerHTML = this.servers[i].name;

            button.setAttribute("data-index", i);

            button.onclick = function() {
                CIMA_PLAYER.open(
                    parseInt(this.getAttribute("data-index"), 10)
                );
            };

            container.appendChild(button);
        }

        this.updateButtons();
    }
};
