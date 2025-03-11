if (typeof window !== 'undefined') {
  try {
    let theme = localStorage.getItem('theme');
    if (!theme) {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = systemTheme ? 'dark' : 'light';
    }
    if (theme === 'dark') document.documentElement.classList.add('dark');
  } catch {}
}
