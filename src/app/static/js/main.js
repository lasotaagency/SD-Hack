const image = document.getElementById("uploaded-image");
const coordinatesDisplay = document.getElementById("coordinates");
const inputText = document.getElementById("input-text");
const inputImage = document.getElementById("input-image"); // Declare inputImage only once
const submitDataBtn = document.getElementById("submit-data");
const resetBtn = document.getElementById("reset");

let selectedCoordinates = { x: 0, y: 0 };

function replaceUploadedWithGeneratedImage(imageUrl) {
    const uploadedImage = document.getElementById("uploaded-image");
    uploadedImage.src = imageUrl;
}

function clearGeneratedImages() {
    const generatedImagesContainer = document.getElementById("generated-images");
    while (generatedImagesContainer.firstChild) {
        generatedImagesContainer.removeChild(generatedImagesContainer.firstChild);
    }

    const uploadedImage = document.getElementById("uploaded-image");
    if (uploadedImage) {
        uploadedImage.src = "";
    }
}

if (image) {
    image.addEventListener("click", (e) => {
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        selectedCoordinates = { x, y };
        coordinatesDisplay.textContent = `Selected coordinates: (${x.toFixed(0)}, ${y.toFixed(0)})`;
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const textOption = document.getElementById('text-option');
    const imageOption = document.getElementById('image-option');

    function updateInputDisplay() {
        if (textOption.checked) {
            inputText.style.display = 'inline-block';
            inputImage.style.display = 'none';
        } else if (imageOption.checked) {
            inputText.style.display = 'none';
            inputImage.style.display = 'inline-block';
        }
    }

    textOption.addEventListener('change', updateInputDisplay);
    imageOption.addEventListener('change', updateInputDisplay);

    updateInputDisplay();
});

if (submitDataBtn) {
    submitDataBtn.addEventListener("click", async () => {
        const selectedOption = document.getElementById("options").value;
        const textOption = document.getElementById('text-option');
        const conditionType = textOption.checked ? "text" : "image";
        let conditionData;

        if (conditionType === "text") {
            const text = inputText.value.trim();
            if (text === '') {
                alert("Please enter some text");
                return;
            }
            conditionData = text;
        } else {
            const file = inputImage.files[0];
            if (!file) {
                alert("Please select an image to upload");
                return;
            }
            const formData = new FormData();
            formData.append("additional_image", file);

            // Upload the additional image
            const uploadResponse = await fetch("/upload_additional_image", {
                method: "POST",
                body: formData,
            });

            if (!uploadResponse.ok) {
                alert("Failed to upload the additional image. Please try again.");
                return;
            }

            const uploadData = await uploadResponse.json();
            conditionData = uploadData.image_url;
        }

        const response = await fetch("/submit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                image_url: image.src,
                coordinates: [selectedCoordinates.x, selectedCoordinates.y],
                option: selectedOption,
                condition_type: conditionType,
                condition_data: conditionData,
            }),
        });

        const data = await response.json();
        if (data.status === "success") {
            alert("Data submitted successfully!");

            replaceUploadedWithGeneratedImage(data.generated_images[0]);

            // Display the generated images
            const generatedImagesContainer = document.getElementById("generated-images");
            generatedImagesContainer.style.display = "block"; // Make the container visible
            data.generated_images.forEach((imageUrl) => {
                const img = document.createElement("img");
                img.src = imageUrl;
                img.alt = "Generated Image";
                generatedImagesContainer.appendChild(img);
            });
        } else {
            alert("Failed to submit data. Please try again.");
        }
    });
}

if (resetBtn) {
    resetBtn.addEventListener("click", () => {
        clearGeneratedImages();
    });
}