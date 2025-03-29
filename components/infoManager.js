import {formatOutput, beautifyObject} from "./utils.js"

export function updateCharacterInfo(characterName) {
    const infoBox = document.querySelector("#characters #info-box");
    fetch('/info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role: characterName }),
    })
    .then(response => response.json())
    .then(data => {
        if(!data.error){
            infoBox.innerHTML = `
            <h3>${characterName}</h3>
            <h4>Profile</h4>
            <p>${data.profile}</p>
            <h4>Memory</h4>
            <p>${data.memory.join('<br>')}</p>
            <h4>React</h4>
            `
            if(data.prompts && Array.isArray(data.prompts) && data.prompts.length > 0){
                const formatContent = (str) => 
                    str.replace(/&/g, "&amp;")
                       .replace(/</g, "&lt;")
                       .replace(/>/g, "&gt;")
                       .replace(/\\n/g, "<br>");

                infoBox.innerHTML += `
                    ${beautifyObject(data.prompts[0])}
                <b>Prompt</b>
                `;
                infoBox.innerHTML += `
                <pre>${formatContent(data.prompts[1])}</pre>
                `;
            }
        }else{
            infoBox.innerHTML = `
            <h3>${data.error}</h3>
            `
        }
    })
    .catch(error => {
        console.error('加载角色信息时出错:', error);
    });
}

function updateWorldRecord() {
    const memoryinfoBox = document.querySelector('#allmemory #info-box');
    fetch('/info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ help: "allmemory" }),
    })
    .then(response => response.json())
    .then(data => {
        if(!data.error && data.allmemory!={}){
            console.log("memory",data.allmemory);
            let memoryContent = `
    <h3>Records</h3>
    <button id="save-record" class="export-button">Export Records</button>
            `
            for (let scene in data.allmemory) {
                memoryContent += `<h4>${scene}</h4>`; 
                memoryContent += '<ul>'; // Start an unordered list to display the scene's statements
                data.allmemory[scene].forEach(statement => {
                    memoryContent += `<li>${statement}</li>`; // Add each statement as a list item
                });
                memoryContent += '</ul>'; 
            }
            memoryinfoBox.innerHTML = memoryContent;
            document.getElementById('save-record').addEventListener('click', () => {
                fetch('/info', {  
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
        }else{
            memoryinfoBox.innerHTML = `
            <h3>${data.error}</h3>
            `
        }
    })
    .catch(error => {
        console.error('加载角色信息时出错:', error);
    });
}

function updateOpenTheatre() {
    const dramallmBox = document.querySelector('#dramallm #info-box');
    fetch('/info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ help: "dramallm" }),
    })
    .then(response => response.json())
    .then(data => {
        console.log("dramallm",data);
        if(!data.error && data.dramallm){
            dramallmBox.innerHTML = `
            <h3>System Feedbacks</h3>
            `;
            if(Array.isArray(data.dramallm) && data.dramallm.length > 0){
                console.log("dramallm array",data);
                const formatContent = (str) => 
                    str.replace(/&/g, "&amp;")
                       .replace(/</g, "&lt;")
                       .replace(/>/g, "&gt;")
                       .replace(/\\n/g, "<br>");
                for(let i = 0; i < data.dramallm.length; i++){
                    if(data.dramallm[i] == "v1" || data.dramallm[i] == "v2"){
                        dramallmBox.innerHTML += `
                        <b>${data.dramallm[i]}</b>
                        `;
                        dramallmBox.innerHTML += `
                            ${beautifyObject(data.dramallm[i+1])}
                        `;
                        dramallmBox.innerHTML += `
                        <b>Prompt</b>
                        `;
                        dramallmBox.innerHTML += `
                        <pre>${formatContent(data.dramallm[i+2])}</pre>
                        `;
                        i = i + 2;
                    }
                }
            }
        } else {
            dramallmBox.innerHTML = `
            <h3>${data.error}</h3>
            `
        }
    })
    .catch(error => {
        console.error('加载角色信息时出错:', error);
    });
}

function updateScript() {
    const scriptBox = document.querySelector('#allscript #info-box');
    fetch('/info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ help: "allscript" }),
    })
    .then(response => response.json())
    .then(data => {
        console.log("script_data",data)
        if(!data.error && data.allscript){
            const formatContent = formatOutput(data.allscript, data.scene_cnt, data.nc);
            scriptBox.innerHTML = `
            <h3>Script</h3>
            <pre>${formatContent}</pre>
            `;
        }else{
            scriptBox.innerHTML = `
            <h3>${data.error}</h3>
            `
        }
    })
    .catch(error => {
        console.error('加载角色信息时出错:', error);
    });
}

export function updateInfoPanelBySubmit(){
    const helpDiv = document.querySelector(".choose-panel .active");
    console.log("helpdiv", helpDiv);
    if (helpDiv.id == "allscript") {
        updateScript();
    } else if(helpDiv.id == "allmemory"){
        updateWorldRecord();
    } else if(helpDiv.id == "dramallm"){
        updateOpenTheatre();
    } else if(helpDiv.id == "characters-info"){
        const characterDiv = document.querySelector(".character-list .selected");
        console.log("selected characterdiv", characterDiv);
        if(characterDiv){
            const characterName = characterDiv.getAttribute('data-name');
            updateCharacterInfo(characterName);
        }
    }
}

/**
 * Sets up the help buttons for Memory or DramaLLM related content.
 * This function handles clicks on help buttons to fetch and display relevant data.
 */
export function setupHelp() {
    const memoryDiv = document.querySelector("#allmemory.icon");
    const dramallmDiv = document.querySelector("#dramallm.icon");
    const scriptDiv = document.querySelector('#allscript.icon');
    memoryDiv.addEventListener('click', () => {
        updateWorldRecord();
    })
    dramallmDiv.addEventListener('click', () => {
        updateOpenTheatre();
    })
    scriptDiv.addEventListener('click', () => {
        updateScript();
    })

}