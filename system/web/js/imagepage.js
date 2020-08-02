var fileList, imagesOnPage = [],
    beforeSort = [],
    endPage, origtag, imgType, nextPartition = null,
    loadMoreWhen, totalImages, partitioned = false,
    loading = false,
    reversed = false,
    sorted = false,
    preHTML = null,
    inputDisabled = false,
    settings = JSON.parse(localStorage.getItem("settings")),
    favourites = JSON.parse(localStorage.getItem("favourites"));

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

var page = parseInt(getUrlParameter('page'));
if (isNaN(page)) {
    page = 0;
}

function isMobile() { 
    return window.innerWidth <= 502;
}

function isTouchDevice() {
    try {
        document.createEvent("TouchEvent");
        return true;
    } catch (e) {
        return false;
    }
}

function getExtension(filename) {
    return filename.substring(filename.lastIndexOf('.') + 1, filename.length) || filename;
}

function pageMath(number) {
    return Math.ceil(parseFloat(60 * number));
}

function updateCache(force=false) {
    var store = new IdbKvStore('OnaniObjectStore');
    store.get(origtag, function (err, value) {
        if (typeof value == 'undefined' || value.start_next != nextPartition || value.expire < new Date().getTime() || force) {
            console.log("Cache Update Needed, Updating Cache.");
            store.set(origtag, {
                files: fileList,
                start_next: nextPartition,
                total: totalImages,
                expire: new Date(new Date().getTime() + 5 * 60000).getTime()
            }, function (err) {
                if (err) {
                    store.remove(origtag, function (err) {
                        if (err) {
                            console.error(err);
                        } else {
                            store.set(origtag, {
                                files: fileList,
                                start_next: nextPartition,
                                total: totalImages,
                                expire: new Date(new Date().getTime() + 5 * 60000).getTime()
                            }, function (err) {
                                if (err) {
                                    console.error(err);
                                }
                            });
                        }
                    });
                }
            });
        }
    });
}

function checkForPageUpdate() {
    if (partitioned) {
        if (nextPartition != null) {
            if (page > Math.ceil(parseFloat(fileList.length / 60)) - 1) {
                if (sorted) { 
                    sorted = false;
                    fileList = beforeSort;
                }
                $("#loading-container").css('display', 'inline-block');
                var settings = {
                    "url": `/api/query_tags?tag=${origtag}&start=${nextPartition}`,
                    "method": "GET",
                    "complete": function () {
                        setTimeout(checkForPageUpdate(), 500);
                    }
                };
                $.ajax(settings).done(function (response) {
                    nextPartition = response.start_next;
                    fileList.push(...response.files);
                    updateImages();
                    renewPage();
                });
            } else {
                $("#loading-container").css('display', 'none');
            }
        } else {
            $("#loading-container").css('display', 'none');
        }
    }
}

