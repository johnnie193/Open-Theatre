import { setupInteractHelper } from "./gameMain.js";

/**
 * Adds a new role and synchronizes it with the interface and memory.
 * @param {number} index - The unique index of the role.
 * @param {string} [id=""] - The role's name; if not empty, it loads an existing role.
 * @param {Object} [character={}] - An object containing detailed information about the role (e.g., settings and initial memory).
 */
export function addRole(index, id = "", character = {}) {
    const rolesContainer = document.getElementById("roles");
    const addRoleButton = document.getElementById("add-role");
    const roleDiv = document.createElement("div");
    roleDiv.className = "role";
    roleDiv.dataset.index = index;
    roleDiv.innerHTML = `
        <input type="text" placeholder="Name" class="role-name" data-index="${index}" />
        <textarea contenteditable="true" placeholder="Profile" class="role-profile"></textarea>
        <button class="delete-role delete-btn">X</button>
    `;
    if(id) {
        roleDiv.querySelector('.role-name').value = id;
        roleDiv.querySelector('.role-profile').value = character.profile;
    }
    rolesContainer.appendChild(roleDiv, addRoleButton);
    createInitialMemory(index, id, character);
    syncRoleWithMemory(roleDiv, index, id);
    if(!id){
        roleDiv.querySelectorAll('input, textarea').forEach(function(input) {
            input.addEventListener('blur', function() {
                if (this.value.trim() !== '') {
                    this.classList.add('finished');
                } else {
                    this.classList.remove('finished');
                }
            });
        });
    }
}

/**
 * Creates the initial memory section for a role.
 * @param {number} index - The unique index of the role.
 * @param {string} [id=""] - The role's name.
 * @param {Object} [character={}] - An object containing the role's initial memory details.
 */
function createInitialMemory(index, id="", character={}) {
    const userMemoryContainer = document.querySelector(".initial-memories");
    const memoryDiv = document.createElement("div");
    memoryDiv.className = "memory-item";
    memoryDiv.dataset.index = index;
    memoryDiv.innerHTML = `
        <input type="text" class="initial-memory-name" readonly placeholder="Name" />
        <textarea contenteditable="true" placeholder="initial memories" class="role-profile"></textarea>
    `;
    if(id) {
        memoryDiv.querySelector('.initial-memory-name').value = id;
        console.log("memory", character.memory);
        if(character.memory.length){
            memoryDiv.querySelector('.role-profile').value = character.memory[0];
        }
    }
    userMemoryContainer.appendChild(memoryDiv);
}

/**
 * Synchronizes role information with its initial memory and handles deletion logic. Update the role selectors in scenes.
 * @param {HTMLElement} roleDiv - The HTML element representing the role.
 * @param {number} index - The unique index of the role.
 * @param {string} [id=""] - The role's name.
 */
function syncRoleWithMemory(roleDiv, index, id="") {
    const userMemoryContainer = document.querySelector(".initial-memories");
    const roleNameInput = roleDiv.querySelector(".role-name");
    const deleteButton = roleDiv.querySelector(".delete-role");
    const memoryDiv = userMemoryContainer.querySelector(`.memory-item[data-index="${index}"]`);
    const memoryNameInput = memoryDiv.querySelector(".initial-memory-name");
    roleNameInput.addEventListener("input", () => {
        memoryNameInput.value = roleNameInput.value.trim();
        updateSceneSelectors();
    });
    deleteButton.addEventListener("click", () => {
        roleDiv.remove();
        memoryDiv.remove();
        updateSceneSelectors();
    });
    memoryDiv.querySelectorAll('input, textarea').forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value.trim() !== '') {
                this.classList.add('finished');
            } else {
                this.classList.remove('finished');
            }
        });
    });
    if(id){
        memoryNameInput.value = roleNameInput.value.trim();
        updateSceneSelectors();
    }
}

/**
 * Updates the role selectors for all scenes to ensure consistency with the current role list.
*/
function updateSceneSelectors() {
    const roleSelects = document.querySelectorAll(".role-select");
    roleSelects.forEach(select => {
        updateRoleSelect(select);
    });
}

