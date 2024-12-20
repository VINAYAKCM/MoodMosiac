document.addEventListener('DOMContentLoaded', () => {
  const moodForm = document.getElementById('mood-form');
  const heatmapContainer = document.getElementById('heatmap');

  // Fetch and render heatmap
  function renderHeatmap() {
      fetch('/api/moods')
          .then(res => res.json())
          .then(data => {
              heatmapContainer.innerHTML = ''; // Clear existing heatmap
              Object.keys(data).forEach(date => {
                  const cell = document.createElement('div');
                  cell.className = `heatmap-cell ${data[date].toLowerCase()}`;
                  cell.title = `${data[date]} - ${date}`;
                  heatmapContainer.appendChild(cell);
              });
          });
  }

  moodForm.addEventListener('submit', event => {
      event.preventDefault();

      const formData = new FormData(moodForm);
      fetch('/mood_input', {
          method: 'POST',
          body: formData
      }).then(() => {
          renderHeatmap(); // Refresh heatmap
      });
  });

  renderHeatmap();
});