const fs = require('fs');

async function testAnalyze() {
    try {
        const formData = new FormData();
        // Create a basic dummy Blob for the file
        const fileBlob = new Blob(["test dummy pdf text content"], { type: 'application/pdf' });
        formData.append("resume", fileBlob, "test.pdf");
        formData.append("userId", "test-user-id");

        const res = await fetch("http://localhost:3001/api/analyze", {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        console.log("STATUS:", res.status);
        if (!res.ok) {
            console.log("ERROR MESSAGE:", data.message);
            console.log("FULL DATA:", JSON.stringify(data, null, 2));
        } else {
            console.log("SUCCESS!");
        }
    } catch (err) {
        console.error("Fetch crashed:", err.message);
    }
}

testAnalyze();
