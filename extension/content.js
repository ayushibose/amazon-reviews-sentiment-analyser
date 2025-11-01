// === CONFIG ===
const API_URL = "https://amazon-reviews-sentiment-analyser.onrender.com/"; // changed to deployed URL
const BATCH_SIZE = 10;
const CONF_LABEL_KEY = "data-sentiment-labeled";

const REVIEW_SELECTORS = [
  ".review .review-text-content span",
  ".review .a-row .a-size-base.review-text.review-text-content span",
  ".a-expander-content.reviewText.review-text-content span",
  ".a-section.review.aok-relative .review-text-content span",
  "[data-hook='review-body'] span",
  ".cr-original-review-text"
];

// === HELPERS ===
function findReviewNodes() {
  const set = new Set();
  REVIEW_SELECTORS.forEach(sel => {
    document.querySelectorAll(sel).forEach(n => set.add(n));
  });
  return Array.from(set).filter(n => (n.innerText || "").trim().length > 10);
}

// Minimal ASIN and title extraction for backend ingestion
function findProductASIN() {
  // Try URL like /dp/ASIN
  const urlMatch = window.location.pathname.match(/\/dp\/([A-Z0-9]{10})/i);
  if (urlMatch) return urlMatch[1].toUpperCase();
  // Fallback: data-asin on page
  const el = document.querySelector('[data-asin]');
  const val = el && el.getAttribute('data-asin');
  if (val && /^[A-Z0-9]{10}$/i.test(val)) return val.toUpperCase();
  return null;
}

function findProductTitle() {
  const el = document.querySelector('#productTitle');
  if (el && el.textContent) return el.textContent.trim().slice(0, 120);
  return document.title.slice(0, 120);
}

function findReviewDate(reviewElement) {
  // Common Amazon review date selectors
  const dateSelectors = [
    '.review-date',
    '.a-size-mini.a-color-secondary.review-date',
    '.a-section.review.aok-relative .a-size-mini.a-color-secondary',
    '[data-hook="review-date"]',
    '.cr-original-review-date',
    '.a-size-mini.a-color-secondary',
    '.review-date a',
    '.a-size-mini.a-color-secondary a'
  ];
  
  for (const selector of dateSelectors) {
    const dateNode = reviewElement.querySelector(selector);
    if (dateNode && dateNode.innerText && dateNode.innerText.trim()) {
      return dateNode.innerText.trim();
    }
  }
  
  // Fallback: look for any text that looks like a date
  const allText = reviewElement.innerText;
  const datePatterns = [
    /\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}/i,
    /\d{1,2}\/\d{1,2}\/\d{4}/,
    /\d{1,2}-\d{1,2}-\d{4}/,
    /\d+\s+(?:day|days|week|weeks|month|months|year|years)\s+ago/i
  ];
  
  for (const pattern of datePatterns) {
    const match = allText.match(pattern);
    if (match) {
      return match[0];
    }
  }
  
  return null;
}

function findReviewCountry(reviewElement) {
  // Look for country information in review text or metadata
  const allText = reviewElement.innerText;
  
  // Pattern to match "Reviewed in [Country] on [Date]"
  const countryPattern = /Reviewed in ([^,]+?)(?:\s+on|\s+in|$)/i;
  const match = allText.match(countryPattern);
  if (match) {
    return match[1].trim();
  }
  
  // Alternative patterns for different Amazon locales
  const alternativePatterns = [
    /from ([A-Z][a-z]+(?: [A-Z][a-z]+)*)/,
    /in ([A-Z][a-z]+(?: [A-Z][a-z]+)*)/
  ];
  
  for (const pattern of alternativePatterns) {
    const altMatch = allText.match(pattern);
    if (altMatch) {
      return altMatch[1].trim();
    }
  }
  
  return null;
}

function sentimentClass(label) {
  if (label === "POSITIVE") return "positive";
  if (label === "NEGATIVE") return "negative";
  return "neutral";
}

