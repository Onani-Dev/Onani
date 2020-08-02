$(document).ready(function () {
    $(document).on('click', '#submit', function () {
        var username = $("#username").val();
        var password = $("#password").val();
        var settings = {
            "url": "/api/login",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "data": JSON.stringify({
                "username": username,
                "password": password
            }),
        };
        $.ajax(settings).done(function (data) {
            console.log(data);
            if (data.error != null) {
                alert(data.error);
            } else {
                localStorage.setItem("user", data.username);
                localStorage.setItem("favourites", JSON.stringify(data.favourites));
                localStorage.setItem("settings", JSON.stringify(data.settings));
                window.location.replace("/");
            }
        });
    });
    $("#password").keyup(function (event) {
        if (event.keyCode === 13) {
            $("#submit").click();
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