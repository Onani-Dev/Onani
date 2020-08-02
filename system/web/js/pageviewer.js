var pageSuccess = false,
    pageFilename, pageLocation, pageIndex, pageArtist, pageSource, pageFavourite, canNext = false,
    canPrev = false,
    deleteEnabled = true,
    pageSaucenaoUsed = false,
    fileType, expandedSidenav = false;

function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName;

    for (let i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
}

var prevTag = getUrlParameter('prev') || "None",
    page = getUrlParameter('p'),
    fileList, settings = JSON.parse(localStorage.getItem("settings")),
    favourites = JSON.parse(localStorage.getItem("favourites"));

function determineFileType(file) {
    if (['webm', 'mp4'].includes(file.split(".").slice(-1)[0])) {
        return "Video";
    } else {
        return "Image";
    }
}

function addTags(tags) {
    var settings = {
        "dataType": "json",
        "url": "/api/tags",
        "method": "PUT",
        "data": JSON.stringify({
            "filename": pageFilename,
            "location": pageLocation,
            "tags": tags
        }),
    };
    $.ajax(settings).done(function (data) {
        $("#tag-bar").empty();
        var tags = data.tags;
        for (var tag in tags) {
            var tagElement = document.createElement("div");
            if (!(tags[tag] == "None" || data.readonly)) {
                var deleteButton = document.createElement("a");
                deleteButton.className = 'delete';
                deleteButton.href = `javascript:deleteTag('${tags[tag]}')`;
                tagElement.appendChild(deleteButton);
            }
            var tagName = document.createElement("a");
            tagName.href = `/view?tag=${tags[tag]}`;
            tagName.innerHTML = tags[tag].replace(/_/g, " ");
            tagElement.appendChild(tagName);
            $("#tag-bar").append(tagElement);
        }
    });
}

function editFilename() {
    var splitName = pageFilename.split("-");
    var newFilename = prompt("New Filename for this file:", splitName[0]);
    if (newFilename === null) {} else {
        var settings = {
            "url": "/api/filename",
            "method": "PATCH",
            "headers": {
                "Content-Type": "application/json"
            },
            "data": JSON.stringify({
                "filename": pageFilename,
                "location": pageLocation,
                "new_filename": newFilename
            }),
        };
        $.ajax(settings).done(function (response) {
            pageFilename = response.new_filename.filename;
            pageLocation = response.new_filename.location;
            var url = window.location.href.split('/');
            url = new URL(`${url[0]}//${url[2]}/view_image`);
            var params = url.searchParams;
            params.set('location', pageLocation);
            params.set('filename', pageFilename);
            params.set('prev', prevTag);
            params.set('p', page);
            window.history.pushState(document.documentElement.innerHTML, document.title, url);
            updateImage();
        });
    }
}

function editArtist() {
    var newartist = prompt(`New tags for this ${fileType} (Split by spaces):`, pageArtist);
    if (newartist === null) {} else {
        var settings = {
            "dataType": "json",
            "url": "/api/artist",
            "method": "PATCH",
            "data": JSON.stringify({
                "filename": pageFilename,
                "location": pageLocation,
                "artist": newartist
            }),
        };
        $.ajax(settings).done(function (data) {
            $("#artist-text").text(`Artist: ${data.artist.replace(/_/g, " ")}`);
            $("#artist-link").attr("href", `/view?tag=artist:${data.artist}`);
            pageArtist = data.artist;
        });
    }
}

function editSource() {
    var newsource = prompt(`New source for this ${fileType}:`);
    if (newsource === null) {} else {
        var settings = {
            "dataType": "json",
            "url": "/api/source",
            "method": "PATCH",
            "data": JSON.stringify({
                "filename": pageFilename,
                "location": pageLocation,
                "source": newsource
            }),
        };
        $.ajax(settings).done(function (data) {
            $("#source-text").text(`Source: ${data.sources[0]}`);
            $("#source-link").attr("href", data.sources[0]);
        });
    }
}

function removeTags(tags) {
    var settings = {
        "dataType": "json",
        "url": "/api/tags",
        "method": "DELETE",
        "data": JSON.stringify({
            "filename": pageFilename,
            "location": pageLocation,
            "tags": tags
        }),
    };
    $.ajax(settings).done(function (data) {
        $("#tag-bar").empty();
        var tags = data.tags;
        for (var tag in tags) {
            var tagElement = document.createElement("div");
            if (!(tags[tag] == "None" || data.readonly)) {
                var deleteButton = document.createElement("a");
                deleteButton.className = 'delete';
                deleteButton.href = `javascript:deleteTag('${tags[tag]}')`;
                tagElement.appendChild(deleteButton);
            }
            var tagName = document.createElement("a");
            tagName.href = `/view?tag=${tags[tag]}`;
            tagName.innerHTML = tags[tag].replace(/_/g, " ");
            tagElement.appendChild(tagName);
            $("#tag-bar").append(tagElement);
        }
    });
}

