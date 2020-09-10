/*
 * @Author: Blakeando
 * @Date:   2020-09-10 02:40:26
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-10 15:09:18
 */
'use strict';
var scrolled = false;

jQuery(function ($) {
    $('#chat-message-area').on('scroll', function () {
        if ($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight) {
            scrolled = false;
        } else {
            scrolled = true;
        }
    })
});

function ScrollChat() {
    var messageArea = document.getElementById("chat-message-area");
    if (!scrolled) {
        messageArea.scrollTop = messageArea.scrollHeight;
    }
}

function AddChatMessage(content) {
    var recievedMessage = document.createElement("li");
    recievedMessage.innerHTML = content;
    document.getElementById("chat-message-area").appendChild(recievedMessage);
    twemoji.parse(recievedMessage);
    ScrollChat();
}

window.onload = function () {
    var socket = io.connect('/chat');

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

    function SendMessage() {
        var text = document.getElementById('chat-box-textarea').value;
        if (text != "") {
            socket.emit('message', text);
            document.getElementById('chat-box-textarea').value = '';
        }
    }

    socket.on('connect', function () {
        AddChatMessage("<b>Connected.</b>");
    });

    socket.on('message', function (message) {
        AddChatMessage(`<b>${message.user}:</b> ${message.message}`);
    });

    socket.on('connection', function (data) {
        AddChatMessage(`<b>${data.data}</b>`);
    });

    socket.on('disconnection', function (data) {
        AddChatMessage(`<b>${data.data}</b>`);
    });
}

