document.addEventListener('DOMContentLoaded', () => {
    const moodSelect = document.querySelector('.mood-select');
    const moodOptions = document.querySelectorAll('.mood-option');
    
    // Existing emoji logic
    if (moodSelect && moodSelect.value) {
        const selectedOption = document.querySelector(`[data-mood="${moodSelect.value}"]`);
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
    }
    
    moodOptions.forEach(option => {
        option.addEventListener('click', () => {
            moodOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            moodSelect.value = option.dataset.mood;
        });
    });

    // Now, initialize Cal-Heatmap
    const cal = new CalHeatmap();

    cal.paint({
      date: {
        start: new Date(new Date().setFullYear(new Date().getFullYear() - 1)) // start a year ago
      },
      range: 12, // 12 months
      domain: { type: 'month', label: { position: 'top' } },
      subDomain: { type: 'day', radius: 4, width: 12, height: 12, gutter: 2 },
      data: {
        source: '/api/calendar_data',
        type: 'json',
        x: (d) => d, // Use the keys as timestamps directly
        y: (value, timestamp) => value // value is mood score
      },
      scale: {
        color: {
          type: 'quantize',
          domain: [0,4],
          range: ['#d8eefe','#add7f7','#8bc1ed','#5ea6da','#3780b4'] // adjust colors as you like
        }
      },
      tooltip: {
        enabled: true,
        text: (date, value) => {
          if (value === null) return 'No data';
          const moodNames = ["Sad","Stressed","Neutral","Excited","Happy"];
          return `${moodNames[value]} on ${date.toDateString()}`;
        }
      }
    });
});