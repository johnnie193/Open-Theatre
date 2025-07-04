import { addRole, addScene } from "./utils.js";

// Event listener to ensure the DOM is fully loaded before executing any scripts
document.addEventListener("DOMContentLoaded", () => {
    const rolesContainer = document.getElementById("roles");
    initializeSync();
    document.getElementById("add-role").addEventListener("click", () => {
        const roleIndex = rolesContainer.querySelectorAll(".role").length; 
        addRole(roleIndex);
    });
    function initializeSync() {
        const existingRoles = rolesContainer.querySelectorAll(".role");
        existingRoles.forEach((role, index) => {
            syncRoleWithMemory(role, index);
        });
    }

    document.querySelectorAll('input, textarea').forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value.trim() !== '') {
                this.classList.add('finished');
            } else {
                this.classList.remove('finished');
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const addSceneButton = document.getElementById("add-scene");
    let sceneIndex = 0; 
    addSceneButton.addEventListener("click", () => {
        addScene(sceneIndex);
        sceneIndex++; 
    });
});