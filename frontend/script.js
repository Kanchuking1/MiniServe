/**
 * MiniServe Day 6: Upload image → POST /submit → poll /result/{job_id} → show prediction + confidence.
 */

const form = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const fileNameEl = document.getElementById("file-name");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const previewEl = document.getElementById("preview");
const resultEl = document.getElementById("result");

const POLL_INTERVAL_MS = 500;
const API_BASE = ""; // same origin (API serves this page at /app/)

function setStatus(text, busy = false) {
    statusEl.textContent = text;
    statusEl.className = "status" + (busy ? " busy" : "");
}

function setResult(html) {
    resultEl.innerHTML = html;
    resultEl.style.display = html ? "block" : "none";
}

function showPreview(file) {
    if (!file || !file.type.startsWith("image/")) {
        previewEl.innerHTML = "";
        return;
    }
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.alt = "Preview";
    previewEl.innerHTML = "";
    previewEl.appendChild(img);
}

fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    fileNameEl.textContent = file ? file.name : "";
    submitBtn.disabled = !file;
    showPreview(file);
    setResult("");
    setStatus("");
});

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;

    setResult("");
    setStatus("Uploading…", true);
    submitBtn.disabled = true;

    try {
        const formData = new FormData();
        formData.append("file", file);
        const submitRes = await fetch(API_BASE + "/submit", {
            method: "POST",
            body: formData,
        });
        if (!submitRes.ok) {
            const err = await submitRes.json().catch(() => ({ detail: submitRes.statusText }));
            throw new Error(err.detail || "Upload failed");
        }
        const { job_id } = await submitRes.json();
        setStatus("Processing…", true);

        const result = await pollResult(job_id);
        if (result.status === "completed") {
            setStatus("Done.");
            setResult(`
                <h2>Prediction</h2>
                <p class="label">${escapeHtml(result.label)}</p>
                <p class="confidence">Confidence: ${(Number(result.confidence) * 100).toFixed(1)}%</p>
            `);
        } else if (result.status === "failed") {
            setStatus("Classification failed.");
            setResult(`<p class="error">${escapeHtml(result.error || "Unknown error")}</p>`);
        } else {
            setStatus("Timeout or unknown status.");
            setResult("");
        }
    } catch (err) {
        setStatus("");
        setResult(`<p class="error">${escapeHtml(err.message)}</p>`);
    } finally {
        submitBtn.disabled = false;
    }
});

function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
}

function pollResult(jobId) {
    return new Promise((resolve) => {
        const go = async () => {
            try {
                const res = await fetch(API_BASE + "/result/" + encodeURIComponent(jobId));
                if (!res.ok) {
                    setTimeout(go, POLL_INTERVAL_MS);
                    return;
                }
                const data = await res.json();
                if (data.status === "pending") {
                    setTimeout(go, POLL_INTERVAL_MS);
                    return;
                }
                resolve(data);
            } catch {
                setTimeout(go, POLL_INTERVAL_MS);
            }
        };
        go();
    });
}
