{% load static %}
{% load i18n %}
let socket = new WebSocket('ws://18.230.134.205:80/ws/operation-chat/'+ CHAT_ID + '/?token=' + TOKEN);
socket.onerror = function(error) {
    console.log(`[error] ${error.message}`);
};

function getLocaltime(message_time) {
    let time = new Date("2021-02-08 11:32:10.676574+00:00");
    return time.toLocaleString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true })
}


let messages = [];
let message = '';


let myMessageRender = (messages) => {
        let chat_container = document.querySelector('.chatContent')
        let fragment = document.createDocumentFragment();

        messages.forEach(m => {

                    let time = getLocaltime(m.date_created)


                    if (m.user_id === my_id) {
                        let myMessageWrapper = document.createElement('div')
                        myMessageWrapper.classList.add('myMessageWrapper')

                        myMessageWrapper.innerHTML = ` <div class="myPhotoWrapper">
                <img width="40" height="40" src=${m.photo ? m.photo : "{% static 'icons/defaultUserPhoto.svg' %}"} alt="" class='userPhoto'>
            </div>
            ${m.content 
                ?  `<div class="myTextContent">
                        ${m.content}
                    </div>`
                : `<div class="myFileMessageContent">
                        <a class="iconWrapper" href=${m.files[0]} target='_blank'>
                            <img src="{% static 'icons/upload-file-svgrepo-com.svg' %}" alt="">
                        </a>
                        <span>${m.files[0].split('/').reverse()[0]}</span>  
                    </div>`
            }
            <div class="localTimeWrapper" style="margin-right: 25px;">
                <div class="localTimeContent">
                ${time}
                </div>
                <div class="deleteMessageWrap" id=${m.id}>
                    <img width="15" height="15" src="{% static 'icons/delete_gray.svg' %}" alt="" class="deleteMessageWrapImg">
                </div>
            </div>`
            fragment.appendChild(myMessageWrapper)

        } else {
            let oppponentMessageWrapper = document.createElement('div')
            oppponentMessageWrapper.classList.add('opponentMessageWrapper')
            oppponentMessageWrapper.innerHTML = ` <div class="opponentPhotoWrapper">
                <img src=${m.photo ? m.photo : "{% static 'icons/defaultUserPhoto.svg' %}"} alt="" class='userPhoto'>
            </div>
            ${m.content 
                ? `<div class="opponentTextContent">
                        ${m.content}
                    </div>`
                : `<div class="opponentFileMessageContent">
                        <a class="iconWrapper" href=${m.files[0]} target='_blank'>
                            <img src="{% static 'icons/upload-file-svgrepo-com.svg' %}" alt="">
                        </a>
                        <span>${m.files[0].split('/').reverse()[0]}</span>  
                    </div>`
            }
            <div class="localTimeWrapper" style="margin-left: 25px;">
                <div class="localTimeContent">
                ${time}
                </div>
                
            </div>`
            fragment.appendChild(oppponentMessageWrapper)
        }
    })
    chat_container.appendChild(fragment)

    let delete_icons = document.querySelectorAll('.deleteMessageWrap')
    delete_icons.forEach((icon) => {
        icon.addEventListener('click', () => {
            let id = icon.getAttribute('id')
            socket.send(JSON.stringify({ "command": "delete_message", "message_id": id }))
        })
    })

    chat_container.scrollTop = chat_container.scrollHeight
}

let newMessageRender = (message) => {
        let chat_container = document.querySelector('.chatContent')

        let time = getLocaltime(message.date_created)

        if (message.user_id === my_id) {
            let myMessageWrapper = document.createElement('div')
            myMessageWrapper.classList.add('myMessageWrapper')

            myMessageWrapper.innerHTML = ` <div class="myPhotoWrapper">
                <img width="40" height="40" src=${message.photo ? message.photo : "{% static 'icons/defaultUserPhoto.svg' %}"} alt="" class='userPhoto'>
            </div>
            ${message.content 
                ?  `<div class="myTextContent">
                        ${message.content}
                    </div>`
                : `<div class="myFileMessageContent">
                        <a class="iconWrapper" href=${'http://' + message.files[0].split('://')[1]} target='_blank'>
                            <img src="{% static 'icons/upload-file-svgrepo-com.svg' %}" alt="">
                        </a>
                        <span>${message.files[0].split('/').reverse()[0]}</span>  
                    </div>`
            }
            <div class="localTimeWrapper" style="margin-right: 25px;">
                <div class="localTimeContent">
                ${time}
                </div>
                <div class="deleteMessageWrap" id=${message.id}>
                    <img width="15" height="15" src="{% static 'icons/delete_gray.svg' %}" alt="" class="deleteMessageWrapImg">
                </div>
            </div>`

        chat_container.insertAdjacentElement("beforeend", myMessageWrapper);
        let delete_icon = document.getElementById(message.id)
        delete_icon.addEventListener('click', () => {
            let id = delete_icon.getAttribute('id')
            socket.send(JSON.stringify({ "command": "delete_message", "message_id": id }))
        })
    } else {
        let opponentMessageWrapper = document.createElement('div')
        opponentMessageWrapper.classList.add('opponentMessageWrapper')
        opponentMessageWrapper.innerHTML = ` <div class="opponentPhotoWrapper">
                <img src=${message.photo ? message.photo : "{% static 'icons/defaultUserPhoto.svg' %}"} alt="" class='userPhoto'>
            </div>
            ${message.content 
                ? `<div class="opponentTextContent">
                        ${message.content}
                    </div>`
                : `<div class="opponentFileMessageContent">
                        <a class="iconWrapper" href=${'http://' + message.files[0].split('://')[1]} target='_blank'>
                            <img src="{% static 'icons/upload-file-svgrepo-com.svg' %}" alt="">
                        </a>
                        <span>${message.files[0].split('/').reverse()[0]}</span> 
                    </div>`
            }
            <div class="localTimeWrapper" style="margin-left: 25px;">
                <div class="localTimeContent">
                ${time}
                </div>
            </div>`
        chat_container.insertAdjacentElement("beforeend", opponentMessageWrapper);
    }
    chat_container.scrollTop = chat_container.scrollHeight
}

