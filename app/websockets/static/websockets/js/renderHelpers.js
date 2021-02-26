// export const myMessageRender = (messages) => {

//     //let outerDiv = document.createElement("div");
//     //outerDiv.classList.add('myMessageWrapper')
//     let chat_container = document.querySelector('.chatContent')
//     let fragment = document.createDocumentFragment();
//     messages.forEach(m => {
//         // !!!УБЕРИ!!!
//         let photo_url = m.photo.split('://')
//         let photo_url_2 = 'http://' + photo_url[1]
//         let time = getLocaltime(m.date_created)

//         if (m.user_id !== my_id) {
//             let myMessageWrapper = document.createElement('div')
//             myMessageWrapper.classList.add('myMessageWrapper')

//             myMessageWrapper.innerHTML = ` <div class="myPhotoWrapper">
//                 <img src=${m.photo ? photo_url_2 : './icons/defaultUserPhoto.svg'} alt="" class='userPhoto'>
//             </div>
//             <div class="myTextContent">
//                 ${m.content}
//             </div>
//             <div class="localTimeWrapper" style="margin-right: 25px;">
//                 <div class="localTimeContent">
//                 ${time}
//                 </div>
//                 <div class="deleteMessageWrap">
//                     <img src="./icons/delete_gray.svg" alt="" class="deleteMessageWrapImg">
//                 </div>
//             </div>`

//             fragment.appendChild(myMessageWrapper)
//         } else {
//             let oppponentMessageWrapper = document.createElement('div')
//             oppponentMessageWrapper.classList.add('opponentMessageWrapper')
//             oppponentMessageWrapper.insertAdjacentHTML('beforeend', ` <div class="opponentPhotoWrapper">
//                 <img src=${m.photo ? photo_url_2 : './icons/defaultUserPhoto.svg'} alt="" class='userPhoto'>
//             </div>
//             <div class="opponentTextContent">
//                 ${m.content}
//             </div>
//             <div class="localTimeWrapper" style="margin-left: 25px;">
//                 <div class="localTimeContent">
//                 ${time}
//                 </div>
//                 <div class="deleteMessageWrap">
//                     <img src="./icons/delete_gray.svg" alt="" class="deleteMessageWrapImg">
//                 </div>
//             </div>`)

//             fragment.appendChild(oppponentMessageWrapper)
//         }
//     })
//     chat_container.appendChild(fragment)
// }


// export const newMessageRender = (message) => {
//     let chat_container = document.querySelector('.chatContent')

//     // !!!УБЕРИ!!!
//     let photo_url = message.photo.split('://')
//     let photo_url_2 = 'http://' + photo_url[1]
//     let time = getLocaltime(message.date_created)

//     if (message.user_id !== my_id) {
//         let myMessageWrapper = document.createElement('div')
//         myMessageWrapper.classList.add('myMessageWrapper')

//         myMessageWrapper.innerHTML = ` <div class="myPhotoWrapper">
//                 <img src=${message.photo ? photo_url_2 : './icons/defaultUserPhoto.svg'} alt="" class='userPhoto'>
//             </div>
//             <div class="myTextContent">
//                 ${message.content}
//             </div>
//             <div class="localTimeWrapper" style="margin-right: 25px;">
//                 <div class="localTimeContent">
//                 ${time}
//                 </div>
//                 <div class="deleteMessageWrap">
//                     <img src="./icons/delete_gray.svg" alt="" class="deleteMessageWrapImg">
//                 </div>
//             </div>`

//         chat_container.insertAdjacentElement("beforeend", myMessageWrapper);
//     } else {
//         let opponentMessageWrapper = document.createElement('div')
//         opponentMessageWrapper.classList.add('opponentMessageWrapper')
//         opponentMessageWrapper.innerHTML = ` <div class="opponentPhotoWrapper">
//                 <img src=${message.photo ? photo_url_2 : './icons/defaultUserPhoto.svg'} alt="" class='userPhoto'>
//             </div>
//             <div class="opponentTextContent">
//                 ${message.content}
//             </div>
//             <div class="localTimeWrapper" style="margin-left: 25px;">
//                 <div class="localTimeContent">
//                 ${time}
//                 </div>
//                 <div class="deleteMessageWrap">
//                     <img src="./icons/delete_gray.svg" alt="" class="deleteMessageWrapImg">
//                 </div>
//             </div>`
//         chat_container.insertAdjacentElement("beforeend", opponentMessageWrapper);
//     }
// }