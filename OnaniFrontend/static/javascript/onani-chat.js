/*
 * @Author: Blakeando
 * @Date:   2020-09-10 02:40:26
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-10 04:53:23
 */
'use strict';

window.onload = function () {
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/chat');

    function SendMessage() {
        var text = document.getElementById('chat-box-textarea').value;
        if (text == "") { }
        else {
            socket.emit('message', text);
            document.getElementById('chat-box-textarea').value = '';
        }

    }


    var connectMessage = document.createElement("li");
    connectMessage.innerHTML = "<b>Connecting...</b>";
    console.log("Connecting...");
    document.getElementById("chat-message-area").appendChild(connectMessage);

    document.getElementById("chat-box-send").addEventListener("click", function () { SendMessage(); })
    document.getElementById("chat-box-textarea").addEventListener("keypress", function (e) {
        if (e.keyCode === 13) {
            e.preventDefault();
            SendMessage();
        }
    })

    socket.on('connect', function () {
        var connectMessage = document.createElement("li");
        connectMessage.innerHTML = "<b>Connected.</b>";
        console.log("Connected.");
        document.getElementById("chat-message-area").appendChild(connectMessage);
    });

    socket.on('message', function (message) {
        var recievedMessage = document.createElement("li");
        recievedMessage.innerHTML = `<b>${message.user}:</b> ${message.message}`;
        document.getElementById("chat-message-area").appendChild(recievedMessage);
    });

    socket.on('connection', function (data) {
        var recievedMessage = document.createElement("li");
        recievedMessage.innerHTML = `<b>${data.data}</b>`;
        document.getElementById("chat-message-area").appendChild(recievedMessage);
    });

    socket.on('disconnection', function (data) {
        var recievedMessage = document.createElement("li");
        recievedMessage.innerHTML = `<b>${data.data}</b>`;
        document.getElementById("chat-message-area").appendChild(recievedMessage);
    });
}