/**
 * Updates the options of a single role selector.
 * @param {HTMLElement} select - The HTML element for the role selector.
 */
function updateRoleSelect(select) {
    let roles = Array.from(document.querySelectorAll(".role-name"))
        .map(input => input.value.trim())
        .filter(name => name !== "");
    const currentValue = select.value; 
    select.innerHTML = `<option value="">-- Select roles --</option>`; 
    console.log(roles);
    
    roles.forEach(role => {
        const option = document.createElement("option");
        option.value = role;
        option.textContent = role;
        if (role === currentValue) {
            option.selected = true; 
        }
        select.appendChild(option);
    });
}

/**
 * Adds a new scene and sets up its content and related interactions.
 * @param {number} index - The unique index of the scene.
 * @param {string} scene_id - The ID of the scene.
 * @param {Object} [scene_data={}] - An object containing detailed information about the scene (e.g., story chains, transitions).
 */
export function addScene(index, scene_id, scene_data={}) {
    const addSceneButton = document.getElementById("add-scene");
    const sceneDiv = document.createElement("div");
    const scenesContainer = document.getElementById("scenes-container");
    sceneDiv.className = "scene";
    sceneDiv.dataset.index = index; 
    sceneDiv.innerHTML = `
        <div class="scene-block">
        <h4>scene${index+1}</h4>
        <div class="user-input-row">
            <label>Scene Name:</label>
            <input type="text" class="scene-name" placeholder="Please input the name of the scene..." />
        </div>
        <div class="user-input">
            <label>Scene Information:</label>
            <textarea contenteditable="true" class="scenes-info" placeholder="Please input background information for this scene"></textarea>
        </div>
        <div class="radio-group">
            <label class="title">Architecture Selection:</label>
            <label class="radio-option active">
                <input type="radio" name="agent-${index+1}" value="v1" checked/>
                <span class="custom-radio"></span>
                v1 mode - One-for-All
            </label>
            <label class="radio-option">
                <input type="radio" name="agent-${index+1}" value="v2" />
                <span class="custom-radio"></span>
                v2 mode - Director-Actor
            </label>
            <label class="radio-option">
                <input type="radio" name="agent-${index+1}" value="v2_plus" />
                <span class="custom-radio"></span>
                v2_plus mode - Director-multi-Actor
            </label>
            <label class="radio-option">
                <input type="radio" name="agent-${index+1}" value="v2_prime" />
                <span class="custom-radio"></span>
                v2_prime mode - Director-multi-Actor
            </label>
            <label class="radio-option">
                <input type="radio" name="agent-${index+1}" value="v3" />
                <span class="custom-radio"></span>
                v3 mode - Hybrid Architecture
            </label>
        </div>
        <div class="scene-memory">
            <label>Character Motivation:</label>
                <! -- 角色过渡记忆插入 -->
            <button class="add-scene-memory add-btn" >+</button>

        </div>
        <div class="user-input chains">
            <label>Plotlines:</label>
                <!-- 剧情链动态插入 -->
            <button class="add-chain add-btn">+</button>
        </div>
        </div>
        <button class="delete-scene delete-btn">Delete scene</button>
    `;
//     <div class="user-input jumpall">
//     <label>跳转:</label>
//     <div class="jumps">
//         <!-- 触发动态插入 -->
//     </div>
//     <button class="add-jump add-btn">+</button>
// </div>
    scenesContainer.insertBefore(sceneDiv, addSceneButton);
    if(scene_id && scene_data.scene){
        // console.log(scene_data);
        // var scene_data_info = scene_data.scene.replace(/\\n/g,"<br>");
        sceneDiv.querySelector(".scenes-info").innerHTML = scene_data.scene;
    }
    if(scene_id && scene_data.name){
        // console.log(scene_data);
        // var scene_data_info = scene_data.scene.replace(/\\n/g,"<br>");
        console.log("name",scene_data.name);
        sceneDiv.querySelector(".scene-name").value = scene_data.name;
    }
    console.log("mode",scene_data.mode)
    if(scene_id && scene_data.mode){
        if (scene_id && scene_data.mode) {
            // 遍历所有 radio 选项，清除 checked 和 active
            sceneDiv.querySelectorAll('.radio-option').forEach(option => {
                const input = option.querySelector('input[type="radio"]');
                // option.classList.remove('active'); // 移除 active 样式
                input.checked = false; // 取消选中状态
                console.log(input)
            });
        
            // 设置当前选中的 radio 选项
            const radioButton = sceneDiv.querySelector(`input[type="radio"][value="${scene_data.mode}"]`);
            console.log(radioButton);
            if (radioButton) {
                radioButton.checked = true; // 设置为选中状态
                sceneDiv.querySelectorAll('.radio-option').forEach(option => {
                    const input = option.querySelector('input[type="radio"]');
                    input.classList.remove('checked');
                    console.log(input)
                });
                radioButton.classList.add('checked');
            }
            sceneDiv.querySelectorAll('.radio-option').forEach(radio => {
                radio.addEventListener('change', () => {
                    // 确保其他 radio 的 checked 状态被清除
                    // sceneDiv.querySelectorAll('.radio-option').forEach(otherRadio => {
                    //     otherRadio.checked = false; // 清除其他 radio 的选中状态
                    // });
                    const radio_ = radio.querySelector('input[type="radio"]');
                    // 设置当前 radio 为选中状态
                    // radio_.checked = true;
                    sceneDiv.querySelectorAll('.radio-option').forEach(option => {
                        const input = option.querySelector('input[type="radio"]');
                        input.classList.remove('checked');
                        console.log(input)
                    });
                    radio_.classList.add('checked');
                });
            });

        }
    }
    const addChainButton = sceneDiv.querySelector(".add-chain");
    addChainButton.addEventListener("click", () => {
        addChain(sceneDiv);
    }); 
    if (scene_id && Array.isArray(scene_data.chain) && scene_data.chain.length > 0) {
        for (let i = 0; i < scene_data.chain.length; i++) {
            if(scene_data.stream){
                // console.log("find stream", scene_data.stream)
                addChain(sceneDiv, scene_data.chain[i], scene_data.stream[scene_data.chain[i]]);
            } else {
                addChain(sceneDiv, scene_data.chain[i]);
            }
        }
    }
    const addSceneMemoryButton = sceneDiv.querySelector(".add-scene-memory");
    addSceneMemoryButton.addEventListener("click", () => {
        addSceneMemory(sceneDiv);
    });
    if(scene_id && typeof scene_data.characters === 'object'){
        for(var cid in scene_data.characters){
            addSceneMemory(sceneDiv, cid, scene_data.characters[cid]); 
        }
    }
    // const addJumpButton = sceneDiv.querySelector(".add-jump");
    // addJumpButton.addEventListener("click", () => {
    //     addJump(sceneDiv);
    // });
    const deleteSceneButton = sceneDiv.querySelector(".delete-scene");
    deleteSceneButton.addEventListener("click", () => {
        sceneDiv.remove();
        updateSceneSelectors();
    });

    /**
     * Adds a story chain to the specified scene.
     * @param {HTMLElement} sceneDiv - The HTML element representing the scene.
     * @param {string} [chain_data=""] - The content of the story chain.
     */
    function addChain(sceneDiv, chain_data="", details_data=[]) {
        const chainsContainer = sceneDiv.querySelector(".chains");
        const chainDiv = document.createElement("div");
        chainDiv.className = "chain";
        chainDiv.innerHTML = `
            <input class="chain-data" type="text" placeholder="Please input the plotline" />
            <button class="delete-chain delete-btn">X</button>
            <div class="details">
                <button class="add-detail add-btn">Add plot details</button>
            </div>
        `;
        if(chain_data){
            chainDiv.querySelector(".chain-data").value = chain_data;
        }
        chainsContainer.appendChild(chainDiv);
        const deleteChainButton = chainDiv.querySelector(".delete-chain");
        deleteChainButton.addEventListener("click", () => {
            chainDiv.remove();
        });
    
        const addDetailButton = chainDiv.querySelector(".add-detail");
        addDetailButton.addEventListener("click", () => {
            addDetail(chainDiv);
        });
        
        if(chain_data && Array.isArray(details_data) && details_data.length > 0){
            for(let i = 0; i < details_data.length; i++){
                addDetail(chainDiv, details_data[i]);
            }
        }

        sceneDiv.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value.trim() !== '') {
                    this.classList.add('finished');
                } else {
                    this.classList.remove('finished');
                }
            });
        });

        function addDetail(chainDiv, detail_data=""){
            const detailDiv = document.createElement("div");
            detailDiv.className = "detail";
            detailDiv.innerHTML = `
                <textarea class="detail-data" type="text" placeholder="Please input the detailed plots for this plotline" ></textarea>
                <button class="delete-detail delete-btn">X</button>
            `;
            if(detail_data){
                detailDiv.querySelector(".detail-data").value = detail_data;
            }
            chainDiv.querySelector(".details").appendChild(detailDiv);
    
            const deleteDetailButton = detailDiv.querySelector(".delete-detail");
            deleteDetailButton.addEventListener("click", () => {
                detailDiv.remove();
            });
    
            detailDiv.querySelector(".detail-data").addEventListener("blur", function() {
                if (this.value.trim() !== '') {
                    this.classList.add('finished');
                } else {
                    this.classList.remove('finished');
                }
            });    
        }
    }

    /**
     * Adds role transition memory functionality to a scene.
     * @param {HTMLElement} sceneDiv - The HTML element representing the scene.
     * @param {string} [cid] - The ID of the role.
     * @param {Object} [memory_data={}] - An object containing transition memory details.
     */
    function addSceneMemory(sceneDiv, cid, scene_memory_data) {
        console.log("add scene memory", cid);
        const scenememoriesContainer = sceneDiv.querySelector(".scene-memory");
        const scenememoryDiv = document.createElement("div");
        scenememoryDiv.className = "scene-memory-item";
    
        scenememoryDiv.innerHTML = `
            <select class="role-select">
                <option value="">-- Select roles --</option>
            </select>
            <textarea placeholder="Character Motivation" contenteditable="true" class="role-profile"></textarea>
            <button class="delete-scene-memory delete-btn">X</button>
        `; 
        //  <input type="text" placeholder="角色名" />
        scenememoriesContainer.appendChild(scenememoryDiv);
        const rolesSelect = sceneDiv.querySelectorAll(".role-select");
        rolesSelect.forEach(roleSelect => {
            updateRoleSelectFromNames(roleSelect);         
        });
        // 删除角色过渡记忆按钮绑定
        const deleteSceneMemoryButton = scenememoryDiv.querySelector(".delete-scene-memory");
        deleteSceneMemoryButton.addEventListener("click", () => {
            scenememoryDiv.remove();
        });
        scenememoryDiv.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value.trim() !== '') {
                    this.classList.add('finished');
                } else {
                    this.classList.remove('finished');
                }
            });
        });
        if(cid){
            scenememoryDiv.querySelector(".role-select").value = cid;
            scenememoryDiv.querySelector(".role-profile").value = scene_memory_data;
        }
    }

    function updateRoleSelectFromNames(select) {
        const currentValue = select.value;  
        const roleNames = Array.from(document.querySelectorAll(".role-name"))
            .map(input => input.value.trim())
            .filter(name => name !== ""); 
    
        select.innerHTML = `<option value="">-- Select roles --</option>`; 
    
        roleNames.forEach(name => {
            const option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            if (name === currentValue) {
                option.selected = true; // 保持已选中的值
            }
            select.appendChild(option);
        });
    
    }

    // /**
    //  * Sets up the logic for scene jumps and connects it with story chains and memory transitions.
    //  * @param {HTMLElement} sceneDiv - The HTML element representing the scene.
    //  * @param {Object} [jump_data={}] - An object containing the jump logic details.
    //  */
    // function addJump(sceneDiv) {
    //     const jumpContainer = sceneDiv.querySelector(".jumps");
    //     const jumpDiv = document.createElement("div");
    //     jumpDiv.className = "jump-item";
    
    //     jumpDiv.innerHTML = `
    //             <div class="trigger-block">
    //             <input type="text" placeholder="触发逻辑" />
    //             <div class="strike">
    //             <select class="role-select">
    //                 <option value="">-- 选择触发 --</option>
    //                 <option value="scene">场景</option>
    //                 <option value="action">动作</option>
    //             </select>
    //             <input type="text" placeholder="触发的动作或场景名（如：场景1）" />
    //             </div>
    //             <div class="jump-tags">
    //             <label>触发项</label>
    //             <button class="add-jump-tag add-btn">+</button>
    //                     <!-- 触发tag动态插入 -->
    //             </div>
    //             </div>
    //             <button class="delete-jump delete-btn">X</button>
    //         `;
    //     jumpContainer.appendChild(jumpDiv);
    
    //     const deleteJumpButton = jumpDiv.querySelector(".delete-jump");
    //     deleteJumpButton.addEventListener("click", () => {
    //         jumpDiv.remove();
    //     });
    
    //     const addJumpTagButton = jumpDiv.querySelector(".add-jump-tag");
    //     addJumpTagButton.addEventListener("click", () => {
    //         addJumpTag(jumpDiv);
    //     });
    
    //     jumpDiv.querySelectorAll('input, textarea').forEach(input => {
    //         input.addEventListener('blur', function() {
    //             if (this.value.trim() !== '') {
    //                 this.classList.add('finished');
    //             } else {
    //                 this.classList.remove('finished');
    //             }
    //         });
    //     });
    
    //     function addJumpTag(jumpDiv) {
    //         const jumpTagContainer = jumpDiv.querySelector(".jump-tags");
    //         const jumpTagDiv = document.createElement("div");
    //         jumpTagDiv.className = "jump-tag";
    
    //         jumpTagDiv.innerHTML = `
    //             <input type="text" placeholder="输入触发项内容" />
    //             <button class="delete-jump-tag delete-btn">X</button>
    //         `;
    //         jumpTagContainer.appendChild(jumpTagDiv);
    
    //         // 删除角色过渡记忆按钮绑定
    //         const deleteJumpTagButton = jumpTagDiv.querySelector(".delete-jump-tag");
    //         deleteJumpTagButton.addEventListener("click", () => {
    //             jumpTagDiv.remove();
    //         });
    
    //         jumpTagDiv.querySelectorAll('input').forEach(input => {
    //             input.addEventListener('blur', function() {
    //                 if (this.value.trim() !== '') {
    //                     this.classList.add('finished');
    //                 } else {
    //                     this.classList.remove('finished');
    //                 }
    //             });
    //         });
    
    //     }
    // }
}

