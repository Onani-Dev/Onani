// thanks stack overflow
function millisecondsToHms(d) {
    d = Number(d);
    d = Math.round(d / 1000);
    var h = Math.floor(d / 3600);
    var m = Math.floor(d % 3600 / 60);
    var s = Math.floor(d % 3600 % 60);

    var hDisplay = h > 0 ? h + (h == 1 ? " hour, " : " hours, ") : "";
    var mDisplay = m > 0 ? m + (m == 1 ? " minute, " : " minutes, ") : "";
    var sDisplay = s > 0 ? s + (s == 1 ? " second" : " seconds") : "";
    return hDisplay + mDisplay + sDisplay; 
}

// non skidded shit
$(document).ready(function () {
    var timer = document.getElementById("timer");
    const start = Date.now();
    var interval = setInterval(function () {
        var seconds = millisecondsToHms(Math.floor(Date.now() - start));
        timer.innerHTML = "You've been drinking cum for: " + seconds;
    }, 1000);
});