function renewPage() {
    var count = 0;
    for (let i = 0; i < 7; i++) {
        $(`#column${i}`).empty();
    }
    var col = 1;
    function loadNewImage(nextImg) {
        if (imagesOnPage.length == nextImg) {
            inputDisabled = false;
        } else {
            var imageElement = document.createElement("div"),
                childThumb = document.createElement("img"),
                favButton = document.createElement("button"),
                image = new Image(),
                file = imagesOnPage[nextImg],
                method;
            image.src = `/view_image?location=${file.location}&filename=${file.filename}&prev=${encodeURI(origtag)}&thumb=True`;
            image.onload = function () {
                if (!isMobile() && !isTouchDevice()) {
                    $(imageElement).hover(function () {
                        $(this).css("transform", "scale(1.1)");
                        $(this).css("z-index", "48");
                        $(this).find('button').css("display", "block");
                        $(this).find('img').css("box-shadow", "0 0 20px 10px rgba(255, 0, 0, 0.6)");
                    }, function () {
                        $(this).css("transform", "");
                        $(this).css("z-index", "0");
                        $(this).find('button').css("display", "none");
                        $(this).find('img').css("box-shadow", "");
                    });
                }
                imageElement.style.cursor = 'pointer';
                imageElement.className = 'image-container';
                childThumb.style.width = "100%";
                childThumb.style.height = "auto";
                childThumb.onclick = function () {
                    window.history.pushState(document.documentElement.innerHTML, document.title, window.href);
                    window.location.replace(`/view_image?location=${file.location}&filename=${file.filename}&prev=${encodeURI(origtag)}&p=${page}`);
                };
                favButton.className = "favourite-button";
                favButton.onclick = function () {
                    var filename = file.filename,
                        location = file.location,
                        element = this;
                    if (favourites.findIndex(obj => obj.filename == file.filename) != -1) {
                        method = "DELETE";
                    } else {
                        method = "PUT";
                    }
                    var settings = {
                        "url": "/api/profile",
                        "method": method,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "data": JSON.stringify({
                            "location": location,
                            "filename": filename
                        }),
                    };

                    $.ajax(settings).done(function (response) {
                        localStorage.setItem("favourites", JSON.stringify(response));
                        favourites = response;
                        if (response.findIndex(obj => obj.filename == filename) != -1) {
                            $(element).text('Unfavourite');
                        } else {
                            $(element).text('Favourite');
                        }
                    });
                };
                if (favourites.findIndex(obj => obj.filename == file.filename) != -1) {
                    favButton.innerHTML = "Unfavourite";
                } else {
                    favButton.innerHTML = "Favourite";
                }
                if (isMobile()) {
                    count += 1;
                    if (['webm', 'mp4'].includes(getExtension(file.filename))) {
                        childThumb.className = "video";
                    } else {
                        childThumb.className = "image";
                    }
                    childThumb.src = `/view_image?location=${file.location}&filename=${file.filename}&prev=${encodeURI(origtag)}&thumb=True`;
                    imageElement.appendChild(childThumb);
                    $(`#column${count}`).append(imageElement);
                    if (settings.sfw_mode) {
                        $(`#column${col}`).css("filter", "blur(5px)");
                    }
                    if (count === 10) {
                        count = 0;
                        col += 1;
                    }
                } else {
                    count += 1;
                    if (['webm', 'mp4'].includes(getExtension(file.filename))) {
                        childThumb.className = "video";
                    } else {
                        childThumb.className = "image";
                    }
                    childThumb.src = `/view_image?location=${file.location}&filename=${file.filename}&prev=${encodeURI(origtag)}&thumb=True`;
                    $(`#column${count}`).append(imageElement);
                    if (settings.sfw_mode) {
                        $(`#column${count}`).css("filter", "blur(5px)");
                    }
                    if (count === 6) {
                        count = 0;
                    }
                }
                imageElement.appendChild(childThumb);
                imageElement.appendChild(favButton);
                inputDisabled = true;
                loadNewImage(nextImg + 1);
            };
        }
    }

    endPage = Math.ceil(parseFloat(totalImages / 60));
    $("#images_on_page").text(`Images on page: ${imagesOnPage.length.toLocaleString()}`);
    $("#page-counter").text(`Page: ${page + 1}/${endPage}`);
    
    if (nextPartition != null) {
        $("#next").attr('class', "forward");
        $("#next_lastpage").attr('class', "forward");
    } else {
        if (endPage - 1 == page) {
            $("#next").attr('class', "forward disable");
            $("#next_lastpage").attr('class', "forward disable");
        } else {
            $("#next").attr('class', "forward");
            $("#next_lastpage").attr('class', "forward");
        }
    }

    if (page !== 0) {
        $("#pre").attr("class", "backward");
        $("#pre_firstpage").attr("class", "backward");
    } else {
        $("#pre").attr("class", "backward disable");
        $("#pre_firstpage").attr("class", "backward disable");
    }
    inputDisabled = true;
    loadNewImage(0);
    updateCache();
}

function updateImages() {
    imagesOnPage = [];
    var count = 0;
    var sliced = fileList.slice(pageMath(page));
    for (var i in sliced) {
        var file = sliced[i];
        if (count === 60) {
            break;
        } else {
            imagesOnPage.push(file);
            count += 1;
        }
    }
}

function checkImageUpdate() {
    var images = [];
    var count = 0;
    var sliced = fileList.slice(pageMath(page));
    for (var i in sliced) {
        var file = sliced[i];
        if (count === 60) {
            break;
        } else {
            images.push(file);
            count += 1;
        }
    }
    return images;
}

function nextPage() {
    if (page == endPage - 1) {
        console.log("Last page!");
    } else if (!inputDisabled) {
        var url = new URL(window.location.href);
        var params = url.searchParams;
        params.set('page', page + 1);
        window.history.pushState(document.documentElement.innerHTML, document.title, url);
        page += 1;
        updateImages();
        renewPage();
        checkForPageUpdate();
    }
}

function lastPage() {
    if (page == endPage - 1) {
        console.log("Last page!");
    } else if (!inputDisabled) {
        var url = new URL(window.location.href);
        var params = url.searchParams;
        params.set('page', endPage - 1);
        window.history.pushState(document.documentElement.innerHTML, document.title, url);
        page = endPage - 1;
        updateImages();
        renewPage();
        checkForPageUpdate();
    }
}

function previousPage() {
    if (page == 0) {
        console.log("First page!");
    } else if (!inputDisabled) {
        var url = new URL(window.location.href);
        var params = url.searchParams;
        params.set('page', page - 1);
        window.history.pushState(document.documentElement.innerHTML, document.title, url);
        page -= 1;
        updateImages();
        renewPage();
        checkForPageUpdate();
    }
}

function firstPage() {
    if (page == 0) {
        console.log("First page!");
    } else if (!inputDisabled) {
        var url = new URL(window.location.href);
        var params = url.searchParams;
        params.set('page', 0);
        window.history.pushState(document.documentElement.innerHTML, document.title, url);
        page = 0;
        updateImages();
        renewPage();
        checkForPageUpdate();
    }
}