function deleteImage() {
    if (confirm("Are you sure you want to delete this image? It cannot be undone.")) {
        var settings = {
            "url": "/api/image",
            "method": "DELETE",
            "data": JSON.stringify({
                "filename": pageFilename,
                "location": pageLocation
            }),
        };
        $.ajax(settings).done(function (data) {
            if (typeof prevTag !== 'undefined') {
                window.location.replace(`/view?tag=${prevTag}&page=${page}`);
            } else {
                window.location.replace("/");
            }
        });
    }
}

function toggleFavourite() {
    $("#toggle-favourite").attr("class", "disabled");
    $("#delete-button").attr("class", "disabled");
    var m;
    switch (pageFavourite) {
        case true:
            m = "DELETE";
            break;
        case false:
            m = "PUT";
            break;
    }
    var settings = {
        "url": "/api/profile",
        "method": m,
        "headers": {
            "Content-Type": "application/json"
        },
        "data": JSON.stringify({"location": pageLocation, "filename": pageFilename}),
    };

    $.ajax(settings).done(function (response) {
        localStorage.setItem("favourites", JSON.stringify(response));
        $("#toggle-favourite").attr("class", "");
        if (response.findIndex(obj => obj.filename == pageFilename) != -1) {
            $("#favourite-text").text(`Unfavourite`);
            pageFavourite = true;
        } else {
            $("#favourite-text").text(`Favourite`);
            pageFavourite = false;
        }
    });
}


function newTags() {
    var newtag = prompt(`New tags for this ${fileType} (Split by spaces):`);
    if (newtag != null) {
        newtag = newtag.split(" ");
        if (["don_chan", "wada_don", "wada_katsu", "katsu_chan", "taiko_no_tatsujin"].some(el => newtag.includes(el))) { // I'm so tired
            confirm("Perish");
            document.body.innerHTML = "";
            var count = -1;
            setInterval(function () {
                count += 1;
                if (count === 2) {
                    count = 0;
                }
                if (count === 0) {
                    document.body.style.backgroundColor = '#000000';
                } else if (count === 1) {
                    document.body.style.backgroundColor = '#ffffff';
                }
            }, 1);
        } else {
            addTags(newtag);
        }
    }
}

function deleteTag(tag) {
    if (confirm(`Are you sure you want to remove the tag ${tag}?`)) {
        removeTags([tag]);
    }
}

function toggleMessagebox() {
    var message_box = document.getElementById("message-box");
    if (message_box.style.display === "none") {
        $("#message-box").show(50);
    } else {
        $("#message-box").hide(50);
    }
}

function startSaucenao() {
    if (!pageSaucenaoUsed) {
        $("#start-saucenao").attr("class", "disabled");
        $("#saucenao-text").text("Please wait...");
        var settings = {
            "dataType": "json",
            "url": "/api/saucenao",
            "method": "POST",
            "data": JSON.stringify({
                "filename": pageFilename,
                "location": pageLocation,
            }),
        };
        $.ajax(settings).done(function (data) {
            var boxhtml = $.parseHTML(data.html);
            $("#start-saucenao").attr("class", "");
            pageSaucenaoUsed = true;
            $("#saucenao-text").text("Saucenao");
            $("#message-box").append(boxhtml);
            $("#message-box").show(50);
        });
    } else {
        toggleMessagebox();
    }  
}

