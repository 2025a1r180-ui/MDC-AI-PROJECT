// Echo Journal Client Script
document.addEventListener('DOMContentLoaded', () => {
  const contentInput = document.getElementById('content');
  const wordCountElem = document.getElementById('live-word-count');
  const charCountElem = document.getElementById('live-char-count');

  if (contentInput && wordCountElem && charCountElem) {
    const updateStats = () => {
      const text = contentInput.value.trim();
      const words = text ? text.split(/\s+/).length : 0;
      const chars = text.length;

      wordCountElem.textContent = `${words} ${words === 1 ? 'word' : 'words'}`;
      charCountElem.textContent = `${chars} ${chars === 1 ? 'character' : 'characters'}`;
    };

    contentInput.addEventListener('input', updateStats);
    updateStats();
  }
});