function reverseImages() {
    $("#loading-container").css('display', 'inline-block');
    fileList.reverse();
    if (!reversed) {
        reversed = true;
        document.getElementById("reverse").className = "reverse enabled";
    } else {
        reversed = false;
        document.getElementById("reverse").className = "reverse disabled";
    }
    updateImages();
    renewPage();
    checkForPageUpdate();
    $("#loading-container").css('display', 'none');
}

function sortImages() {
    if (!inputDisabled) {
        if (!sorted) {
            sorted = true;
            beforeSort = [];
            fileList.forEach(function (file, i) {
                beforeSort.push(file);
            });
            var collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'});
            fileList.sort(function (a, b) {
                return collator.compare(a.filename, b.filename);
            });
            document.getElementById("sort").className = "sort enabled";
        } else {
            sorted = false;
            fileList = beforeSort;
            document.getElementById("sort").className = "sort disabled";
        }
        updateImages();
        renewPage();
        updateCache(force=true);
        checkForPageUpdate();
    }
}

function jumpPage() {
    if (!inputDisabled) {
        var newPage = prompt(`New page (Between 1 and ${endPage}):`, page + 1);
        newPage = parseInt(newPage) - 1;
        if (isNaN(newPage)) {
            alert('Invalid page!');
        } else if (_.range(0, endPage).includes(newPage)) {
            var url = new URL(window.location.href);
            var params = url.searchParams;
            params.set('page', newPage);
            window.history.pushState(document.documentElement.innerHTML, document.title, url);
            page = newPage;
            updateImages();
            renewPage();
            checkForPageUpdate();
        } else {
            alert('Invalid page!');
        }
    }
}

function setupButtonControls() {
    shortcut.add('Right', function () {
        nextPage();
    });
    shortcut.add('Left', function () {
        previousPage();
    });
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
        } else {
            if (yDiff > 0) {
                // Up swipe
            } else {
                // Down swipe
            }
        }
        // reset values
        xDown = null;
        yDown = null;
    }
}

$(document).ready(function () {
    function parseFileListData(data) {
        fileList = data.files;
        if (data.start_next != null) {
            partitioned = true;
            nextPartition = data.start_next;
            loadMoreWhen = Math.ceil(parseFloat(data.start_next / 60));
        }
        if (fileList.length === 0) {
            alert(`No files with the tag(s): ${tag} were found.`);
            window.history.back();
        } else {
            origtag = tag;
            $("#image_amount").text(`Amount of images: ${data.total.toLocaleString()}`);
            totalImages = data.total;
            var count = 0;
            var sliced = fileList.slice(pageMath(page));
            for (var i in sliced) {
                var file = sliced[i];
                if (count === 60) {
                    break;
                } else {
                    imagesOnPage.push(file);
                    count += 1;
                }
            }
            $("#pre_firstpage").on("click", function () {
                firstPage();
            });
            $("#pre").on("click", function () {
                previousPage();
            });
            $("#next").on("click", function () {
                nextPage();
            });
            $("#next_lastpage").on("click", function () {
                lastPage();
            });
            $("#reverse").on("click", function () {
                reverseImages();
            });
            $("#sort").on("click", function () {
                sortImages();
            });
            $("#jumpe").on("click", function () {
                jumpPage();
            });
            renewPage();
            $("#loading-container").css('display', 'none');
        }
    }
    setupButtonControls();
    var tag = getUrlParameter('tag');
    if (typeof tag === 'undefined') {
        tag = "all";
    }
    tag = tag.replace(/\+/g, " ");
    document.getElementById("search_box").value = tag;
    document.title = `Onani Viewer | ${tag}`;
    var store = new IdbKvStore('OnaniObjectStore');
    var settings = {
        "url": `/api/query_tags?tag=${tag}&start=0`,
        "method": "GET"
    };
    store.get(tag, function (err, value) {
        if (err) {
            fileList = null;
        } else {
            fileList = value || null;
        }
        if (fileList !== null) {
            if ((value.expire < new Date().getTime())) {
                $.ajax(settings).done(function (data) {
                    parseFileListData(data);
                    checkForPageUpdate();
                }).fail(function (jqxhr, textStatus, error) {
                    alert(`Failed to load.\nError: ${error}`);
                    window.history.back();
                });
            } else {
                parseFileListData(value);
                checkForPageUpdate();
            }
        } else {
            $.ajax(settings).done(function (data) {
                parseFileListData(data);
                checkForPageUpdate();
            }).fail(function (jqxhr, textStatus, error) {
                alert(`Failed to load.\nError: ${error}`);
                window.history.back();
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


var prevScrollpos = window.pageYOffset;
window.onscroll = function () {
    if (isMobile()) {
        var currentScrollPos = window.pageYOffset;
        if (prevScrollpos > currentScrollPos) {
            document.getElementById("topbar").style.top = "0";
        } else {
            document.getElementById("topbar").style.top = "-75px";
        }
        prevScrollpos = currentScrollPos;
    }
};
