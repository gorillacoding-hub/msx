
/*
 * Cima4U Original Player
 * Samsung Tizen 4.0 / Chromium 56
 */

(function () {
    "use strict";

    function getParameter(name) {
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
    }

    function goBack() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = "index.html";
        }
    }

    window.goBack = goBack;

    var episodeUrl = getParameter("episode");
    var player = document.getElementById("player");
    var message = document.getElementById("message");

    if (!episodeUrl) {
        message.innerHTML = "No episode URL was provided.";
        player.style.display = "none";
        return;
    }

    if (episodeUrl.indexOf("https://") !== 0) {
        message.innerHTML = "Invalid episode URL.";
        player.style.display = "none";
        return;
    }

    player.onload = function () {
        message.style.display = "none";
    };

    player.onerror = function () {
        message.innerHTML =
            "The original player could not be loaded.";
    };

    player.src = episodeUrl;
})();
