const image = document.getElementById("uploaded-image");
const coordinatesDisplay = document.getElementById("coordinates");
const inputText = document.getElementById("input-text");
const submitDataBtn = document.getElementById("submit-data");

let selectedCoordinates = { x: 0, y: 0 };

if (image) {
    image.addEventListener("click", (e) => {
        const rect = e.target.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        selectedCoordinates = { x, y };
        coordinatesDisplay.textContent = `Selected coordinates: (${x.toFixed(0)}, ${y.toFixed(0)})`;
    });
}

if (submitDataBtn) {
    submitDataBtn.addEventListener("click", async () => {
        const text = inputText.value.trim();
        if (text === '') {
            alert("Please enter some text");
            return;
        }
        const response = await fetch("/submit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                image_url: image.src,
                coordinates: [selectedCoordinates.x, selectedCoordinates.y],
                text: text,
            }),
        });

        const data = await response.json();
        if (data.status === "success") {
            alert("Data submitted successfully!");

            // Display the generated images
            const generatedImagesContainer = document.getElementById("generated-images");
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