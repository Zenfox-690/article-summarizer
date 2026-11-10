(function () {
  "use strict";

  const MAX_ARTICLE_CHARACTERS = 100000;

  const SAMPLE_ARTICLE = `# How Community Gardens Improve Urban Life

As cities grow, access to green spaces and fresh food is becoming an important challenge. Community gardens offer a practical solution by allowing residents to grow vegetables, herbs, and fruits in shared spaces such as vacant plots, rooftops, and school grounds.

One major benefit of community gardens is improved access to nutritious food. Residents can grow fresh produce locally, potentially reducing grocery expenses and dependence on long supply chains. Gardening also encourages people to learn about nutrition, seasonal crops, and sustainable food production.

Community gardens can strengthen social relationships as well. People from different backgrounds work together, exchange gardening knowledge, and share their harvests. These activities can create a stronger sense of belonging, reduce social isolation, and provide opportunities for educational programmes involving children and older residents.

Gardens may also benefit the urban environment. Plants can provide habitats for pollinators, improve local green cover, and help absorb rainwater. Vegetation can contribute to cooling in built-up areas, although the overall effect depends on the garden's size, design, and location.

Despite these benefits, community gardens face challenges. Urban land is expensive, access to water can be limited, and gardens require ongoing maintenance. Projects are more likely to succeed when residents receive permission to use land, reliable access to resources, and support from local authorities or community organisations.

Ultimately, community gardens are not a complete solution to urban food insecurity or environmental problems. However, with thoughtful planning and sustained community participation, they can make neighbourhoods greener, encourage healthier habits, and strengthen connections between residents.`;

  // Elements
  const articleInput = document.getElementById("article-input");
  const inputWordCount = document.getElementById("input-word-count");
  const inputCharCount = document.getElementById("input-char-count");
  const inputError = document.getElementById("input-error");
  const summarizeBtn = document.getElementById("summarize-btn");
  const btnText = document.getElementById("btn-text");
  const loadingSpinner = document.getElementById("loading-spinner");
  const sampleBtn = document.getElementById("sample-btn");
  const clearBtn = document.getElementById("clear-btn");

  const summarySection = document.getElementById("summary-section");
  const summaryContent = document.getElementById("summary-content");
  const outputWordCount = document.getElementById("output-word-count");
  const outputCharCount = document.getElementById("output-char-count");
  const reductionBadge = document.getElementById("reduction-badge");
  const copyBtn = document.getElementById("copy-btn");
  const copyText = document.getElementById("copy-text");

  const errorBanner = document.getElementById("error-banner");
  const errorMessage = document.getElementById("error-message");
  const dismissErrorBtn = document.getElementById("dismiss-error-btn");

  let currentSummary = "";

  function countWords(text) {
    if (!text || !text.trim()) return 0;
    return text.trim().split(/\s+/).filter(Boolean).length;
  }

  function updateInputStats() {
    const text = articleInput.value;
    const words = countWords(text);
    const chars = text.length;

    inputWordCount.textContent = words.toLocaleString();
    inputCharCount.textContent = chars.toLocaleString();

    if (text.trim().length > 0) {
      clearInputError();
    }
  }

  function showInputError(message) {
    inputError.textContent = message;
    inputError.classList.remove("hidden");
    articleInput.classList.add("input-error-state");
  }

  function clearInputError() {
    inputError.textContent = "";
    inputError.classList.add("hidden");
    articleInput.classList.remove("input-error-state");
  }

  function showErrorBanner(message) {
    errorMessage.textContent = message;
    errorBanner.classList.remove("hidden");
    errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function hideErrorBanner() {
    errorBanner.classList.add("hidden");
    errorMessage.textContent = "";
  }

  function setLoading(isLoading) {
    summarizeBtn.disabled = isLoading;
    articleInput.disabled = isLoading;
    if (isLoading) {
      loadingSpinner.classList.remove("hidden");
      btnText.textContent = "Summarizing with Gemini...";
    } else {
      loadingSpinner.classList.add("hidden");
      btnText.textContent = "Summarize Article";
    }
  }

  async function handleSummarize() {
    hideErrorBanner();
    clearInputError();

    const rawText = articleInput.value;
    const trimmedText = rawText.trim();

    if (!trimmedText) {
      showInputError("Please enter or paste an article before summarizing.");
      articleInput.focus();
      return;
    }

    if (rawText.length > MAX_ARTICLE_CHARACTERS) {
      showInputError(
        `Article length (${rawText.length.toLocaleString()} chars) exceeds the maximum allowed limit of ${MAX_ARTICLE_CHARACTERS.toLocaleString()} characters.`
      );
      articleInput.focus();
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify({ article: rawText }),
      });

      let data;
      try {
        data = await response.json();
      } catch (parseErr) {
        throw new Error("Invalid response format received from the server.");
      }

      if (!response.ok) {
        const errorDetail =
          data && data.detail
            ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail))
            : `Request failed with status ${response.status}.`;
        showErrorBanner(errorDetail);
        return;
      }

      if (!data || typeof data.summary !== "string") {
        showErrorBanner("Unexpected server response: missing summary text.");
        return;
      }

      // Display summary
      currentSummary = data.summary.trim();
      displaySummary(currentSummary, countWords(rawText));
    } catch (err) {
      showErrorBanner(
        err.message || "Failed to contact the summarization service. Please check your network and retry."
      );
    } finally {
      setLoading(false);
    }
  }

  function displaySummary(summary, inputWords) {
    // Render summary cleanly preserving paragraph breaks
    summaryContent.innerHTML = "";
    const paragraphs = summary.split(/\n\s*\n/);
    paragraphs.forEach(function (para) {
      const p = document.createElement("p");
      p.textContent = para.trim();
      summaryContent.appendChild(p);
    });

    const outputWords = countWords(summary);
    const outputChars = summary.length;

    outputWordCount.textContent = outputWords.toLocaleString();
    outputCharCount.textContent = outputChars.toLocaleString();

    if (inputWords > 0 && outputWords < inputWords) {
      const reductionPercent = Math.round(((inputWords - outputWords) / inputWords) * 100);
      reductionBadge.textContent = `${reductionPercent}% shorter`;
      reductionBadge.classList.remove("hidden");
    } else {
      reductionBadge.classList.add("hidden");
    }

    summarySection.classList.remove("hidden");
    summarySection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function handleCopy() {
    if (!currentSummary) return;

    try {
      await navigator.clipboard.writeText(currentSummary);
      const originalText = copyText.textContent;
      copyText.textContent = "Copied!";
      copyBtn.classList.add("btn-primary");
      copyBtn.classList.remove("btn-secondary");

      setTimeout(function () {
        copyText.textContent = originalText;
        copyBtn.classList.remove("btn-primary");
        copyBtn.classList.add("btn-secondary");
      }, 2000);
    } catch (err) {
      // Fallback if clipboard API is restricted
      const tempArea = document.createElement("textarea");
      tempArea.value = currentSummary;
      document.body.appendChild(tempArea);
      tempArea.select();
      try {
        document.execCommand("copy");
        copyText.textContent = "Copied!";
        setTimeout(function () {
          copyText.textContent = "Copy Summary";
        }, 2000);
      } catch (e) {
        showErrorBanner("Could not automatically copy summary to clipboard.");
      }
      document.body.removeChild(tempArea);
    }
  }

  // Event Listeners
  articleInput.addEventListener("input", updateInputStats);
  summarizeBtn.addEventListener("click", handleSummarize);
  copyBtn.addEventListener("click", handleCopy);
  dismissErrorBtn.addEventListener("click", hideErrorBanner);

  sampleBtn.addEventListener("click", function () {
    articleInput.value = SAMPLE_ARTICLE;
    updateInputStats();
    clearInputError();
    hideErrorBanner();
    articleInput.focus();
  });

  clearBtn.addEventListener("click", function () {
    articleInput.value = "";
    currentSummary = "";
    updateInputStats();
    clearInputError();
    hideErrorBanner();
    summarySection.classList.add("hidden");
    articleInput.focus();
  });

  // Initial stats
  updateInputStats();
})();