/**
 * Updates the main panel UI with the latest data.
 * @param {Object} data - The data object containing updated world, scene, and script details.
 */
export function updateMainPanel(data){
    document.querySelector('#main-container #world-name').innerText = data.id || document.querySelector('#main-container #world-name').innerText;
    var scene_title = document.querySelector('#main-container #world-name').innerText;
    if(data.scenes[`scene${data.scene_cnt}`].id){
        if(data.scenes[`scene${data.scene_cnt}`].name){
            scene_title = `Scene ${data.scene_cnt}  ${data.scenes[`scene${data.scene_cnt}`].name}`;
        } else {
            scene_title = `Scene ${data.scene_cnt}`;
        }
    }
    document.querySelector('#scene #scene-id').innerText = scene_title;
    var scene_info = data.scenes[`scene${data.scene_cnt}`].info.replace(/\\n/g,"<br>");
    document.querySelector('#scene #scene-info').innerHTML = scene_info || document.querySelector('#main-container #world-name').innerText;                
    document.querySelector('#current-script #script-name').value = data.id || document.querySelector('#current-script #script-name').value;
    document.querySelector('#current-script #background').value = data.script.background.narrative || document.querySelector('#current-script #background').value;
    document.querySelector('#current-script #player-name').value = data.script.background.player || document.querySelector('#current-script #player-name').value;
}

