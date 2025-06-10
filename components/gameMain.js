import { saveConfig, updateMainPanel, updateInfoPanel } from "./utils.js";
import { updateInfoPanelBySubmit, setupHelp, updateCharacterInfo } from "./infoManager.js" 
document.addEventListener('DOMContentLoaded', () => {
    setupCharacterSelection();
    setupInteract();
    setupChatSubmit();
    setupHelp();
});

// Save the configuration
saveConfig();

/**
 * Sets up the character selection functionality.
 * This function handles character selection and displays relevant information about the selected character.
 */
function setupCharacterSelection() {
    const characterDiv = document.querySelector("#characters .character-list");
    characterDiv.addEventListener('dblclick', (event) => {
        const fileInput = document.getElementById('file-input');
        const character = event.target.closest('.character');
        fileInput.click(); // 触发文件选择窗口
        fileInput.addEventListener('change', (event) => {
            const file = event.target.files[0]; // 获取选择的文件
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = character.querySelector('img'); // 查找内部的 <img> 元素
                    if (img) {
                        img.src = e.target.result;
                        const formData = new FormData();
                        formData.append('file', file); // `file` 是用户选择的文件
                        formData.append('name', img.alt);
                        fetch('/upload', {
                            method: 'POST',
                            body: formData,
                        })
                            .then(response => response.json())
                            .then(data => {
                                console.log('File uploaded successfully:', data);
                            })
                            .catch(error => {
                                console.error('Error uploading file:', error);
                            });
                    } else {
                        console.error('The character does not have an <img> element.');
                    }
                };
                reader.readAsDataURL(file); // 读取文件为 Data URL
            }
        });
    });
    
    characterDiv.addEventListener('click', (event) => {
        const character = event.target.closest('.character');
        if (!character) return; // Ensure that a character element is clicked

        // Remove selected state from all characters
        const characters = characterDiv.querySelectorAll('.character');
        characters.forEach(char => char.classList.remove('selected'));

        character.classList.add('selected');
        const characterName = character.getAttribute('data-name');
        updateCharacterInfo(characterName);
    });
}

function setupInteract() {
    document.getElementById('action-select').addEventListener('change', () => {
        setupInteractHelper();
    })
}

export function setupInteractHelper() {
    const additionalInput = document.getElementById('additional-input');
    const selectedValue = document.getElementById('action-select').value;
    
    // 完全清空additional-input
    document.getElementById("additional-input").innerHTML = "";
    console.log("additionalInput", additionalInput);
    // if (selectedValue === '-speak') {
    const multiSelect = document.createElement('select');
    let options = ['null']; 
    
    // 创建输入框
    const inputField = document.createElement('input');
    inputField.type = 'text';
    inputField.placeholder = 'Type your message and Press Enter or submit [IF YOU SELECT SPEAK]';
    const submitButton = document.getElementById('submit-btn');
    inputField.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            submitButton.click();
        }
    });

    fetch('/api/info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ help: "characters" }),
    })
    .then(response => response.json())
    .then(data => {
        if(!data.error){
            options = data.characters;
        }
        // 清空现有选项
        multiSelect.innerHTML = '';
        // 添加新选项
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            multiSelect.appendChild(opt);
        });
        console.log("additionalInput", additionalInput);
        // 只添加一次元素
        if (!additionalInput.contains(multiSelect) || !additionalInput.contains(inputField)) {
            additionalInput.innerHTML = "";
            additionalInput.appendChild(multiSelect);
            additionalInput.appendChild(inputField);
        }
    })
    .catch(error => {
        console.error('加载角色信息时出错:', error);
    });
    // }
}

/**
 * Sets up the chat submission functionality.
 * This function handles sending messages in the chat and receiving character responses.
 */
