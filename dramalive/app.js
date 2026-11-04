(function () {
  "use strict";

  var launchButton = document.getElementById("launch");

  if (!launchButton) {
    return;
  }

  document.addEventListener("keydown", function (event) {
    var key = event.key || event.keyCode;

    if (key === "Enter" || key === 13) {
      launchButton.click();
    }
  });
}());
