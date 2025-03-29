import { loadScript } from "./loadScript.js";

document.querySelector(".save-script").addEventListener("click", () => saveScript());
/**
 * Saves the current script state.
 * This function sends a GET request to the server to save the current script and updates the UI with the result.
 */
function saveScript(){
    fetch('/save', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        const infoParagraph = document.querySelector('#save-game p');
        if(data.error){
            infoParagraph.textContent = data.error;
            return;
        } else {
            infoParagraph.textContent = data.info;
        }
        const loadDiv = document.querySelector("#load-game");
        const buttonHTML = `<button class="load-script" id="load-script-${data.save_id}">${data.save_id}</button>`;
        loadDiv.innerHTML += buttonHTML; 
        document.querySelectorAll(".load-script").forEach(script => 
            script.addEventListener("click", () => loadScript(script))
        );
    })
    .catch(error => {
        console.error('保存剧本时出错:', error);
    });
}