
(function () {
    var container;
    var status;
    var request;

    function createPage() {
        container = document.getElementById("catalogue");

        if (!container) {
            container = document.createElement("div");
            container.id = "catalogue";
            document.body.appendChild(container);
        }

        status = document.getElementById("catalogue-status");

        if (!status) {
            status = document.createElement("div");
            status.id = "catalogue-status";
            container.parentNode.insertBefore(status, container);
        }

        status.innerHTML = "Loading Cima4U catalogue...";
    }

    function showItems(items) {
        var i;
        var item;
        var link;
        var title;

        container.innerHTML = "";

        if (!items || !items.length) {
            status.innerHTML = "No catalogue entries found.";
            return;
        }

        for (i = 0; i < items.length; i++) {
            item = items[i];

            if (!item.title || !item.url) {
                continue;
            }

            link = document.createElement("a");
            link.href = item.url;
            link.className = "catalogue-item";

            title = document.createElement("div");
            title.className = "catalogue-title";
            title.innerHTML = "";

            title.appendChild(document.createTextNode(item.title));
            link.appendChild(title);

            if (item.description) {
                var description = document.createElement("div");
                description.className = "catalogue-description";
                description.appendChild(
                    document.createTextNode(item.description)
                );
                link.appendChild(description);
            }

            container.appendChild(link);
        }

        status.innerHTML = "Catalogue loaded.";
    }

    function loadCatalogue() {
        request = new XMLHttpRequest();
        request.open("GET", "catalogue.json", true);

        request.onreadystatechange = function () {
            if (request.readyState !== 4) {
                return;
            }

            if (request.status === 200) {
                try {
                    showItems(JSON.parse(request.responseText));
                } catch (error) {
                    status.innerHTML = "Could not read catalogue.";
                }
            } else {
                status.innerHTML = "Catalogue not available yet.";
            }
        };

        request.onerror = function () {
            status.innerHTML = "Could not connect to catalogue.";
        };

        request.send();
    }

    window.onload = function () {
        createPage();
        loadCatalogue();
    };
})();
