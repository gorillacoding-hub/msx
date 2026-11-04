
/*
 * Cima4U TV configuration
 * Samsung Tizen 4.0 / Chromium 56
 */

var CIMA_CONFIG = {

    SITE: "https://cimafu.live",

    PLAYER_SERVERS: [],

    REMOTE_KEYS: {
        LEFT: 37,
        UP: 38,
        RIGHT: 39,
        DOWN: 40,
        ENTER: 13,
        BACK: 8,
        ESCAPE: 27
    },

    RESULTS_PER_PAGE: 12,

    SEARCH_URL: function(query) {
        return this.SITE + "/?s=" + encodeURIComponent(query);
    }

};