/**
 * Synchronizes the current state of the script with the server.
 */
export function syncToServer() {
    console.log("开始同步");
    const scriptId = document.querySelector('#current-script #script-name').value
    const scriptBackgroundNarrative = document.querySelector('#current-script #background').value
    const playerName = document.querySelector('#current-script #player-name').value
    const memoriesData = Array.from(document.querySelectorAll(".memory-item")).reduce((acc, memoryDiv) => {
        const key = memoryDiv.querySelector(".initial-memory-name").value.trim(); // 第一个输入框的值作为键
        const value = memoryDiv.querySelector(".role-profile").value.trim(); // 第二个输入框的值作为值
        if (key) { // 确保键非空
            acc[key] = value;
        }
        return acc;
    }, {});
    const rolesData = Array.from(document.querySelectorAll(".role")).map(roleDiv => {
        const roleId = roleDiv.querySelector(".role-name").value.trim();
        return {
            id: roleId,
            profile: roleDiv.querySelector(".role-profile").value.trim(),
            initial_memory: memoriesData[roleId] ? memoriesData[roleId] : ""
        };
    });
    const scenesData = Array.from(document.querySelectorAll(".scene")).reduce((acc, sceneDiv) => {
        const sceneTitle = sceneDiv.querySelector("h4").innerText.trim(); // 获取场景标题（如：场景1、场景2）
        const sceneName = sceneDiv.querySelector(".scene-name").value.trim(); 
        const sceneInfo = sceneDiv.querySelector(".scenes-info").value.trim(); // 获取场景信息
        const chains = Array.from(sceneDiv.querySelectorAll(".chain")).map(chainDiv => {
            return chainDiv.querySelector(".chain-data").value.trim(); // 提取剧情链内容
        });
        const streams = Array.from(sceneDiv.querySelectorAll(".chain")).reduce((acc, chainDiv) => {
            const chainData = chainDiv.querySelector(".chain-data").value.trim(); // 提取 chain-data
            const details = Array.from(chainDiv.querySelectorAll(".detail-data")).map(detailInput => 
                detailInput.value.trim() // 提取 detail-data
            ).filter(detail => detail !== ""); // 忽略空值
            if (chainData) {
                acc[chainData] = details; // 设置 key-value 对
            }
            return acc;
        }, {});
        const jumps = Array.from(sceneDiv.querySelectorAll(".jumps > .jump")).map(jumpDiv => {
            return jumpDiv.value.trim(); // 提取跳转逻辑内容
        });
        const sceneMemory = Array.from(sceneDiv.querySelectorAll(".scene-memory-item")).reduce((acc, scenesMemoryDiv) => {
            const key = scenesMemoryDiv.querySelector(".role-select").value.trim(); // 第一个输入框的值作为键
            const value = scenesMemoryDiv.querySelector(".role-profile").value.trim(); // 第二个输入框的值作为值
            if (key) { 
                acc[key] = value;
            }
            return acc;
        }, {});
        let sceneMode = "v1"; // 默认值
        const scenemodediv = sceneDiv.querySelectorAll('.radio-option input[type="radio"]:checked');
        
        if (scenemodediv) {
            for (const radio of scenemodediv) {
                console.log("radio", radio);
                if (radio.checked) {
                    sceneMode = radio.value;
                    console.log("Current sceneMode:", sceneMode);
                }
            }
        } 
        // put the scene information together
        acc[sceneTitle] = {
            sceneName: sceneName,
            sceneInfo: sceneInfo,
            chains: chains,
            streams: streams,
            // jumps: jumps,
            characters: sceneMemory,
            mode: sceneMode
        };
        return acc;
    }, {});
    
    var data = {
        id: scriptId,
        background_narrative: scriptBackgroundNarrative,
        player_name: playerName,
        characters: rolesData, 
        scenes: scenesData,
        storageMode: true
    }
    console.log("send data", data)
    fetch('/api/data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if(data.error){
            document.querySelectorAll('#info-box').forEach(function(infoBox) {
                infoBox.innerHTML = `
                    <p>${data.error}<p>
                    `;
            })
            return;
        }
        updateInfoPanel(data);
        updateMainPanel(data);
        const scriptBox = document.querySelector('#allscript #info-box');
        const formatContent = formatOutput(data.script, data.scene_cnt, data.nc);
        scriptBox.innerHTML = `
            <h3>Script</h3>
            <pre>${formatContent}</pre>
            `;            
    })
    .catch(error => {
        console.error('加载角色信息时出错:', error);
    });
}