function labelNode(node, label, confidence) {
  const cls = sentimentClass(label);
  node.classList.remove("sentiment-positive", "sentiment-neutral", "sentiment-negative");
  node.classList.add(`sentiment-${cls}`);
  node.setAttribute(CONF_LABEL_KEY, `${label}:${confidence.toFixed(2)}`);

  let badge = node.parentElement.querySelector(".sentiment-badge");
  if (!badge) {
    badge = document.createElement("span");
    badge.className = "sentiment-badge";
    node.parentElement.appendChild(badge);
  }
  badge.className = `sentiment-badge badge-${cls}`;
  badge.textContent = `${label} ${Math.round(confidence * 100)}%`;

  // Find review date and country using the improved finding functions
  const reviewElement = node.closest('.review');
  const reviewDate = reviewElement ? findReviewDate(reviewElement) : null;
  const reviewCountry = reviewElement ? findReviewCountry(reviewElement) : null;
  
  // Store reviewDate and country with sentiment
  node.setAttribute("data-review-date", reviewDate);
  node.setAttribute("data-review-country", reviewCountry);
  
  // Debug: log the date and country being captured
  if (reviewDate) {
    console.log(`Captured review date: ${reviewDate} for sentiment analysis`);
  }
  if (reviewCountry) {
    console.log(`Captured review country: ${reviewCountry} for sentiment analysis`);
  }
}

function storeResultsForPopup(results) {
  chrome.storage.local.get("sentimentResults", ({ sentimentResults }) => {
    const allResults = (sentimentResults || []).concat(results);
    chrome.storage.local.set({ sentimentResults: allResults }, () => {
      console.log(`Stored ${results.length} new sentiment results. Total: ${allResults.length}`);
    });
  });

  // Also send to backend for realtime dashboard ingestion
  const asin = findProductASIN();
  const title = findProductTitle();
  if (asin) {
    fetch(`${API_URL}/ingest_results`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ asin, title, results })
    }).then(r => {
      if (!r.ok) throw new Error(`Ingest failed ${r.status}`);
      return r.json();
    }).then(j => {
      console.log(`Ingested ${j.stored} results to backend for ${asin}`);
    }).catch(err => {
      console.warn("Ingest to backend failed:", err);
    });
  } else {
    console.warn("ASIN not found; skipping backend ingestion");
  }
}

async function fetchBatch(texts) {
  try {
    const res = await fetch(`${API_URL}/predict_batch`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ texts })
    });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return (await res.json()).results;
  } catch (error) {
    console.warn("API not available, using mock results:", error);
    // Mock results for testing when API is not available
    return texts.map(text => ({
      sentiment: Math.random() > 0.5 ? "POSITIVE" : Math.random() > 0.3 ? "NEGATIVE" : "NEUTRAL",
      confidence: 0.5 + Math.random() * 0.5
    }));
  }
}

function chunk(arr, size) {
  const out = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

// === PROCESS NODES ===
async function processNodes(nodes) {
  const fresh = nodes.filter(n => !n.hasAttribute(CONF_LABEL_KEY));
  if (fresh.length === 0) return;

  console.log(`Processing ${fresh.length} new review nodes`);

  const texts = fresh.map(n => n.innerText.trim());
  const parts = chunk(texts, BATCH_SIZE);
  const collectedResults = [];

  for (let p of parts) {
    try {
      const results = await fetchBatch(p);
      results.forEach(r => {
        const node = fresh.shift();
        if (node) {
          labelNode(node, r.sentiment, r.confidence);
          collectedResults.push({
            sentiment: r.sentiment,
            confidence: r.confidence,
            text: node.innerText.trim(),
            date: node.getAttribute("data-review-date"),
            country: node.getAttribute("data-review-country")
          });
        }
      });
    } catch (err) {
      console.warn("Sentiment API batch failed:", err);
      p.forEach(() => {
        const node = fresh.shift();
        if (node) {
          labelNode(node, "NEUTRAL", 0.0);
          collectedResults.push({
            sentiment: "NEUTRAL",
            confidence: 0.0,
            text: node.innerText.trim(),
            date: node.getAttribute("data-review-date"),
            country: node.getAttribute("data-review-country")
          });
        }
      });
    }
    await new Promise(res => setTimeout(res, 250));
  }

  if (collectedResults.length > 0) {
    storeResultsForPopup(collectedResults);
  }
}

// === OBSERVER ===
function initObserver() {
  console.log("Initializing sentiment analysis observer");
  processNodes(findReviewNodes());

  const obs = new MutationObserver(() => {
    processNodes(findReviewNodes());
  });
  obs.observe(document.body, { childList: true, subtree: true });
}

// === INIT ===
(function main() {
  // Clear previous results on page load
  chrome.storage.local.set({ sentimentResults: [] });
  
  setTimeout(() => {
    initObserver();
    // createAnalyticsToggle(); // <-- REMOVE THIS LINE
  }, 1500);
})();