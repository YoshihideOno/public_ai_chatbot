(function (w, d, s, o) {
  w['RagChatWidget'] = o;
  w[o] = w[o] || function () { (w[o].q = w[o].q || []).push(arguments); };

  // rudimentary command processor
  const queue = [];
  const process = (cmd, args) => {
    if (cmd === 'init') {
      const config = args[0] || {};
      // create shadow host
      const host = d.createElement('div');
      host.id = 'rag-chat-widget';
      d.body.appendChild(host);
      const root = host.attachShadow({ mode: 'open' });
      const style = d.createElement('style');
      style.textContent = `:host{all:initial;position:fixed;right:20px;bottom:20px;z-index:999999}
      .toggle{width:48px;height:48px;border-radius:9999px;background:#1976d2;color:#fff;border:none;cursor:pointer}`;
      root.appendChild(style);
      const btn = d.createElement('button');
      btn.className = 'toggle';
      btn.setAttribute('aria-label', 'チャットを開く');
      btn.textContent = '💬';
      root.appendChild(btn);
    }
  };

  // flush existing queue
  (w[o].q || []).forEach(args => process(args[0], Array.prototype.slice.call(args, 1)));
  w[o] = function () { process(arguments[0], Array.prototype.slice.call(arguments, 1)); };

})(window, document, 'script', 'ragChat');