/* 
    Handle the save config logic, sync to server and update main panel and info panel.
*/
export function saveConfig(){
    document.getElementById("save-config").addEventListener('click', () => {
        syncToServer();
        function autoResizeInput(element) {
            element.style.height = "auto"; 
            element.style.height = `${element.scrollHeight}px`; 
        }
        document.querySelectorAll("input, textarea").forEach(function(input) {
            if(input.classList.contains('fixedsize')){
                return;
            }
            autoResizeInput(input);
        });
        setupInteractHelper();
    });
}

export function formatOutput(data, scene_id, nc) {
    let output = `<br><b>Script name：</b> ${data.id} <br>
<b>Player's name:</b> ${data.background.player} <br>
<b>Characters with their profiles:</b><br><br>`;
    for (const [name, description] of Object.entries(data.background.characters)) {
        output += `&nbsp;&nbsp;${name}: ${description ? description : " None"} <br>`;
    }
    output += `<b>Background narrative:</b> ${data.background.narrative} <br>
<b>Characters' initial memories: </b>`
    if(data.background.context && typeof(data.background.context) == "object"){
        output += `<br><br>`
        for (const [name, description] of Object.entries(data.background.context)) {
            output += `&nbsp;&nbsp;${name}: ${description ? description : " None"} <br>`;
        }
    } else {
        output += ` None<br>`
    }

    if(data.scenes && typeof(data.scenes) == "object"){
        for (const sceneKey in data.scenes) {
            const scene = data.scenes[sceneKey];
            console.log("sceneKey",`scene${scene_id}`)
            let sceneStyle = sceneKey == `scene${scene_id}` ? 'style="background-color: yellow; font-weight: bold;"' : '';
            output += `<br><b ${sceneStyle}>${sceneKey}: </b> <br>
    <b>Scene Name: </b> ${scene.name ? scene.name : " None"} <br>
    <b>Scene Information: </b> ${scene.scene} <br>
    <b>Architecture: </b> ${scene.mode} <br>
    <b>Character Motivation:</b><br><br>`
            for (const [name, description] of Object.entries(scene.characters)) {
                output += `&nbsp;&nbsp;${name}: ${description ? description : " None"}  <br><br>`;
            }
            output += `<b>Plotlines: </b><br><br>`;
            
            // Format chain with distinction
            if (scene.chain && scene.chain.length > 0) {
                scene.chain.forEach((item) => {
                    if (sceneKey == `scene${scene_id}`) {
                        console.log("Nc",nc);
                        const isTrue = nc.some(([entry, status]) => entry == item && status);
                        let style = isTrue ? 'style="color: green; font-weight: bold; font-style: italic"' : 'style="color: gray; font-style: italic"';
                        output += `&nbsp;&nbsp;<span ${style}>${item}</span> <br>`;
                    } else {
                        let style = 'style="font-style: italic"'
                        output += `&nbsp;&nbsp;<span ${style}>${item}</span> <br>`;
                    }
                    if (scene.stream && item in scene.stream) {
                        scene.stream[item].forEach((line) => {
                            output += `&nbsp;&nbsp;${line} <br>`;
                        });
                    }
                    output += `<br>`
                });
            } else {
                output += ` None <br>`;
            }
        }
        output += "<br>";
    }

    return output;
}

