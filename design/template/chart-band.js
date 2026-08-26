/* =================================================================
   RC.band — טווח מוצלל בין רצפה לתקרה, עם מתג ציר-Y מספרים/אחוזים.
   ---------------------------------------------------------------
   קובץ תוספת עצמאי. אינו נוגע ב-charts.js / render.js / brand.css.
   נטען אחרי charts.js (שמגדיר window.RC) ולפני render.js.
   מנוע הבסיס אינו יודע על סוג זה; הוא מגיע דרך טאב בתוך סקשן `tabbed`,
   שבו render.js מפעיל RC[spec.kind] ללא רשימת-היתר.

   spec = {
     kind:'band', x:[labels], floor:[nums], ceiling:[nums],
     unit:'', pctBase: number,            // בסיס לחישוב אחוזים
     floorName, ceilName, floorColor, ceilColor,
     pctLabel:'% מתוך ...',  mode:'abs'|'pct'
   }
   ================================================================= */
(function () {
  if (!window.RC) return;
  var NS = "http://www.w3.org/2000/svg";
  function S(t, a) { var e = document.createElementNS(NS, t); for (var k in a) e.setAttribute(k, a[k]); return e; }

  function niceNum(x, round) {
    var exp = Math.floor(Math.log10(x || 1)), f = x / Math.pow(10, exp), nf;
    if (round) { nf = f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10; }
    else { nf = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10; }
    return nf * Math.pow(10, exp);
  }
  function niceAxis(min, max, ticks) {
    ticks = ticks || 5;
    var step = niceNum((max - min || 1) / (ticks - 1), true);
    var lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step;
    if (lo === min) lo -= step;
    if (hi === max) hi += step;
    return { lo: lo, hi: hi, step: step };
  }
  var fmt = function (v, dec) {
    return dec ? v.toFixed(dec) : Math.round(v).toLocaleString('en-US');
  };

  function paintChip(btn, col, on) {
    btn.classList.toggle('off', !on);
    btn.style.borderColor = col;
    btn.style.background = on ? col : 'transparent';
    btn.style.color = on ? '#fff' : col;
  }

  RC.band = function (host, spec) {
    var mode = spec.mode === 'pct' ? 'pct' : 'abs';
    var base = spec.pctBase || 0;
    var fCol = spec.floorColor || 'var(--c-blue)';
    var cCol = spec.ceilColor || 'var(--c-lime)';
    var fName = spec.floorName || 'רצפה';
    var cName = spec.ceilName || 'תקרה';
    var canPct = !!(base > 0);
    if (!canPct) mode = 'abs';

    var svgWrap = document.createElement('div');
    host.appendChild(svgWrap);

    /* ---- ציר-Y: מתג מספרים / אחוזים ---- */
    var bar = null;
    if (canPct) {
      bar = document.createElement('div');
      bar.className = 'ml-legend';
      bar.style.marginBottom = '2px';
      host.appendChild(bar);
    }

    var animated = false;

    function vals(arr) {
      return mode === 'pct' ? arr.map(function (v) { return v / base * 100; }) : arr.slice();
    }

    function draw(animate) {
      svgWrap.innerHTML = '';
      var W = 720, H = 330, m = { t: 26, r: 26, b: 44, l: 58 };
      var iw = W - m.l - m.r, ih = H - m.t - m.b, xInset = 18;
      var xs = spec.x, F = vals(spec.floor), C = vals(spec.ceiling);
      var all = F.concat(C);
      var ax = niceAxis(Math.min.apply(null, all), Math.max.apply(null, all), 6);
      var lo = ax.lo, hi = ax.hi;
      var dec = mode === 'pct' ? 0 : 0;
      var suffix = mode === 'pct' ? '%' : (spec.unit || '');
      var X = function (i) { return m.l + xInset + (i / (xs.length - 1)) * (iw - 2 * xInset); };
      var Y = function (v) { return m.t + (1 - (v - lo) / (hi - lo)) * ih; };
      var svg = S('svg', { viewBox: '0 0 ' + W + ' ' + H });
      svgWrap.appendChild(svg);

      /* grid + Y labels */
      for (var v = lo; v <= hi + 1e-6; v += ax.step) {
        svg.appendChild(S('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), class: 'grid-line' }));
        var t = S('text', { x: m.l - 9, y: Y(v) + 4, 'text-anchor': 'end', class: 'ax-label' });
        t.textContent = fmt(v, dec) + suffix;
        svg.appendChild(t);
      }
      /* X labels */
      xs.forEach(function (lab, i) {
        var t = S('text', { x: X(i), y: H - 14, 'text-anchor': 'middle', class: 'ax-label' });
        t.textContent = lab; svg.appendChild(t);
      });

      /* ---- the shaded range itself ---- */
      var top = C.map(function (v, i) { return X(i) + ',' + Y(v); });
      var bot = F.map(function (v, i) { return X(i) + ',' + Y(v); }).reverse();
      var area = S('path', {
        d: 'M' + top.join('L') + 'L' + bot.join('L') + 'Z',
        fill: cCol, opacity: 0, style: 'cursor:pointer'
      });
      svg.appendChild(area);

      var pc = S('path', {
        d: 'M' + C.map(function (v, i) { return X(i) + ',' + Y(v); }).join('L'),
        fill: 'none', stroke: cCol, 'stroke-width': 2.2, 'stroke-linecap': 'round',
        'stroke-linejoin': 'round'
      });
      var pf = S('path', {
        d: 'M' + F.map(function (v, i) { return X(i) + ',' + Y(v); }).join('L'),
        fill: 'none', stroke: fCol, 'stroke-width': 3.0, 'stroke-linecap': 'round',
        'stroke-linejoin': 'round'
      });
      svg.appendChild(pc); svg.appendChild(pf);

      /* hover column per period — one tooltip carrying the whole range */
      var dots = [];
      xs.forEach(function (lab, i) {
        var half = (iw - 2 * xInset) / (xs.length - 1) / 2;
        var hit = S('rect', {
          x: X(i) - half, y: m.t, width: half * 2, height: ih,
          fill: 'transparent', style: 'cursor:pointer'
        });
        var spread = C[i] - F[i];
        RC.hover(hit,
          '<span class="t-key">' + lab + '</span>' +
          '<div class="t-row"><span>' + cName + '</span><span>' + fmt(C[i], dec) + suffix + '</span></div>' +
          '<div class="t-row"><span>' + fName + '</span><span>' + fmt(F[i], dec) + suffix + '</span></div>' +
          '<div class="t-row"><span>טווח</span><span>' + fmt(spread, dec) + suffix + '</span></div>');
        svg.appendChild(hit);
        [[C[i], cCol, 3.6], [F[i], fCol, 4.4]].forEach(function (d) {
          var c = S('circle', {
            cx: X(i), cy: Y(d[0]), r: d[2], fill: '#fff', stroke: d[1],
            'stroke-width': 2.4, opacity: 0, style: 'pointer-events:none'
          });
          svg.appendChild(c); dots.push(c);
        });
      });

      function play() {
        area.style.transition = 'opacity .7s ease';
        area.style.opacity = '.20';
        [pc, pf].forEach(function (p, k) {
          var len = p.getTotalLength() || 0;
          if (!len) return;
          p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
          requestAnimationFrame(function () {
            requestAnimationFrame(function () {
              p.style.transition = 'stroke-dashoffset 1.1s cubic-bezier(.2,.7,.2,1) ' + (k * .12) + 's';
              p.style.strokeDashoffset = '0';
            });
          });
        });
        dots.forEach(function (c, i) {
          c.style.transition = 'opacity .35s ease ' + (.6 + i * .03) + 's';
          c.style.opacity = '1';
        });
      }
      if (animate) { RC.register(host, play); }
      else { area.style.opacity = '.20'; dots.forEach(function (c) { c.style.opacity = '1'; }); }
    }

    if (canPct) {
      var bAbs = document.createElement('button');
      bAbs.type = 'button'; bAbs.className = 'ml-leg-btn'; bAbs.textContent = 'מספרים';
      var bPct = document.createElement('button');
      bPct.type = 'button'; bPct.className = 'ml-leg-btn';
      bPct.textContent = spec.pctLabel || 'אחוזים';
      function paint() {
        paintChip(bAbs, 'var(--c-bluedeep)', mode === 'abs');
        paintChip(bPct, 'var(--c-bluedeep)', mode === 'pct');
      }
      bAbs.onclick = function () { if (mode === 'abs') return; mode = 'abs'; paint(); draw(false); };
      bPct.onclick = function () { if (mode === 'pct') return; mode = 'pct'; paint(); draw(false); };
      bar.appendChild(bAbs); bar.appendChild(bPct); paint();
    }
    draw(true);
  };
})();
