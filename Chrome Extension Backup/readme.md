## JavaScript console
  - enable disable content form webisite 
```
// 1. Har element pe user-select allow karo
document.querySelectorAll('*').forEach(el => {
  el.style.userSelect = 'text';
  el.style.webkitUserSelect = 'text';
  el.style.msUserSelect = 'text';
});

// 2. Overlay ya block karne wale elements ko hatao ya invisible karo
document.querySelectorAll('div, span, section').forEach(el => {
  const style = getComputedStyle(el);
  if (
    (style.pointerEvents === 'none' || style.zIndex > 999) &&
    style.position === 'fixed'
  ) {
    el.style.display = 'none';
  }
});

// 3. Context menu (right click) aur copy block events hatao
['copy', 'cut', 'contextmenu', 'selectstart', 'mousedown', 'mouseup'].forEach(event => {
  document.body.addEventListener(event, e => e.stopPropagation(), true);
});
```
