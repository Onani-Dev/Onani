/*
 * @Author: kapsikkum
 * @Date:   2020-09-10 02:40:26
 * @Last Modified by:   kapsikkum
 * @Last Modified time: 2020-10-31 23:04:00
 */
'use strict';
let currentRoom = "general";
let scrolled = false;

const messageArea = document.getElementById("chat-message-area");
const inputArea = document.getElementById('chat-box-textarea');
const customEmotes = /(:don:|:katsu:|:desuwa:|:dirt:|:armagan:)/g
const emojiTable = {
  don: "/svg/don.svg",
  katsu: "/svg/katsu.svg",
  desuwa: "/svg/desuwa.svg",
  dirt: "/image/dirt_small.gif",
  armagan: "/image/armagan_small.gif"
}


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
  if (!scrolled) {
    messageArea.scrollTop = messageArea.scrollHeight;
  }
}

function AddChatMessage(content) {
  if (messageArea.childElementCount >= 150) {
    messageArea.removeChild(messageArea.childNodes[0]);
  }
  var recievedMessage = document.createElement("li");
  recievedMessage.innerHTML = content;
  messageArea.appendChild(recievedMessage);
  twemoji.parse(recievedMessage);
  ScrollChat();
}

document.addEventListener('DOMContentLoaded', init, false);
function init() {
  const socket = io.connect('/chat');

  let connectMessage = document.createElement("li");
  connectMessage.innerHTML = "<b>Connecting...</b>";
  messageArea.appendChild(connectMessage);
  document.getElementById("chat-box-send").addEventListener("click", function () { SendMessage(); })
  inputArea.addEventListener("keypress", function (e) {
    if (e.key == "Enter") {
      e.preventDefault();
      SendMessage();
    }
  })

  function SendMessage(text = inputArea.value) {
    inputArea.value = '';
    if (text != "") {
      let splitText = text.split(" ");
      if (splitText[0].startsWith("/")) {
        switch (splitText[0].replace("/", "")) {
          case "join":
            if (splitText.length > 1) {
              ConnectTo(splitText[1]);
            }
            return;

          case "clear":
            messageArea.innerHTML = "";
            return;

          case "shrug":
            SendMessage(`¯\\_(ツ)_/¯`);
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
    inputArea.placeholder = `Send message to ${currentRoom}...`;
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
    let msg = message.message.replace(customEmotes, (current) => {
      return `<img src='${emojiTable[current.replace(/:/g, "")]}' class='emoji' draggable='false' alt='${current}'></img>`
    });
    AddChatMessage(`<a style="text-decoration:none;cursor:pointer;" title="Double click to view profile, or Right click to open profile in a new tab." onauxclick="window.open('/users/${message.user_id}', '_blank').focus();" ondblclick="location.href='/users/${message.user_id}'"><b>${message.user}:</b></a> ${msg}`);
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

