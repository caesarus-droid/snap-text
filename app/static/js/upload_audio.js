document.getElementById("audioFile").addEventListener("change", function () {
    const uploadBox = document.getElementById("upload-box");
    const progressSection = document.getElementById("progress-section");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    const metadataForm = document.getElementById("metadata-form");
    const fileInput = document.getElementById('audioFile');
    const fileNameDiv = document.getElementById('file-name');

    // Handle the file selection and display file name
    displayFileName(fileInput, fileNameDiv);

    // Hide the upload box and show the progress section
    uploadBox.style.display = "none";
    progressSection.style.display = "block";

    let progress = 0;
    const interval = setInterval(() => {
        if (progress >= 100) {
            clearInterval(interval);
            progressText.innerHTML = "Upload Complete!";
            setTimeout(() => {
                progressSection.style.display = "none";
                metadataForm.style.display = "block";
            }, 1000);
        } else {
            progress += 20;
            progressBar.style.width = progress + "%";
        }
    }, 500);
});

// Function to display the file name and give feedback
function displayFileName(fileInput, fileNameDiv) {
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        // Check if the file type is audio
        if (file.type.startsWith('audio/')) {
            fileNameDiv.textContent = 'Selected file: ' + file.name;
            fileNameDiv.style.color = 'green'; // Green for success
        } else {
            fileNameDiv.textContent = 'Error: Please upload a valid audio file.';
            fileNameDiv.style.color = 'red'; // Red for error
        }
    } else {
        fileNameDiv.textContent = 'No file selected';
        fileNameDiv.style.color = 'black'; // Reset color if no file is selected
    }
}

function addField() {
        let container = document.getElementById("extra-fields");

        let div = document.createElement("div");
        div.classList.add("field-group");

        // Label Name Input
        let labelInput = document.createElement("input");
        labelInput.type = "text";
        labelInput.name = "extra_labels[]"; // Array format for Flask
        labelInput.placeholder = "Label Name (e.g., Lecture Duration)";
        labelInput.required = true;
        div.appendChild(labelInput);

        // Value Input
        let valueInput = document.createElement("input");
        valueInput.type = "text";
        valueInput.name = "extra_values[]"; // Array format for Flask
        valueInput.placeholder = "Value (e.g., 45 minutes)";
        valueInput.required = true;
        div.appendChild(valueInput);

        // Remove Button
        let removeButton = document.createElement("button");
        removeButton.classList.add("remove-btn");
        removeButton.innerText = "Remove";
        removeButton.onclick = function(event) {
            event.preventDefault();
            container.removeChild(div);
        };
        div.appendChild(removeButton);

        // Add separator line
        let separator = document.createElement("hr");
        container.appendChild(div);
        container.appendChild(separator);
}