var currentMenu = "scraper";
var infCache = {};
const ansi_up = new AnsiUp();


$(document).ready(function () {
    var Regexes = [
        '^(http[s]?:\\/\\/)?(e-hentai\\.org)\\/(g)\\/([0-9]{1,9})\\/([a-zA-Z0-9]{1,10})\\/?',
        '^(http[s]?:\\/\\/)?(yiff\\.party)\\/patreon\\/([0-9]{7,12})',
        '^((http[s]?:\\/\\/)?twitter\\.com\\/([0-9a-zA-Z_-]{1,})|@([0-9a-zA-Z_-]{1,}))'];
    function changeMenu() {
        if (currentMenu == "scraper") {
            var settings = {
                "url": "/api/supported_sites",
                "method": "GET",
            };
            $("#pannel-menu").empty();
            $("#pannel-menu").append('<form id="sites-selectors"></form>');
            $.ajax(settings).done(function (data) {
                for (var i in data) {
                    $("#sites-selectors").append(`<div style="display:inline-block;white-space: nowrap;width:25%;text-align: left;"><input id="${data[i]}" name="${data[i]}" type="checkbox" value=true><label for="${data[i]}">${data[i]}</label></div>`);
                }
            }).then($("#sites-selectors").append('<div><input name="query" placeholder="Enter Query..." onkeydown="return (event.keyCode!=13);" style="display:inline-block;width:75%;" type="text" autocomplete="new-password"><input type="button" value="Scrape" id="scrape-button" class="start-scrape" style="display:inline-block;width:15%;"></div>'));
            if (infCache.scraping) {
                $("#scrape-button").prop("value", "Stop");
                $("#scrape-button").removeClass('start-scrape').addClass('stop-scrape');
            }
        } else if (currentMenu == "downloader") {
            $("#pannel-menu").empty();
            $("#pannel-menu").append('<form id="download-form"></form>');
            $("#download-form").append('<div><input name="query" id="link-input" placeholder="Enter Link..." onkeydown="return (event.keyCode!=13);" style="display:inline-block;width:75%;" type="text" autocomplete="new-password"><input type="button" value="Download" id="download-button" class="start-download" style="display:inline-block;width:15%;"></div>');
        }
    }

    $.ajax({
        "url": "/api/scraper_values",
        "method": "GET",
    }).done(function (data) {
        infCache = data;
    });

    changeMenu();

    $(document).on('click', '#toggle-scraper-menu', function () {
        currentMenu = "scraper";
        changeMenu();
    });

    $(document).on('click', '#toggle-downloader-menu', function () {
        currentMenu = "downloader";
        changeMenu();
    });

    $(document).on('click', '#toggle-console', function () {
        $("#console-pannel").show();
    });

    $(document).on('click', '#exit-console-button', function () {
        $("#console-pannel").hide();
    });

    $(document).on('click', '#download-button', function () {
        var downloadBoxVal = $("#link-input").val();
        var valid = false;
        for (var r in Regexes) {
            var reg = new RegExp(Regexes[r]);
            if (downloadBoxVal.match(reg) != null) {
                valid = true;
                downloadBoxVal = downloadBoxVal.match(reg)[0];
            }
        }
        if (valid) {
            $("#console-pannel").show();
            console.log(`Valid Link Found!: ${downloadBoxVal}`);
            var settings = {
                "url": "/api/download",
                "method": "POST",
                "data": JSON.stringify({
                    "link": downloadBoxVal
                }),
            };
            $.ajax(settings).done(function (data) {
                console.log(data);
                console.log("Started Download");
                $("#scrape-button").prop("value", "Stop");
            });
        } else {
            alert("Invalid input.");
        }
    });

    $(document).on('click', '.start-scrape', function () {
        var vals = {};
        var formdata = $("#sites-selectors").serializeArray();
        var query = formdata[0].value;
        formdata.shift();
        for (var v in formdata) {
            vals[formdata[v].name] = true;
        }
        var settings = {
            "url": "/api/scrape",
            "method": "POST",
            "data": JSON.stringify({
                "action": "start",
                "query": query,
                "values": vals
            }),
        };
        $.ajax(settings).done(function (data) {
            console.log("Started Scrape");
            $("#scrape-button").prop("value", "Stop");
        });
        $("#console-pannel").show();
        $(this).removeClass('start-scrape').addClass('stop-scrape');
    });

    $(document).on('click', '.stop-scrape', function () {
        var settings = {
            "url": "/api/scrape",
            "method": "POST",
            "data": JSON.stringify({
                "action": "stop"
            }),
        };
        $.ajax(settings).done(function (data) {
            console.log("Stopped Scrape");
            $("#scrape-button").prop("value", "Scrape");
        });
        $(this).removeClass('stop-scrape').addClass('start-scrape');
    });

    setInterval(function () {
        $.ajax({"url": "/api/scraper_values", "method": "GET",}).done(function (data) {
            infCache = data;
        });
        $.ajax({"url": "/api/console", "method": "GET",}).done(function (data) {
            $("#console-pannel").empty();
            $("#console-pannel").append(`<a class="exit-button" id="exit-console-button"></a>`);
            for (var l in data) {
                var line = data[l];
                $("#console-pannel").append(`<p style="margin-top:0px;margin-bottom:0px;font-size:12px;display:block;float:left;clear: both;color:#FFF;>${ansi_up.ansi_to_html(line)}</p>`);
            }
            var scrolled = false;
            function updateScroll() {
                if (!scrolled) {
                    var element = document.getElementById("console-pannel");
                    element.scrollTop = element.scrollHeight;
                }
            }
            $("#console-pannel").on('scroll', function () {
                scrolled = true;
            });
            updateScroll();
        });
        // console.log(infCache);
    }, 1500);
});