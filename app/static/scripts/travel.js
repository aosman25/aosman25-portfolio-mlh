document.addEventListener("DOMContentLoaded", function () {
  var map = L.map("map").setView([20, 0], 2); // Global view
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  const visited = [
    { city: "Cairo", country: "Egypt", lat: 30.0444, lon: 31.2357 },
    { city: "San Francisco", country: "USA", lat: 37.7749, lon: -122.4194 },
    { city: "Berlin", country: "Germany", lat: 52.52, lon: 13.405 },
    {
      city: "Buenos Aires",
      country: "Argentina",
      lat: -34.6037,
      lon: -58.3816,
    },
    { city: "Seoul", country: "South Korea", lat: 37.5665, lon: 126.978 },
    { city: "Istanbul", country: "Turkey", lat: 41.0082, lon: 28.9784 },
    { city: "Doha", country: "Qatar", lat: 25.276987, lon: 51.520008 },
  ];

  visited.forEach((place) => {
    L.marker([place.lat, place.lon])
      .addTo(map)
      .bindPopup(`<strong>${place.city}</strong><br>${place.country}`);
  });
});
