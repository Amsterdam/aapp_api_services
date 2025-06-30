(function () {
  const key = "adminScroll:" + location.pathname;

  // remember position before the form is submitted / page unloads
  window.addEventListener("beforeunload", () =>
    sessionStorage.setItem(key, window.scrollY)
  );

  // restore it after the new page loads
  window.addEventListener("load", () => {
    const y = sessionStorage.getItem(key);
    if (y !== null) window.scrollTo(0, +y);
    sessionStorage.removeItem(key);             // one-shot
  });
})();