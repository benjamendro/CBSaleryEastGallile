/* =================================================================
   RC.stack100 — עמודה מוערמת ל-100% לכל קטגוריה.
   ---------------------------------------------------------------
   קובץ תוספת עצמאי, כמו chart-band.js. אינו נוגע ב-charts.js /
   render.js / brand.css. נטען אחרי charts.js ולפני render.js.
   מיועד להשוואת *פרופורציות* בין קטגוריות: כל שורה נמתחת על מלוא
   הרוחב, ולכן העין משווה חלקים ולא גדלים מוחלטים.

   spec = { kind:'stack100',
            series:[{name,color}...],
            data:[{label, values:[...]}...],   // אותה סדרה בכל שורה
            unit:'%', totalLabel:'n' }
   ================================================================= */
(function () {
  if (!window.RC) return;
  var NS = "http://www.w3.org/2000/svg";
  function S(t, a) { var e = document.createElementNS(NS, t); for (var k in a) e.setAttribute(k, a[k]); return e; }

  RC.stack100 = function (host, spec) {
    var d = spec.data, ser = spec.series || [];
    var W = 720, rowH = 58, top = 8, barH = 20;
    var H = top * 2 + d.length * rowH;
    var svg = S('svg', { viewBox: '0 0 ' + W + ' ' + H });
    host.appendChild(svg);
    var segs = [];

    d.forEach(function (row, i) {
      var rTop = top + i * rowH;
      var tot = row.values.reduce(function (a, b) { return a + b; }, 0) || 1;

      /* label line — flush right, RTL-correct */
      var lab = S('text', {
        x: W, y: rTop + 15, 'text-anchor': 'start', class: 'val-label',
        style: 'direction:rtl;unicode-bidi:plaintext'
      });
      lab.textContent = row.label;
      lab.style.fontWeight = '700'; lab.style.fontSize = '15px'; lab.style.fill = 'var(--ink)';
      svg.appendChild(lab);

      /* optional right-hand note (e.g. how many homes the row covers) */
      if (row.note) {
        var nt = S('text', {
          x: 0, y: rTop + 15, 'text-anchor': 'end', class: 'ax-label',
          style: 'direction:rtl;unicode-bidi:plaintext'
        });
        nt.textContent = row.note; nt.style.fontSize = '12.5px';
        svg.appendChild(nt);
      }

      var by = rTop + 26, cum = 0;
      /* track */
      svg.appendChild(S('rect', {
        x: 0, y: by, width: W, height: barH, rx: 5, fill: 'var(--paper-2)'
      }));

      row.values.forEach(function (v, si) {
        var frac = v / tot, w = frac * W;
        var col = (ser[si] && ser[si].color) || RC.series(si);
        /* RTL: first series starts at the right edge and grows leftward */
        var x = W - cum - w;
        var r = S('rect', {
          x: W - cum, y: by, width: 0, height: barH,
          fill: col, style: 'cursor:pointer'
        });
        r.dataset.w = w; r.dataset.x = x;
        RC.hover(r,
          '<span class="t-key">' + row.label + '</span>' +
          '<div class="t-row"><span>' + ((ser[si] && ser[si].name) || '') + '</span>' +
          '<span>' + v + (spec.unit || '%') + '</span></div>' +
          (row.note ? '<div class="t-row"><span>היקף</span><span>' + row.note + '</span></div>' : ''));
        svg.appendChild(r); segs.push(r);

        /* value inside the segment when it fits */
        var txt = Math.round(frac * 100) + '%';
        if (w > 42) {
          var vl = S('text', {
            x: x + w / 2, y: by + 14, 'text-anchor': 'middle', class: 'val-label'
          });
          vl.textContent = txt;
          vl.style.fontSize = '12.5px'; vl.style.fontWeight = '800';
          vl.style.fill = '#fff'; vl.style.direction = 'ltr'; vl.style.opacity = 0;
          svg.appendChild(vl); segs.push(vl);
        }
        cum += w;
      });
    });

    RC.register(host, function () {
      segs.forEach(function (el, i) {
        if (el.tagName === 'rect') {
          el.style.transition = 'width .85s cubic-bezier(.2,.7,.2,1) ' + ((i / 6) * .06) +
            's, x .85s cubic-bezier(.2,.7,.2,1) ' + ((i / 6) * .06) + 's';
          el.setAttribute('width', el.dataset.w);
          el.setAttribute('x', el.dataset.x);
        } else {
          el.style.transition = 'opacity .45s ease ' + (.55 + (i / 6) * .06) + 's';
          el.style.opacity = 1;
        }
      });
    });
  };
})();
