
/*
 * Cima4U TV configuration
 * Samsung Tizen 4.0 / Chromium 56
 */

var CIMA_CONFIG = {
    SITE: "https://cimafu.live",

    PLAYER_SERVERS: [
        {
            name: "Server 1",
            url: "https://bysetayico.com/e/xfma0yd2zcom"
        },
        {
            name: "Server 2",
            url: "https://1vid.xyz/embed-pshlpck8k6kf.html"
        },
        {
            name: "Server 3",
            url: "https://vidmoly.org/embed-m4tsa28ojsr4.html"
        },
        {
            name: "Server 4",
            url: "https://vidspeed.org/embed-j54vlwgbq5ot.html"
        }
    ],

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
