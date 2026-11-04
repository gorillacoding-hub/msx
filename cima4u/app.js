(function () {
    "use strict";

    var browse = document.getElementById("browse");
    var status = document.getElementById("status");

    if (!browse) {
        return;
    }

    browse.addEventListener("click", function () {
        status.innerHTML = "Opening Cima4U...";
    });

    /*
     * Keep the real website URL on the link.
     * Do not intercept browsing with an iframe.
     * The TV browser opens the actual website.
     */

}());
