const form = document.querySelector("form");
form.addEventListener("submit", (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    fetch("/predict", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => document.getElementById("result").innerHTML = `
        <p>Class ID: ${data.class_id}</p>
        <p>Label: ${data.label}</p>
        <p>Confidence: ${data.confidence}</p>
    `);
});