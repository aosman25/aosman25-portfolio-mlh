document.addEventListener("DOMContentLoaded", () => {
  const timelineForm = document.querySelector("#timeline-form");

  timelineForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(timelineForm);
    const payload = new URLSearchParams(formData);

    try {
      const response = await fetch("/api/timeline_post", {
        method: "POST",
        body: payload,
      });

      if (response.status === 429) {
        alert(
          "You're posting too quickly. Please wait a minute before trying again."
        );
        return; // Don't reload
      }

      if (!response.ok) {
        alert(`Server error: ${response.status}`);
        return;
      }

      // Only reload if POST was successful
      location.reload();
    } catch (err) {
      console.error("Request failed:", err);
      alert("Something went wrong. Please try again.");
    }
  });
});
