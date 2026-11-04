
/*
 * Cima4U catalogue configuration
 * Compatible with older Samsung Tizen browsers.
 */

var CIMA4U = {
    site: "https://cimafu.live",

    categories: [
        {
            name: "Foreign Movies",
            url: "/category/movies/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A%D8%A9/"
        },
        {
            name: "Arabic Movies",
            url: "/?s=%D8%A7%D9%81%D9%84%D8%A7%D9%85+%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9"
        },
        {
            name: "Asian Movies",
            url: "/?s=%D8%A7%D9%81%D9%84%D8%A7%D9%85+%D8%A7%D8%B3%D9%8A%D9%88%D9%8A%D8%A9"
        },
        {
            name: "Turkish Movies",
            url: "/?s=%D8%A7%D9%81%D9%84%D8%A7%D9%85+%D8%AA%D8%B1%D9%83%D9%8A%D8%A9"
        },
        {
            name: "Indian Movies",
            url: "/?s=%D8%A7%D9%81%D9%84%D8%A7%D9%85+%D9%87%D9%86%D8%AF%D9%8A%D8%A9"
        },
        {
            name: "Foreign Series",
            url: "/?s=foreign+series"
        },
        {
            name: "Arabic Series",
            url: "/?s=%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9"
        },
        {
            name: "Turkish Series",
            url: "/?s=%D9%85%D8%B3%D9%84%D8%B3%D9%84%D8%A7%D8%AA+%D8%AA%D8%B1%D9%83%D9%8A%D8%A9"
        },
        {
            name: "Asian Series",
            url: "/?s=asian+series"
        },
        {
            name: "Anime",
            url: "/?s=anime"
        },
        {
            name: "TV Shows",
            url: "/?s=tv+shows"
        }
    ],

    search: function (query) {
        return this.site + "/?s=" + encodeURIComponent(query);
    },

    category: function (index) {
        if (index < 0 || index >= this.categories.length) {
            return this.site;
        }

        return this.site + this.categories[index].url;
    }
};
