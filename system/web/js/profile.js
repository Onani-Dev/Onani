function notify(message) {
    if (is_mobile()) {
        alert(message);
    } else {
        var text = document.createElement("p");
        text.innerHTML = message;
        text.style.top = `${Math.floor(Math.random() * screen.availHeight - 200) + 200}px`;
        text.className = "flier";
        document.body.appendChild(text);
    }
}


function is_mobile() {
    return window.innerWidth <= 768;
}


$(document).ready(function () {
    document.body.style.overflowY = 'overlay';
    document.getElementsByClassName("title")[0].style.maxWidth = '250px';
    $("#copy-button").on("click", function () {
        var copyText = document.getElementById("api-key");
        copyText.select();
        copyText.setSelectionRange(0, 99999);
        document.execCommand("copy");
        notify("Copied to clipboard.");
    });

    $("#save-button").on("click", function () {
        var sfw_mode = false;
        if ($("#sfw-mode").val() == "Enabled") {
            sfw_mode = true;
        }
        var splash_text = false;
        if ($("#splash-text").val() == "Enabled") {
            splash_text = true;
        }
        var settings = {
            "url": "/api/profile",
            "method": "PATCH",
            "headers": {
                "Content-Type": "application/json"
            },
            "data": JSON.stringify({
                "updated": {
                    "free_hand": $("#free-hand").val(),
                    "sfw_mode": sfw_mode,
                    "splash_text": splash_text
                }
            }),
        };
        $.ajax(settings).done(function (response) {
            localStorage.setItem("settings", JSON.stringify({
                "free_hand": $("#free-hand").val(),
                "sfw_mode": sfw_mode,
                "splash_text": splash_text
            }));
            notify("Changes Saved.");
        }).fail(function (){
            notify("Failed saving changes.");
        });
    });

    $("#regen-button").on("click", function () {
        if (confirm("Are you sure you want to regenerate your API key? It will invalidate your existing one.")) {
            var settings = {
                "url": "/api/api_key",
                "method": "PATCH",
                "headers": {
                    "Content-Type": "application/json"
                }
            };
            $.ajax(settings).done(function (response) {
                $("#api-key").val(response.new_key);
                notify("API Key Regenerated.");
            }).fail(function () {
                notify("Failed to regenerate API key.");
            });
        }
    });
    twemoji.parse(document.body, {
        callback: function (icon, options, variant) {
            switch (icon) {
                case 'a9': // © copyright
                case 'ae': // ® registered trademark
                case '2122': // ™ trademark
                    return false;
            }
            return ''.concat(options.base, options.size, '/', icon, options.ext);
        }
    });
});