/*
 update the info panel when sync to server
 */
export function updateInfoPanel(data){
    const scriptBox = document.querySelector('#allscript #info-box');
    const formatContent = formatOutput(data.script, data.scene_cnt, data.nc);
    scriptBox.innerHTML = `
        <h3>Script</h3>
        <pre>${formatContent}</pre>
        `;
    const characterDiv = document.querySelector("#characters .character-list");
    characterDiv.innerHTML = "";
    // console.log("data[chara", data.characters);
    Object.entries(data.characters).forEach(([name, _]) => {
        const characterElement = document.createElement("div");
        characterElement.className = "character";
        characterElement.setAttribute("data-name", name);

        const characterImage = `assets/${name}.jpg`;
        const imgElement = document.createElement("img");
        imgElement.src = characterImage;
        imgElement.alt = name;
        imgElement.onerror = function () {
            imgElement.src = "assets/default_agent.jpg";
        };

        const nameElement = document.createElement("p");
        nameElement.textContent = name;
        characterElement.appendChild(imgElement);
        characterElement.appendChild(nameElement);
        characterDiv.appendChild(characterElement);

        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'file-input';
        fileInput.accept = 'image/*'; // 只允许图片文件
        fileInput.style.display = 'none'; // 默认隐藏
        
        // 将文件输入框添加到目标容器中
        characterDiv.appendChild(fileInput);
    });

    const playerDiv = document.querySelector("#footer #player");
    playerDiv.innerHTML = "";
    // 创建图片元素
    // console.log("player",data);
    const playerImage = document.createElement("img");
    playerImage.src = `assets/${data.script.background.player}.jpg`; 
    playerImage.onerror = function () {
        playerImage.src = "assets/default_player.jpg"; 
    };
    const playerName = document.createElement("p");
    playerName.textContent = data.script.background.player;
    playerDiv.appendChild(playerImage);
    playerDiv.appendChild(playerName);
}

