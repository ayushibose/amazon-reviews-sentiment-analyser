// popup.js
console.log("popup.js loaded");
document.getElementById("pieChart").getContext("2d").fillRect(10, 10, 50, 50);

document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get("sentimentResults", ({ sentimentResults }) => {
    if (!sentimentResults || sentimentResults.length === 0) {
      document.getElementById("charts").innerHTML = "<p>No sentiment data available. Please visit an Amazon product page with reviews.</p>";
      return;
    }

    renderCharts(sentimentResults);
  });
});

function renderCharts(results) {
  // --- 1. Pie chart: sentiment distribution ---
  const counts = { POSITIVE: 0, NEUTRAL: 0, NEGATIVE: 0 };
  let totalConfidence = 0;

  results.forEach(r => {
    counts[r.sentiment] = (counts[r.sentiment] || 0) + 1;
    totalConfidence += r.confidence;
  });

  const avgConfidence = totalConfidence / results.length;

  new Chart(document.getElementById("pieChart"), {
    type: "pie",
    data: {
      labels: ["Positive", "Neutral", "Negative"],
      datasets: [{
        data: [counts.POSITIVE, counts.NEUTRAL, counts.NEGATIVE],
        backgroundColor: ['#00c800','#888','#dc0000']
      }]
    },
    options: {
      responsive: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });

  // --- 2. Confidence bar ---
  new Chart(document.getElementById("confidenceChart"), {
    type: "bar",
    data: {
      labels: ["Avg Confidence"],
      datasets: [{
        label: "Confidence",
        data: [avgConfidence],
        backgroundColor: ['#007bff']
      }]
    },
    options: {
      responsive: false,
      scales: { 
        y: { 
          min: 0, 
          max: 1,
          ticks: {
            callback: function(value) {
              return Math.round(value * 100) + '%';
            }
          }
        } 
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  });

  // --- 3. Time Trend ---
  // Group by date and create time series data
  const trend = {};
  const dateCounts = {};
  let hasValidDates = false;
  
  results.forEach(r => {
    if (!r.date) return;
    
    // Parse date string to get a more consistent format
    let parsedDate = r.date;
    try {
      // Try to parse common Amazon date formats
      if (r.date.includes('ago')) {
        // Handle relative dates like "2 days ago"
        const now = new Date();
        const agoMatch = r.date.match(/(\d+)\s+(day|days|week|weeks|month|months|year|years)\s+ago/);
        if (agoMatch) {
          const amount = parseInt(agoMatch[1]);
          const unit = agoMatch[2];
          const multiplier = unit.includes('day') ? 1 : unit.includes('week') ? 7 : unit.includes('month') ? 30 : 365;
          const targetDate = new Date(now.getTime() - (amount * multiplier * 24 * 60 * 60 * 1000));
          parsedDate = targetDate.toISOString().split('T')[0]; // YYYY-MM-DD format
          hasValidDates = true;
        }
      } else {
        // Try to parse absolute dates
        const date = new Date(r.date);
        if (!isNaN(date.getTime())) {
          parsedDate = date.toISOString().split('T')[0]; // YYYY-MM-DD format
          hasValidDates = true;
        }
      }
    } catch (e) {
      // If parsing fails, use original date string
      parsedDate = r.date;
    }
    
    if (!trend[parsedDate]) {
      trend[parsedDate] = { POSITIVE: 0, NEGATIVE: 0, NEUTRAL: 0 };
      dateCounts[parsedDate] = 0;
    }
    trend[parsedDate][r.sentiment] += 1;
    dateCounts[parsedDate] += 1;
  });
  
  // If no valid dates found, create a trend by review order
  if (!hasValidDates) {
    const batchSize = 5; // Group reviews into batches
    for (let i = 0; i < results.length; i += batchSize) {
      const batch = results.slice(i, i + batchSize);
      const batchKey = `Batch ${Math.floor(i / batchSize) + 1}`;
      trend[batchKey] = { POSITIVE: 0, NEGATIVE: 0, NEUTRAL: 0 };
      dateCounts[batchKey] = 0;
      
      batch.forEach(r => {
        trend[batchKey][r.sentiment] += 1;
        dateCounts[batchKey] += 1;
      });
    }
  }

  // Sort dates chronologically or batches by order
  const dates = Object.keys(trend).sort((a, b) => {
    // Handle ISO format (YYYY-MM-DD)
    if (a.match(/^\d{4}-\d{2}-\d{2}$/) && b.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return new Date(a) - new Date(b);
    }
    // Handle batch format (Batch 1, Batch 2, etc.)
    if (a.startsWith('Batch ') && b.startsWith('Batch ')) {
      const aNum = parseInt(a.match(/Batch (\d+)/)[1]);
      const bNum = parseInt(b.match(/Batch (\d+)/)[1]);
      return aNum - bNum;
    }
    // Handle mixed formats - prioritize dates over batches
    if (a.match(/^\d{4}-\d{2}-\d{2}$/)) return -1;
    if (b.match(/^\d{4}-\d{2}-\d{2}$/)) return 1;
    return a.localeCompare(b);
  });

  // Prepare data for chart
  const positive = dates.map(d => trend[d].POSITIVE);
  const negative = dates.map(d => trend[d].NEGATIVE);
  const neutral = dates.map(d => trend[d].NEUTRAL);
  const total = dates.map(d => dateCounts[d]);

  // Create time trend chart
  new Chart(document.getElementById("timeTrendChart"), {
    type: "line",
    data: {
              labels: dates.map(d => {
          // Format date for display
          if (d.match(/^\d{4}-\d{2}-\d{2}$/)) {
            const date = new Date(d);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          }
          // Format batch labels
          if (d.startsWith('Batch ')) {
            return d;
          }
          return d;
        }),
      datasets: [
        {
          label: "Positive",
          data: positive,
          borderColor: "#00c800",
          backgroundColor: "rgba(0, 200, 0, 0.1)",
          fill: true,
          tension: 0.4,
          pointRadius: 4
        },
        {
          label: "Negative",
          data: negative,
          borderColor: "#dc0000",
          backgroundColor: "rgba(220, 0, 0, 0.1)",
          fill: true,
          tension: 0.4,
          pointRadius: 4
        },
        {
          label: "Neutral",
          data: neutral,
          borderColor: "#888",
          backgroundColor: "rgba(136, 136, 136, 0.1)",
          fill: true,
          tension: 0.4,
          pointRadius: 4
        }
      ]
    },
    options: {
      responsive: false,
      plugins: {
        legend: { 
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 15
          }
        },
        tooltip: {
          callbacks: {
            afterBody: function(context) {
              const dataIndex = context[0].dataIndex;
              return `Total reviews: ${total[dataIndex]}`;
            }
          }
        }
      },
      scales: {
        x: { 
          title: { display: true, text: hasValidDates ? "Date" : "Review Batch" },
          grid: { display: false }
        },
        y: { 
          title: { display: true, text: "Number of Reviews" }, 
          beginAtZero: true,
          grid: { color: 'rgba(0,0,0,0.1)' }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  });
}