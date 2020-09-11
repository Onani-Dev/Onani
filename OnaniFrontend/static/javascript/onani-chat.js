/*
 * @Author: Blakeando
 * @Date:   2020-09-10 02:40:26
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-11 16:22:47
 */
'use strict';
var currentRoom = "general";
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
    document.getElementById('chat-box-textarea').value = '';
    if (text != "") {
      var splitText = text.split(" ");
      if (splitText[0].startsWith("/")) {
        switch (splitText[0].replace("/", "")) {
          case "join":
            if (splitText.length > 1) {
              ConnectTo(splitText[1]);
            }
            return;

          case "clear":
            document.getElementById("chat-message-area").innerHTML = "";
            return;
        }
      }
      socket.emit('message', { "text": text, "room": currentRoom });
    }
  }

  function ConnectTo(room, reconnect = false, leavePrevious = true) {
    if (leavePrevious) {
      socket.emit('leave', { "room": currentRoom });
    }
    socket.emit('join', { "room": room, "reconnect": reconnect });
    currentRoom = room;
    // AddChatMessage(`You joined <b>${currentRoom}</b>`);
    document.getElementById('chat-box-textarea').placeholder = `Send message to ${currentRoom}...`;
  }

  // function Disconnect() {
  //   socket.emit('leave', { "room": currentRoom });
  // }

  socket.on('connect', function () {
    AddChatMessage("<b>Connected.</b>");
    AddChatMessage("Type /join {room} to join another room.");
    ConnectTo(currentRoom);
  });

  socket.on('message', function (message) {
    AddChatMessage(`<a style="text-decoration:none;" href="/users/${message.user_id}"><b>${message.user}:</b></a> ${message.message}`);
  });

  socket.on('connection', function (data) {
    AddChatMessage(`<b>${data.data}</b>`);
  });

  socket.on('disconnection', function (data) {
    AddChatMessage(`<b>${data.data}</b>`);
  });

  socket.on('notification', function (data) {
    AddChatMessage(`<b>${data.data}</b>`);
  });
}