function beautifyObjecthelper(obj, indent = 0) {
    let beautified = '';
    let indentString = ' '.repeat(indent);
 
    function boldKey(key) {
        return `<strong>${key}</strong>`;
    }

    if (Array.isArray(obj)) {
        obj.forEach(item => {
            beautified += `${beautifyObjecthelper(item, indent + 1)}\n`;
        });
    } else if (typeof obj === 'object' && obj !== null) {
        Object.keys(obj).forEach(key => {
            let value = obj[key];
            if (typeof value === 'object' && value !== null) {
                beautified += `${indentString}${boldKey(key)}:\n${beautifyObjecthelper(value, indent + 1)}`;
            } else {
                beautified += `${indentString}${boldKey(key)}: ${value}\n`;
            }
        });
    } else {
        beautified += `${indentString}${obj}`;
    }
    return beautified;
    // return `<pre>${beautified.replace(/\n/g, '<br/>').replace(/\s/g, '&nbsp;')}</pre>`;
}

export function beautifyObject(obj, indent = 0){
    return `<pre style="font-family: 'Times New Roman', serif;">${beautifyObjecthelper(obj, indent).replace(/\n/g, '<br/>')}</pre>`;
}
  

// function setupChatWithdraw(){
//     clearInfoPanel();
//     const withdrawButton = document.getElementById('drawback-btn');
//     const chatContent = document.getElementById('chat-content');
//     withdrawButton.addEventListener('click', () => {
//         fetch('/withdraw', {
//             method: 'GET',
//         })
//         .then(response => response.json())
//         .then(data => {
//             if (data.mode === 'v1') {
//                 // Remove the last two messages if they exist
//                 const messages = chatContent.querySelectorAll('p');
//                 if (messages.length > 0) {
//                     chatContent.removeChild(messages[messages.length - 1]);
//                 }
//                 if (messages.length > 1) {
//                     chatContent.removeChild(messages[messages.length - 2]);
//                 }
//             }
//         })
//         .catch(error => {
//             console.error('Error during withdraw:', error);
//         });
//     });
// }