let messagesRenderAfterDelete = (messages) => {
    let chat_container = document.querySelector('.chatContent')
    chat_container.innerHTML = ''
    myMessageRender(messages)
}


//send message
let messageInput = document.querySelector('.messageInput')
let sendIcon = document.querySelector('.sendIconWrapper')


sendIcon.addEventListener('click', () => {
    message.length > 0 && socket.send(JSON.stringify({ 'command': 'new_message', 'message': message, "files": [] }))
    message = ''
    messageInput.value = ''
    socket.send(JSON.stringify({ "command": "stop_typing_message", "user_id": my_id }))
})

messageInput.addEventListener('keydown', (event) => {

    message = event.target.value.replace(/(<([^>]+)>)/gi, '')
    if (event.key === 'Enter' && !event.shiftKey) {
        //event.preventDefault()
        socket.send(JSON.stringify({ 'command': 'new_message', 'message': event.target.value, "files": [] }))
        messageInput.value = ''
        message = ''
        socket.send(JSON.stringify({ "command": "stop_typing_message", "user_id": my_id }))
    } else {
        event.target.value.length === 2 &&
            (event.key !== 'Delete') &&
            (event.key !== 'Backspace') &&
            socket.send(JSON.stringify({ "command": "typing_message", "user_id": my_id }))

        event.target.value.length <= 1 &&
            socket.send(JSON.stringify({ "command": "stop_typing_message", "user_id": my_id }))
    }
})


const typingGifRender = (res) => {

    let chat_container = document.querySelector('.chatContent')

    if (res.user_id !== my_id) {
        let opponentMessageWrapper = document.createElement('div')
        opponentMessageWrapper.classList.add('typingMessageWrapper')

        opponentMessageWrapper.innerHTML = `
            <div class="typingPhotoWrapper">
                    <img src=${res.photo ? res.photo:"{% static 'icons/defaultUserPhoto.svg' %}" } alt="" class='userPhoto'>
                </div>
                <div class="typingIconWrapper">
                    <img src="{% static 'icons/giphy.gif' %}" alt="">
                </div>
               `

        chat_container.insertAdjacentElement("beforeend", opponentMessageWrapper);
    }
}
const removeTypingGifHandler = () => {
    const removed_gif_wrap = document.querySelector('.typingMessageWrapper')
    removed_gif_wrap && removed_gif_wrap.remove()
}


//file loader
let uploadInput = document.querySelector('.uploadInput')
uploadInput.addEventListener('change', (e) => {
    const formData = new FormData();
    let file = e.target.files[0];
    formData.append('file', file)

    fetch('http://18.230.134.205:80/api/v1/websockets/file/', {
            method: 'POST',
            headers: {
                "Authorization": 'JWT ' + TOKEN
            },
            body: formData
        })
        .then(res => res.json())
        .then(res => {
            console.log(res);
            socket.send(JSON.stringify({ 'command': 'new_message', 'message': '', "files": res.id ? [res.id] : [] }))
        })
        .catch(e => console.log('file_error', e))
})

const wsChatHelper = (res) => {

    switch (res.command) {
        case 'messages':
            {
                messages = [...messages, ...res.messages]
                res.messages.length > 0 && myMessageRender(res.messages);
                break
            }
        case 'typing_message':
            {
                typingGifRender(res)
                break
            }
        case 'stop_typing_message':
            {
                removeTypingGifHandler()
                break
            }
        case 'new_message':
            {
                messages.push(res.message)
                newMessageRender(res.message)
                break
            }

        case 'delete_message':
            {
                messages = messages.filter(m => m.id != res.message_id)
                messagesRenderAfterDelete(messages.filter(m => m.id != res.message_id))
            }
        default:
            return null
    }
}

socket.onopen = function(e) {
    console.log("[open] Соединение установлено");
    console.log("Отправляем данные на сервер");
};

socket.onmessage = function(event) {
    //console.log(`[message] Данные получены с сервера: ${event.data}`);
    wsChatHelper(JSON.parse(event.data))
};

socket.onclose = function(event) {
    if (event.wasClean) {
        console.log(`[close] Соединение закрыто чисто, код=${event.code} причина=${event.reason}`);
    } else {
        // например, сервер убил процесс или сеть недоступна
        // обычно в этом случае event.code 1006
        console.log('[close] Соединение прервано');
        console.log(event)
    }
};