function updateImage() {
    $.getJSON('/api/image', {
        "filename": pageFilename,
        "location": pageLocation
    }, function success(data) {
        if (fileList !== null) {
            if (fileList.findIndex(obj => obj.filename == pageFilename) === -1) {
                $("#next").css("visibility", "hidden");
                $("#pre").css("visibility", "hidden");
            } else {
                pageIndex = fileList.findIndex(obj => obj.filename == pageFilename);
                if (pageIndex === 0) {
                    $("#pre").css("visibility", "hidden");
                } else {
                    $("#pre").css("visibility", "visible");
                }
                if (pageIndex === fileList.length - 1) {
                    $("#next").css("visibility", "hidden");
                } else {
                    $("#next").css("visibility", "visible");
                }
            }
        } else {
            $("#next").css("visibility", "hidden");
            $("#pre").css("visibility", "hidden");
        }
        pageSuccess = true;
        fileType = determineFileType(pageFilename);
        pageArtist = data.artist;
        pageSource = data.source[0];
        var timestamp = new Date(data.timestamp * 1000);
        var tags = data.tags;
        $(document).prop('title', `Onani Viewer | ${pageFilename}`);
        if (typeof prevTag !== 'undefined') {
            $("#title-href").attr("href", `/view?tag=${prevTag}&page=${page}`);
        } else {
            $("#title-href").attr("href", "/");
        }
        $("#tag-bar").empty();
        for (var tag in tags) {
            var tagElement = document.createElement("div");
            if (!(tags[tag] == "None" || data.readonly)) {
                var deleteButton = document.createElement("a");
                deleteButton.className = 'delete';
                deleteButton.href = `javascript:deleteTag('${tags[tag]}')`;
                tagElement.appendChild(deleteButton);
            }
            var tagName = document.createElement("a");
            tagName.href = `/view?tag=${tags[tag]}`;
            tagName.innerHTML = tags[tag].replace(/_/g, " ");
            tagElement.appendChild(tagName);
            $("#tag-bar").append(tagElement);
        }
        if (data.readonly) {
            $("#options-bar").css("visibility", "hidden");
        } else {
            if (data.favourite) {
                $("#favourite-text").text(`Unfavourite`);
                pageFavourite = true;
            } else {
                $("#favourite-text").text(`Favourite`);
                pageFavourite = false;
            }
            if (fileType === "Video") {
                $("#start-saucenao").hide();
            } else {
                $("#start-saucenao").show();
            }
            $("#delete-button").text(`Delete ${fileType}`);
            if (data.favourite) {
                $("#delete-button").attr('class', 'disabled');
            } else {
                $("#delete-button").attr('class', '');
            }
        }
        $("#timestamp").text(`Timestamp: ${strftime('%d/%m/%Y %I:%M %p', timestamp)} (${moment(timestamp).fromNow()})`);
        $("#md5-text").text(`MD5: ${data.md5}`);
        $("#md5-link").attr("href", `/view?tag=md5:${data.md5}`);
        $("#filesize").text(`Filesize: ${Humanize.filesize(data.filesize)}`);
        $("#artist-text").text(`Artist: ${data.artist}`);
        $("#artist-link").attr("href", `/view?tag=artist:${data.artist}`);
        $("#source-text").text(`Source: ${data.source[0]}`);
        $("#source-link").attr("href", data.source[0]);
        $("#download-button").attr("href", `/view_image?location=${pageLocation}&filename=${pageFilename}&download=True`);
        $("#image-container").empty();
        $("#message-box").hide(50);
        $("#message-box").empty();
        $("#message-box").append('<a class="exit-button" id="toggle-messagebox"></a>');
        $("#toggle-messagebox").on("click", function () {
            toggleMessagebox();
        });
        if (fileType === "Image") {
            var imageContainer = document.createElement("div");
            imageContainer.className = 'main_image';
            imageContainer.addEventListener("dblclick", function () {
                window.history.pushState(document.documentElement.innerHTML, document.title, window.location.href);
                window.location.replace(`/view_image?location=${pageLocation}&filename=${pageFilename}&raw=True`);
            });
            imageContainer.style.backgroundImage = `url('/view_image?location=${pageLocation}&filename=${JSON.stringify(pageFilename).replace(/((^")|("$))/g, "").trim()}&raw=True')`;
            imageContainer.style.cursor = 'pointer';
            imageContainer.style.backgroundSize = 'contain';
            imageContainer.style.backgroundRepeat = 'no-repeat';
            imageContainer.style.backgroundPosition = 'center';
            $("#image-container").append(imageContainer);
        } else if (fileType === "Video") {
            var videoContainer = document.createElement("video");
            videoContainer.src = `/view_image?location=${pageLocation}&filename=${pageFilename}&raw=True`;
            videoContainer.controls = 'ass > tits';
            $("#image-container").append(videoContainer);
        }
        if (settings.sfw_mode) {
            $("#image-container").css("filter", "blur(20px)");
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
    }).fail(function (jqxhr, textStatus, error) {
        alert("An error getting this image occured. \nError:\n" + error);
        if (favourites.findIndex(obj => obj.filename == pageFilename) != -1) {
            if (confirm("Do you want to remove this from favourites?")) {
                removeFavourite();
            }
        }
        if (typeof prevTag !== 'undefined') {
            window.location.replace(`/view?tag=${prevTag}&page=${page}`);
        } else {
            window.location.replace("/");
        }
    });
}

// April fools 2020
function printImg() {
    var printimg = window.open(`/view_image?location=${pageLocation}&filename=${pageFilename}&raw=True`);
    printimg.focus();
    printimg.print();
}

function previousPage() {
    if (fileList.findIndex(obj => obj.filename == pageFilename) === 0) {
    } else {
        var newImage = fileList[pageIndex - 1];
        pageIndex -= 1;
        pageLocation = newImage.location;
        pageFilename = newImage.filename;
        var url = window.location.href.split('/');
        url = new URL(`${url[0]}//${url[2]}/view_image`);
        var params = url.searchParams;
        params.set('location', pageLocation);
        params.set('filename', pageFilename);
        params.set('prev', prevTag);
        params.set('p', page);
        window.history.pushState(document.documentElement.innerHTML, document.title, url);
        updateImage();
    }
}

function nextPage() {
    if (fileList.findIndex(obj => obj.filename == pageFilename) === fileList.length - 1) {
    } else {
        var newImage = fileList[pageIndex + 1];
        pageIndex += 1;
        pageLocation = newImage.location;
        pageFilename = newImage.filename;
        var url = window.location.href.split('/');
        url = new URL(`${url[0]}//${url[2]}/view_image`);
        var params = url.searchParams;
        params.set('location', pageLocation);
        params.set('filename', pageFilename);
        params.set('prev', prevTag);
        params.set('p', page);
        window.history.pushState(document.documentElement.innerHTML, document.title, url);
        updateImage();
    }
}

function setupButtonControls() {
    shortcut.add('Right', function () {
        nextPage();
    });

    shortcut.add('Left', function () {
        previousPage();
    });

    if (settings != null){
        if (typeof settings.free_hand !== 'undefined') {
            if (settings.free_hand == "left") {
                $("#control-div").addClass("anchor-left");
            } else if (settings.free_hand == "right") {
                $("#control-div").addClass("anchor-right");
            }
        } 
    }

    document.addEventListener('touchstart', handleTouchStart, false);
    document.addEventListener('touchmove', handleTouchMove, false);
    var xDown = null;
    var yDown = null;
    function getTouches(evt) {
        return evt.touches || // browser API
            evt.originalEvent.touches; // jQuery
    }
    function handleTouchStart(evt) {
        const firstTouch = getTouches(evt)[0];
        xDown = firstTouch.clientX;
        yDown = firstTouch.clientY;
    }
    function handleTouchMove(evt) {
        if (!xDown || !yDown) {
            return;
        }
        var xUp = evt.touches[0].clientX;
        var yUp = evt.touches[0].clientY;
        var xDiff = xDown - xUp;
        var yDiff = yDown - yUp;

        if (Math.abs(xDiff) > Math.abs(yDiff)) {
            if (xDiff > 0) {
                // Left swipe
                nextPage();
            } else {
                // Right swipe
                previousPage();
            }
        }
        xDown = null;
        yDown = null;
    }

    $("#toggle-navbar").on("click", function(){
        if (!expandedSidenav) {
            $(".sidenav").css("left", "0");
            $("#toggle-navbar").css("left", "270px");
            $("#toggle-navbar").text("<<");
            $("#control-div").css("display", "none");
            expandedSidenav = true;
        } else {
            $(".sidenav").css("left", "-270px");
            $("#toggle-navbar").css("left", "0");
            $("#toggle-navbar").text(">>");
            $("#control-div").css("display", "flex");
            expandedSidenav = false;
        }
    });
}

$(document).ready(function () {
    var filename = getUrlParameter("filename");
    var location = getUrlParameter("location");
    var store = new IdbKvStore('OnaniObjectStore');
    pageFilename = filename;
    pageLocation = location;
    store.get(prevTag, function (err, value) {
        if (err) {
            fileList = null;
        } else if (typeof value == "undefined") {
            fileList = null;
        } else {
            fileList = value.files;
        }
        if (fileList !== null) {
            if (fileList.findIndex(obj => obj.filename == pageFilename) === -1) {
                $("#next").css("visibility", "hidden");
                $("#pre").css("visibility", "hidden");
            } else {
                pageIndex = fileList.findIndex(obj => obj.filename == pageFilename);
                if (pageIndex === 0) {
                    $("#pre").css("visibility", "hidden");
                } else {
                    $("#pre").css("visibility", "visible");
                }
                if (pageIndex === fileList.length - 1) {
                    $("#next").css("visibility", "hidden");
                } else {
                    $("#next").css("visibility", "visible");
                }
            }
        } else {
            $("#next").css("visibility", "hidden");
            $("#pre").css("visibility", "hidden");
        }
        $("#toggle-favourite").on("click", function () {
            toggleFavourite();
        });
        $("#pre").on("click", function () {
            previousPage();
        });
        $("#next").on("click", function () {
            nextPage();
        });
        $("#toggle-messagebox").on("click", function () {
            toggleMessagebox();
        });
        $("#start-saucenao").on("click", function () {
            startSaucenao();
        });
        $("#april-print").on("click", function () {
            printImg();
        });
        $("#add-tags").on("click", function () {
            newTags();
        });
        $("#edit-artist").on("click", function () {
            editArtist();
        });
        $("#edit-source").on("click", function () {
            editSource();
        });
        $("#edit-filename").on("click", function () {
            editFilename();
        });
        $("#delete-button").on("click", function () {
            if (deleteEnabled) {
                deleteImage();
            }
        });

        setupButtonControls();
        updateImage(); 
    });
});

