import { addRole, addScene, saveConfig, updateMainPanel, updateInfoPanel, formatOutput } from "./utils.js";
import { setupInteractHelper } from "./gameMain.js"

// 页面加载时重置
document.addEventListener('DOMContentLoaded', () => {
    resetData();
});

function resetData(){
    const scriptDiv = document.querySelector("#current-script")
    scriptDiv.innerHTML = `
        <h2>Current script</h2>
        <div class="user-input-row">
            <label for="script-name">Script name:</label>
            <input type="text" id="script-name" placeholder="Please input the name of the script..." />
        </div>
        <div class="user-input-row">
            <label for="player-name">Player name:</label>
            <input type="text" id="player-name" placeholder="Please input the name of the player..." />
        </div>
        <div id="roles">
            <label>Characters:</label>
            <!-- 添加角色按钮 -->
            <button id="add-role" class="add-btn">+</button>
        </div>
        <div class="user-input">
            <label for="background">Background narrative:</label>
            <textarea id="background" placeholder="Please input the background narrative..."></textarea>
        </div>
        <div class="initial-memories">
            <label>Initial memories for characters:</label>
        </div>
        <div id="scenes-container">
            <h3>Scene list</h3>
            <button id="add-scene">Add scene</button>
        </div>
        <button id="save-config">Save configuration</button>   
    `
    console.log("reset");
    
    // 重新绑定添加角色按钮事件
    const addRoleButton = document.getElementById("add-role");
    let roleIndex = 0;
    addRoleButton.addEventListener("click", () => {
        addRole(roleIndex);
        roleIndex++;
    });

    // 重新绑定添加场景按钮事件
    const addSceneButton = document.getElementById("add-scene");
    let sceneIndex = 0;
    addSceneButton.addEventListener("click", () => {
        addScene(sceneIndex);
        sceneIndex++;
    });

    // 清空聊天记录
    const chatContent = document.getElementById('chat-content');
    if(chatContent) {
        chatContent.innerHTML = '';
        // 清空所有消息元素
        const messages = chatContent.querySelectorAll('.message');
        messages.forEach(message => message.remove());
    }
    // const chatInput = document.querySelector('#chat-input input');
    // chatInput.value = ' '
    // const infoBox = document.getElementById('info-box');
    // infoBox.innerHTML =
    //     `
    //     <h3>Information Box</h3>
    //     <p>Select a character or the buttons below to see details.</p>
    //     `
    const defaultHTML = {
        "allscript": `                                
                <h3>Script</h3>
                <p>Create your own script or load a default script to start the game!</p>
        `,
        "characters-info": `
                <h3>Characters Information</h3>
                <p>Select a character to see details.</p>
        `,
        "dramallm": `
                <h3>System Feedbacks</h3>
                <p>Start the game and check how the director operates.</p>
        `,
        "allmemory": `
                <h3>Records</h3>
                <p>Check the records.</p>
        `
    };

    // 遍历每个 info-interface 并重置内容
    Object.keys(defaultHTML).forEach(id => {
        const interfaceElement = document.querySelector(`#${id} #info-box `);
        if (interfaceElement) {
            interfaceElement.innerHTML = defaultHTML[id];
        }
    });

    // 重新绑定保存配置按钮事件
    const saveConfigButton = document.getElementById("save-config");
    if(saveConfigButton) {
        saveConfigButton.addEventListener("click", saveConfig);
    }

    // 发送重置请求到服务器
    saveConfig();
}

function preloadData(data) {
    // 加载角色
    console.log("data", data)
    const addRoleButton = document.getElementById("add-role");
    let index = 0;
    // initializeSync();
    for (var char_id in data.characters) {
        // console.log(`${char_id}: ${data.characters[char_id]}`);
        addRole(index, char_id, data.characters[char_id])
        index = index + 1;
    }
    // function initializeSync() {
    //     const existingRoles = rolesContainer.querySelectorAll(".role");
    //     existingRoles.forEach((role, index) => {
    //         syncRoleWithMemory(role, index);
    //     });
    // }
    addRoleButton.addEventListener("click", () => {
        addRole(index);
        index++; // 索引递增
    });
    const addSceneButton = document.getElementById("add-scene");
    let sceneIndex = 0; // 用于场景索引管理
    // 添加新场景
    if("scenes" in data.script){
        for (var scene_id in data.script.scenes) {
            if(scene_id != "id" && scene_id != "background" && "chain" in data.script.scenes[scene_id]){
                addScene(sceneIndex, scene_id, data.script.scenes[scene_id])
                sceneIndex = sceneIndex + 1;
            }
        }
    }
    addSceneButton.addEventListener("click", () => {
        addScene(sceneIndex);
        sceneIndex++; // 索引递增
    });

}

export function loadScript(script) {
    console.log("Loading script for:", script.id);
    fetch('/load', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ script_name: script.id }),
    })
    .then(response => response.json())
    .then(data => {
        resetData();
        console.log('world', data);
        updateMainPanel(data);
        preloadData(data);
        updateInfoPanel(data);
        setupInteractHelper();
        document.querySelectorAll('input, textarea').forEach(function(input) {
            if (input.value.trim() !== '') {
                input.classList.add('finished');
            } else {
                input.classList.remove('finished');
            }
        });
    })
    .catch(error => {
        console.error('加载剧本时出错:', error);
    });
}

document.querySelectorAll(".load-script").forEach(script => 
    script.addEventListener("click", () => loadScript(script))
);