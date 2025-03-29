document.addEventListener("DOMContentLoaded", () => {
    fetch('/prompt', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        console.log("Prompt settings saved:", data);
        Object.keys(data).forEach(key => {
            const input = document.querySelector(`#${key}`);
            console.log(`#${key}`)
            console.log(input)
            if (input) {
                input.value = data[key];
                const lineHeight = parseInt(window.getComputedStyle(input).lineHeight, 10) || 20;
                const emptyLines = (input.value.match(/^\s*$/gm) || []).length;
                const totalLines = input.value.split('\n').length;
                const totalHeight = (totalLines + emptyLines) * lineHeight;
                input.style.height = `${totalHeight}px`; // 调整高度            }
                console.log("lines",totalLines);
        }
        })
    })
    .catch(error => {
        console.error("Error fetching initial prompt:", error);
    });
    let updated_prompt = {
        "prompt_drama_v1": "",
        "prompt_drama_v2": "",
        "prompt_character": "",
        "prompt_character_v2": ""
    };
    document.getElementById("save-prompt").addEventListener("click", () => {
        Object.keys(updated_prompt).forEach(key => {
            const input = document.querySelector(`textarea#${key}`);
            if (input) {
                updated_prompt[key] = input.value;
            }
        });        
        fetch('/prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updated_prompt)
        })
        .then(response => response.json())
        .then(data => {
            if(data.error){
                const infoParagraph = document.querySelector('#mode p');
                if(data.error){
                    infoParagraph.textContent = data.error;
                } 
            }
        })
        .catch(error => {
            console.error("Error saving prompt:", error);
        });
    });
})

