
/*
 * Cima4U Remote Navigation
 * Samsung Tizen 4.0 / Chromium 56
 */

var CIMA_REMOTE = {

    focusIndex: 0,

    init: function() {
        document.addEventListener("keydown", this.handle.bind(this));
    },

    handle: function(event) {
        var key = event.keyCode;
        var buttons = document.getElementsByClassName("server-button");

        if (!buttons.length) {
            return;
        }

        if (key === 37) {
            this.focusIndex--;
        } else if (key === 39) {
            this.focusIndex++;
        } else if (key === 13) {
            buttons[this.focusIndex].click();
            event.preventDefault();
            return;
        } else {
            return;
        }

        if (this.focusIndex < 0) {
            this.focusIndex = 0;
        }

        if (this.focusIndex >= buttons.length) {
            this.focusIndex = buttons.length - 1;
        }

        buttons[this.focusIndex].focus();
        event.preventDefault();
    }
};

window.onload = function() {
    CIMA_PLAYER.createButtons();
    CIMA_REMOTE.init();
};
