const testSignup = async () => {
    try {
        const res = await fetch("http://localhost:3001/api/auth/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: "Test", email: "rituraj@example.com", password: "password", targetRole: "Software Engineer" })
        });
        const data = await res.json();
        console.log("Status:", res.status);
        console.log("Response:", data);
    } catch (err) {
        console.error("Fetch failed:", err.message);
    }
};

testSignup();