function setupChatSubmit() {
    const submitButton = document.getElementById('submit-btn');
    const chatContent = document.getElementById('chat-content');
    const nextSceneButton = document.getElementById('next-scene-btn');
    const backSceneButton = document.getElementById('back-scene-btn');
    const withdrawButton = document.getElementById('withdraw-btn');
    const exportRecordButton = document.getElementById('save-record');
    nextSceneButton.addEventListener('click', () => {
        fetch('/api/interact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interact: "next"}),
        })
        .then(response => response.json())
        .then(data => {
            if(data){
                updateMainPanel(data);
                // updateInfoPanel(data);
                setupInteractHelper();
            }
        })
        .catch(error => {
            console.error("Error fetching initial prompt:", error);
        });
    })

    backSceneButton.addEventListener('click', () => {
        fetch('/api/interact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interact: "back"}),
        })
        .then(response => response.json())
        .then(data => {
            if(data){
                updateMainPanel(data);
                // updateInfoPanel(data);
                setupInteractHelper();
            }
        })
        .catch(error => {
            console.error("Error fetching initial prompt:", error);
        });
    })

    withdrawButton.addEventListener('click', () => {
        fetch('/api/interact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interact: "withdraw"}),
        })
        .then(response => response.json())
        .then(data => {
            if(data.cnt){
                console.log("cnt:" , data.cnt);
                function deleteLastMessages(cnt) {
                    // 获取所有 .message 元素
                    let messages = document.querySelectorAll('#chat-content .message');
                    // 删除最后 cnt 条消息
                    for (let i = 0; i < cnt; i++) {
                        if (messages.length > 0) {
                            messages[messages.length - 1].remove();  // 删除最后一个 message
                            messages = document.querySelectorAll('#chat-content .message');
                        }
                    }
                }
                deleteLastMessages(data.cnt)
            }
            updateInfoPanelBySubmit();
        })
        .catch(error => {
            console.error("Error fetching initial prompt:", error);
        });
    })

    submitButton.addEventListener('click', () => {
        const playerName = document.querySelector('#player p').textContent;
        const interaction_type = document.getElementById('action-select').value;
        let interaction_object = "";
        if(document.querySelector('#additional-input select')){
            interaction_object = document.querySelector('#additional-input select').value;
        }
        const chatInput = document.querySelector('#additional-input input');
        let message = "";
        if(chatInput){
            message = chatInput.value.trim();
            chatInput.value = " ";
        }
        fetch('/api/interact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type: interaction_type, message: message, object: interaction_object}),
        })
        .then(response => response.json())
        .then(data => {
            if(data.error) {
                document.querySelectorAll('#info-box').forEach(function(infoBox) {
                    infoBox.innerHTML = `
                        <p>${data.error}<p>
                        `;
                })
                return;            
            }
            console.log(data.done);
            if(data.done){
                console.log("done");
                updateMainPanel(data.state);
            }
            let newMessagediv = null;
            console.log("response",data.action);
            if(data.input.x == "-speak"){
                const playerImgSrc = document.getElementById('player').querySelector('img').src; // 获取图片的 src
                // 创建新的消息容器
                newMessagediv = document.createElement('div');
                newMessagediv.classList.add('message'); // 为容器添加类名便于样式控制
    
                // 创建玩家头像及名称的容器
                const playerContainer = document.createElement('div');
                playerContainer.classList.add('message-character');
                // 创建头像元素
                const playerImg = document.createElement('img');
                playerImg.src = playerImgSrc;
                playerImg.alt = playerName;
                playerImg.classList.add('message-img'); // 可选：为图片添加样式
                // 创建名称元素
                const playerText = document.createElement('p');
                playerText.textContent = playerName;
                playerText.classList.add('message-name'); // 可选：为名称添加样式
                // 将头像和名称添加到玩家容器中
                playerContainer.appendChild(playerImg);
                playerContainer.appendChild(playerText);
    
                // 创建消息文本
                const messageText = document.createElement('div');
                let message = "";
                if(Array.isArray(data.input.bid) && data.input.bid.length > 0){
                    message = "@";
                    for(let i = 0; i < data.input.bid.length; i++){
                        message += ` ${data.input.bid[i]}`;
                        if(i != data.input.bid.length - 1){
                            characterMessage += `,`;
                        }                                 
                    }
                }
                message += "  ";
                message += data.input.content;
                messageText.textContent = message;
                messageText.classList.add('message-text');
    
                // 将玩家容器和消息文本添加到消息容器中
                newMessagediv.appendChild(playerContainer);
                newMessagediv.appendChild(messageText);
                // 将新消息添加到聊天内容中
                chatContent.appendChild(newMessagediv);
            }
            console.log("data.action", data.action);
            if(Array.isArray(data.action) && data.action.length > 0){
                for(let i = 0; i < data.action.length; i++){
                    let action = data.action[i];
                    if(action.x == "-speak"){
                        const characterName = action.aid;
                        let characterMessage = "";
                        if(Array.isArray(action.bid) && action.bid.length > 0){
                            characterMessage = "@";
                            for(let i = 0; i < action.bid.length; i++){
                                characterMessage += ` ${action.bid[i]}`;
                                if(i != action.bid.length - 1){
                                    characterMessage += `,`;
                                }                        
                            }
                        } 
                        else if (typeof data.action.bid == 'string'){
                            // characterContainer = "s";
                            characterMessage = `@ ${action.bid}`;
                        }

                        characterMessage += "  ";
                        characterMessage += action.content;
                        // const newMessage = document.createElement('p');
                        // newMessage.textContent = `${characterName}: ${characterMessage}`;
                        // const character = document.querySelector(`.character[data-name=${characterName}]`);

                        const characterImgSrc = document.querySelector(`.character[data-name="${characterName}"]`).querySelector('img').src; // 获取图片的 src
                        // 创建新的消息容器
                        const newMessagediv = document.createElement('div');
                        newMessagediv.classList.add('message'); // 为容器添加类名便于样式控制
            
                        // 创建玩家头像及名称的容器
                        const characterContainer = document.createElement('div');
                        characterContainer.classList.add('message-character');
                        // 创建头像元素
                        const characterImg = document.createElement('img');
                        characterImg.src = characterImgSrc;
                        characterImg.alt = characterName;
                        characterImg.classList.add('message-img'); // 可选：为图片添加样式
                        // 创建名称元素
                        const characterText = document.createElement('p');
                        characterText.textContent = characterName;
                        characterText.classList.add('message-name'); // 可选：为名称添加样式
                        // 将头像和名称添加到玩家容器中
                        characterContainer.appendChild(characterImg);
                        characterContainer.appendChild(characterText);
            
                        // 创建消息文本
                        const messageText = document.createElement('div');
                        messageText.textContent = characterMessage;
                        messageText.classList.add('message-text');
            
                        // 将玩家容器和消息文本添加到消息容器中
                        newMessagediv.appendChild(characterContainer);
                        newMessagediv.appendChild(messageText);
                        // 将新消息添加到聊天内容中
                        chatContent.appendChild(newMessagediv);                  
                        chatContent.scrollTop = chatContent.scrollHeight;
                    }
                }
                updateInfoPanelBySubmit();
            }
            if(data.done){
                console.log("done");
                updateMainPanel(data.state);
                updateInfoPanel(data.state);
                setupInteractHelper();
            }
        })
    });

    exportRecordButton.addEventListener('click', () => {
        fetch('/api/info', {  
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ help: "export_records" })
        })
        .then(response => {
            if (!response.ok) throw new Error('导出失败');
            return response.blob();
        })
        .catch(error => {
            console.error('导出错误:', error);
            alert('导出失败，请重试！');
        });
    });
}
