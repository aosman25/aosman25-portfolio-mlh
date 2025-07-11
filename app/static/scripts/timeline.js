document.addEventListener("DOMContentLoaded", () => {
  const timelineForm = document.querySelector("#timeline-form");

  timelineForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(timelineForm);
    const payload = new URLSearchParams(formData);
    try {
      await fetch(`/api/timeline_post`, {
        method: "POST",
        body: payload,
      });
      location.reload();
    } catch (err) {
      console.log(`ERROR: ${err}`);
    }
  });
});
