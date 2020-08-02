var total;
var startNext;

function tagSizeMath(length) {
	var size = 0.2 * length / 100;
	if (size > 6.0) {
        size = (Math.random() * (5 - 6) + 6).toFixed(2);
    }
    if (size < 0.90) {
        size = 0.6;
    }
	return size;
}


$(document).ready(function () {
    var settings = {
        "url": "/api/tag_counts?start=0&limit=1000",
        "method": "GET",
    };
    $.ajax(settings).done(function (data) {
        total = data.total;
        startNext = data.start_next;
        if (Object.keys(data.tags).length === 0) {
            $("#tags_div").append('<div class="tag_block"><a class="tag" href="/" title="Nothing at all" style="font-size: 0.6em;">Sorry Nothing</a></div>');
        } else {
            for (var tag in data.tags) {
                $("#tags_div").append(`<div class="tag_block"><a class="tag" href="/view?reverse=false&tag=${tag}"title="${data.tags[tag]} images" style="margin-right:5px;margin-left:5px;font-size: ${tagSizeMath(data.tags[tag])}em;">${tag.replace(/_/g, " ")}</a></div>`);
            }
        }
        $("#loading-container").hide();
        $(window).scroll(function () {
            if ($(window).scrollTop() == $(document).height() - $(window).height()) {
                if (startNext != null) {
                    $("#loading-container").show();
                    var settings = {
                        "url": `/api/tag_counts?start=${startNext}&limit=1000`,
                        "method": "GET",
                    };

                    $.ajax(settings).done(function (data) {
                        startNext = data.start_next;
                        for (var tag in data.tags) {
                            $("#tags_div").append(`<div class="tag_block"><a class="tag" href="/view?reverse=false&tag=${tag}"title="${data.tags[tag]} images" style="margin-right:5px;margin-left:5px;font-size: ${tagSizeMath(data.tags[tag])}em;">${tag.replace(/_/g, " ")}</a></div>`);
                        };
                        $("#loading-container").hide();
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
                }
            }
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
    });
});
